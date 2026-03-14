"""
Vues du workflow BDC Peinture.
"""

import logging
import os
import tempfile
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages

logger = logging.getLogger(__name__)
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.safestring import mark_safe

from apps.pdf_extraction.detector import PDFTypeInconnu, detecter_parser

from .filters import BonDeCommandeFilter
from .forms import AttributionForm, BDCEditionForm
from .models import (
    ActionChoices,
    Bailleur,
    BonDeCommande,
    ChecklistItem,
    ChecklistResultat,
    LignePrestation,
    PrixForfaitaire,
    StatutChoices,
    TransitionChoices,
)
from .notifications import notifier_st_attribution
from .services import (
    BDCIncomplet,
    TransitionInvalide,
    attribuer_st,
    changer_statut,
    enregistrer_action,
    reattribuer_st,
    renvoyer_controle,
    valider_facturation,
    valider_realisation,
)


def _parse_lignes_forfait(post_data):
    """Parse les lignes forfait du POST (format: ligne_N_prix, ligne_N_qty, ligne_N_pu)."""
    lignes = []
    i = 0
    while f"ligne_{i}_prix" in post_data:
        prix_id = post_data.get(f"ligne_{i}_prix")
        qty = post_data.get(f"ligne_{i}_qty")
        pu = post_data.get(f"ligne_{i}_pu")
        if prix_id and qty and pu:
            lignes.append({"prix_id": int(prix_id), "quantite": Decimal(qty), "prix_unitaire": Decimal(pu)})
        i += 1
    return lignes


def _parse_date(value):
    """Convertit une chaîne date (session) en objet date ou None."""
    if not value:
        return None
    if isinstance(value, date):
        return value
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            from datetime import datetime

            return datetime.strptime(value, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


PERIODES_CHOICES = [
    ("semaine", "Semaine"),
    ("mois", "Mois"),
    ("trimestre", "Trimestre"),
    ("annee", "Année"),
]


def _parse_periode_params(request):
    """Parse les query params de periode et retourne les bornes.

    Returns:
        (date_du, date_au, date_du_n1, date_au_n1, periode_active)
    """
    from apps.bdc.periode import calculer_bornes_periode

    periode = request.GET.get("periode", "")
    date_du_str = request.GET.get("date_du", "")
    date_au_str = request.GET.get("date_au", "")
    date_du = date_au = date_du_n1 = date_au_n1 = None
    periode_active = ""

    if periode and periode != "custom":
        date_ref_str = request.GET.get("date", "")
        date_ref = _parse_date(date_ref_str) if date_ref_str else None
        bornes = calculer_bornes_periode(periode, date_ref)
        if bornes:
            date_du, date_au, date_du_n1, date_au_n1 = bornes
            periode_active = periode
    elif date_du_str and date_au_str:
        date_du = _parse_date(date_du_str)
        date_au = _parse_date(date_au_str)
        if date_du and date_au:
            delta = date_au - date_du
            date_au_n1 = date_du - timedelta(days=1)
            date_du_n1 = date_au_n1 - delta
            periode_active = "custom"

    return date_du, date_au, date_du_n1, date_au_n1, periode_active


def _attach_n1_data(sous_traitants, date_du_n1, date_au_n1, statuts=None, with_delta=False):
    """Attache les donnees N-1 sur chaque ST annote.

    Modifie la liste en place. Retourne True si N-1 est present.
    """
    if not (date_du_n1 and date_au_n1):
        return False
    n1_qs = _get_repartition_st(date_du=date_du_n1, date_au=date_au_n1, statuts=statuts)
    n1_map = {st.pk: st for st in n1_qs}
    for st in sous_traitants:
        st_n1 = n1_map.get(st.pk)
        if st_n1:
            st.nb_bdc_n1 = st_n1.nb_bdc
            st.total_montant_st_n1 = st_n1.total_montant_st
        else:
            st.nb_bdc_n1 = 0
            st.total_montant_st_n1 = None
        if with_delta:
            st.delta_bdc = st.nb_bdc - (st.nb_bdc_n1 or 0)
    return True


def _parse_decimal(value):
    """Convertit une valeur session en Decimal ou None."""
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


# Transitions "avant" que la Secrétaire peut déclencher depuis la sidebar.
# Seul A_TRAITER → A_FAIRE est pertinent ; les autres avancements passent par le CDT.
SIDEBAR_TRANSITIONS: dict[str, list[str]] = {}

# ─── Dashboard / Liste BDC ───────────────────────────────────────────────────


@login_required
def liste_bdc(request):
    """Tableau de bord : liste paginée des BDC avec filtres et recherche."""
    queryset = (
        BonDeCommande.objects.select_related("bailleur", "sous_traitant")
        .annotate(montant_ht_total=Sum("lignes_prestation__montant"))
        .all()
    )

    # Recherche textuelle
    recherche = request.GET.get("q", "").strip()
    if recherche:
        queryset = queryset.filter(
            Q(numero_bdc__icontains=recherche) | Q(adresse__icontains=recherche) | Q(occupant_nom__icontains=recherche)
        )

    # Filtre alerte (retard / proche)
    alerte = request.GET.get("alerte", "").strip()
    if alerte == "retard":
        from apps.notifications.alertes import get_bdc_en_retard
        queryset = queryset.filter(pk__in=get_bdc_en_retard().values_list("pk", flat=True))
    elif alerte == "proche":
        from apps.notifications.alertes import get_bdc_delai_proche
        queryset = queryset.filter(pk__in=get_bdc_delai_proche().values_list("pk", flat=True))

    # Filtres django-filter
    filtre = BonDeCommandeFilter(request.GET, queryset=queryset)
    queryset_filtre = filtre.qs

    # Pagination
    paginator = Paginator(queryset_filtre, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Compteurs par statut (sur l'ensemble, pas le filtré)
    compteurs_qs = BonDeCommande.objects.values("statut").annotate(count=Count("id"))
    compteurs = {s.value: 0 for s in StatutChoices}
    for row in compteurs_qs:
        compteurs[row["statut"]] = row["count"]
    total = sum(compteurs.values())

    from apps.notifications.alertes import get_bdc_delai_proche, get_bdc_en_retard

    alertes_retard = get_bdc_en_retard()
    alertes_proches = get_bdc_delai_proche()

    nb_filtres = sum(
        [
            bool(request.GET.get("bailleur")),
            bool(request.GET.get("ville")),
            bool(request.GET.get("date_du")),
            bool(request.GET.get("date_au")),
        ]
    )

    context = {
        "page_obj": page_obj,
        "filtre": filtre,
        "recherche": recherche,
        "compteurs": compteurs,
        "total": total,
        "statut_choices": StatutChoices,
        "alertes_retard": alertes_retard,
        "alertes_proches": alertes_proches,
        "nb_filtres": nb_filtres,
    }

    # HTMX: return only the dashboard fragment, not the full layout
    if request.headers.get("HX-Request"):
        return render(request, "bdc/_liste_partial.html", context)

    return render(request, "bdc/liste.html", context)


# ─── Upload PDF ───────────────────────────────────────────────────────────────


@login_required
def upload_pdf(request):
    """
    GET  → Affiche le formulaire d'upload.
    POST → Extrait les données du PDF, stocke en session, redirige vers creer_bdc.
    """
    if request.method == "GET":
        return render(request, "bdc/upload.html")

    pdf_file = request.FILES.get("pdf_file")

    if not pdf_file:
        messages.error(request, "Veuillez sélectionner un fichier PDF.")
        return render(request, "bdc/upload.html")

    if not pdf_file.name.lower().endswith(".pdf"):
        messages.error(request, "Seuls les fichiers PDF sont acceptés.")
        return render(request, "bdc/upload.html")

    # Écriture dans un fichier temporaire (pdfplumber nécessite un chemin)
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    try:
        with os.fdopen(tmp_fd, "wb") as tmp:
            for chunk in pdf_file.chunks():
                tmp.write(chunk)

        parser = detecter_parser(tmp_path)
        donnees = parser.extraire()

    except PDFTypeInconnu as e:
        messages.error(request, str(e))
        return render(request, "bdc/upload.html")
    except Exception:
        messages.error(request, "Impossible de lire ce PDF. Vérifiez que le fichier n'est pas corrompu.")
        return render(request, "bdc/upload.html")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    # Sauvegarde du fichier PDF original pour la création du BDC
    pdf_file.seek(0)
    media_tmp_name = f"tmp/{uuid.uuid4()}.pdf"
    default_storage.save(media_tmp_name, ContentFile(pdf_file.read()))

    # Stockage en session (serialisation JSON-compatible)
    request.session["bdc_extrait"] = _serialiser_pour_session(donnees)
    request.session["bdc_pdf_name"] = pdf_file.name
    request.session["bdc_pdf_temp"] = media_tmp_name

    bailleur_code = donnees.get("bailleur_code", "")
    messages.success(request, f"PDF {bailleur_code} importé avec succès.")
    return redirect("bdc:nouveau")


# ─── Création BDC ─────────────────────────────────────────────────────────────


@login_required
def creer_bdc(request):
    """
    GET  → Affiche les données extraites du PDF en lecture seule pour confirmation.
    POST → Crée le BDC depuis les données en session, crée les lignes, trace l'historique, redirige.
    """
    donnees_session = request.session.get("bdc_extrait")
    if not donnees_session:
        messages.error(request, "Aucun PDF importé. Veuillez d'abord importer un bon de commande.")
        return redirect("bdc:upload")

    donnees = dict(donnees_session)
    lignes_session = donnees.pop("lignes_prestation", [])

    if request.method == "GET":
        return render(
            request,
            "bdc/creer_bdc.html",
            {
                "donnees": donnees,
                "lignes_session": lignes_session,
            },
        )

    # POST : création du BDC depuis les données session
    bailleur_code = donnees.pop("bailleur_code", None)
    bailleur = None
    if bailleur_code:
        try:
            bailleur = Bailleur.objects.get(code=bailleur_code)
        except Bailleur.DoesNotExist:
            messages.error(request, f"Bailleur « {bailleur_code} » introuvable.")
            return render(
                request,
                "bdc/creer_bdc.html",
                {
                    "donnees": donnees_session,
                    "lignes_session": lignes_session,
                    "error_message": f"Bailleur « {bailleur_code} » introuvable en base.",
                },
            )

    numero_bdc = donnees.get("numero_bdc", "").strip()
    if not numero_bdc:
        return render(
            request,
            "bdc/creer_bdc.html",
            {
                "donnees": donnees_session,
                "lignes_session": lignes_session,
                "error_message": "Le numéro BDC n'a pas pu être extrait du PDF.",
            },
        )

    if BonDeCommande.objects.filter(numero_bdc=numero_bdc).exists():
        return render(
            request,
            "bdc/creer_bdc.html",
            {
                "donnees": donnees_session,
                "lignes_session": lignes_session,
                "error_message": f"Le BDC n°{numero_bdc} existe déjà dans le système.",
            },
        )

    # Conversion des dates (chaînes → objets date)
    date_emission = _parse_date(donnees.get("date_emission"))
    delai_execution = _parse_date(donnees.get("delai_execution"))

    bdc = BonDeCommande(
        numero_bdc=numero_bdc,
        numero_marche=donnees.get("numero_marche", ""),
        bailleur=bailleur,
        date_emission=date_emission,
        programme_residence=donnees.get("programme_residence", ""),
        adresse=donnees.get("adresse", ""),
        code_postal=donnees.get("code_postal", ""),
        ville=donnees.get("ville", ""),
        logement_numero=donnees.get("logement_numero", ""),
        logement_type=donnees.get("logement_type", ""),
        logement_etage=donnees.get("logement_etage", ""),
        logement_porte=donnees.get("logement_porte", ""),
        objet_travaux=donnees.get("objet_travaux", ""),
        delai_execution=delai_execution,
        occupant_nom=donnees.get("occupant_nom", ""),
        occupant_telephone=donnees.get("occupant_telephone", ""),
        occupant_email=donnees.get("occupant_email", ""),
        emetteur_nom=donnees.get("emetteur_nom", ""),
        emetteur_telephone=donnees.get("emetteur_telephone", ""),
        montant_ht=_parse_decimal(donnees.get("montant_ht")),
        montant_tva=_parse_decimal(donnees.get("montant_tva")),
        montant_ttc=_parse_decimal(donnees.get("montant_ttc")),
        cree_par=request.user,
        statut=StatutChoices.A_TRAITER,
    )
    bdc.save()

    # Lignes de prestation depuis la session
    for i, ligne_data in enumerate(lignes_session):
        LignePrestation.objects.create(
            bdc=bdc,
            designation=ligne_data.get("designation", ""),
            quantite=Decimal(str(ligne_data.get("quantite", "0"))),
            unite=ligne_data.get("unite", ""),
            prix_unitaire=Decimal(str(ligne_data.get("prix_unitaire", "0"))),
            montant=Decimal(str(ligne_data.get("montant_ht") or ligne_data.get("montant") or "0")),
            ordre=i,
        )

    # PDF original depuis la session
    tmp_path = request.session.get("bdc_pdf_temp")
    pdf_name = request.session.get("bdc_pdf_name", "bdc.pdf")
    if tmp_path and default_storage.exists(tmp_path):
        with default_storage.open(tmp_path) as f:
            bdc.pdf_original.save(pdf_name, File(f), save=True)
        default_storage.delete(tmp_path)

    # Traçabilité
    enregistrer_action(bdc, request.user, ActionChoices.CREATION)

    # Nettoyage session
    for cle in ("bdc_extrait", "bdc_pdf_name", "bdc_pdf_temp"):
        request.session.pop(cle, None)

    messages.success(request, f"BDC n°{bdc.numero_bdc} créé avec succès.")
    return redirect("bdc:detail", pk=bdc.pk)


# ─── Détail BDC ───────────────────────────────────────────────────────────────


def _render_sidebar(request, bdc, error_message=None, success_message=None):
    """Render le partial sidebar avec contexte complet. Ajoute HX-Trigger pour rafraîchir le dashboard."""
    bdc.refresh_from_db()
    lignes = bdc.lignes_prestation.all()
    historique = bdc.historique.all()[:10]
    transitions = [(statut, StatutChoices(statut).label) for statut in SIDEBAR_TRANSITIONS.get(bdc.statut, [])]
    form_edition = BDCEditionForm(instance=bdc) if bdc.statut == StatutChoices.A_TRAITER else None

    # Déterminer si des checklists existent pour les transitions du statut courant
    checklist_transitions = {}
    if bdc.statut == StatutChoices.EN_COURS:
        checklist_transitions["EN_COURS__A_FACTURER"] = ChecklistItem.objects.filter(
            actif=True, transition=TransitionChoices.REALISATION
        ).exists()
    elif bdc.statut == StatutChoices.A_FACTURER:
        checklist_transitions["A_FACTURER__FACTURE"] = ChecklistItem.objects.filter(
            actif=True, transition=TransitionChoices.FACTURATION
        ).exists()

    response = render(
        request,
        "bdc/_detail_sidebar.html",
        {
            "bdc": bdc,
            "lignes": lignes,
            "historique": historique,
            "transitions": transitions,
            "form_edition": form_edition,
            "error_message": error_message,
            "success_message": success_message,
            "checklist_transitions": checklist_transitions,
        },
    )
    response["HX-Trigger"] = "bdc-updated"
    return response


@login_required
def detail_sidebar(request, pk: int):
    """Partial HTML for the HTMX sidebar — no base layout."""

    bdc = get_object_or_404(BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk)
    lignes = bdc.lignes_prestation.all()
    historique = bdc.historique.all()[:10]

    transitions = [(statut, StatutChoices(statut).label) for statut in SIDEBAR_TRANSITIONS.get(bdc.statut, [])]
    form_edition = BDCEditionForm(instance=bdc) if bdc.statut == StatutChoices.A_TRAITER else None

    # Déterminer si des checklists existent pour les transitions du statut courant
    checklist_transitions = {}
    if bdc.statut == StatutChoices.EN_COURS:
        checklist_transitions["EN_COURS__A_FACTURER"] = ChecklistItem.objects.filter(
            actif=True, transition=TransitionChoices.REALISATION
        ).exists()
    elif bdc.statut == StatutChoices.A_FACTURER:
        checklist_transitions["A_FACTURER__FACTURE"] = ChecklistItem.objects.filter(
            actif=True, transition=TransitionChoices.FACTURATION
        ).exists()

    return render(
        request,
        "bdc/_detail_sidebar.html",
        {
            "bdc": bdc,
            "lignes": lignes,
            "historique": historique,
            "transitions": transitions,
            "form_edition": form_edition,
            "checklist_transitions": checklist_transitions,
        },
    )


@login_required
def detail_bdc(request, pk: int):
    """Fiche de détail d'un BDC — accessible à tous les utilisateurs authentifiés."""

    bdc = get_object_or_404(BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk)
    lignes = bdc.lignes_prestation.all()
    historique = bdc.historique.all()[:10]

    form_edition = BDCEditionForm(instance=bdc) if bdc.statut == StatutChoices.A_TRAITER else None
    transitions = [(statut, StatutChoices(statut).label) for statut in SIDEBAR_TRANSITIONS.get(bdc.statut, [])]

    return render(
        request,
        "bdc/detail.html",
        {
            "bdc": bdc,
            "lignes": lignes,
            "historique": historique,
            "form_edition": form_edition,
            "transitions": transitions,
        },
    )


@login_required
def modifier_bdc(request, pk: int):
    """POST-only : sauvegarde les champs manuels depuis la fiche détail."""
    if request.method != "POST":
        return redirect("bdc:detail", pk=pk)

    bdc = get_object_or_404(BonDeCommande, pk=pk)
    form = BDCEditionForm(request.POST, instance=bdc)
    if form.is_valid():
        form.save()
        enregistrer_action(bdc, request.user, ActionChoices.MODIFICATION)
        messages.success(request, "BDC mis à jour.")
    else:
        for erreurs in form.errors.values():
            for erreur in erreurs:
                messages.error(request, erreur)
    return redirect("bdc:detail", pk=pk)


@login_required
def sidebar_save_and_transition(request, pk: int):
    """POST: save edition form + optional status transition, return updated sidebar partial."""
    if request.method != "POST":
        return redirect("bdc:detail", pk=pk)

    bdc = get_object_or_404(BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk)
    form = BDCEditionForm(request.POST, instance=bdc)
    error_message = None

    if form.is_valid():
        form.save()
        enregistrer_action(bdc, request.user, ActionChoices.MODIFICATION)

        nouveau_statut = form.cleaned_data.get("nouveau_statut")
        if nouveau_statut:
            try:
                changer_statut(bdc, nouveau_statut, request.user)
            except (TransitionInvalide, BDCIncomplet) as e:
                error_message = str(e)

    # Rebuild sidebar context

    bdc.refresh_from_db()
    lignes = bdc.lignes_prestation.all()
    historique = bdc.historique.all()[:10]

    transitions = [(statut, StatutChoices(statut).label) for statut in SIDEBAR_TRANSITIONS.get(bdc.statut, [])]
    form_edition = BDCEditionForm(instance=bdc) if bdc.statut == StatutChoices.A_TRAITER else None

    # Déterminer si des checklists existent pour les transitions du statut courant
    checklist_transitions = {}
    if bdc.statut == StatutChoices.EN_COURS:
        checklist_transitions["EN_COURS__A_FACTURER"] = ChecklistItem.objects.filter(
            actif=True, transition=TransitionChoices.REALISATION
        ).exists()
    elif bdc.statut == StatutChoices.A_FACTURER:
        checklist_transitions["A_FACTURER__FACTURE"] = ChecklistItem.objects.filter(
            actif=True, transition=TransitionChoices.FACTURATION
        ).exists()

    response = render(
        request,
        "bdc/_detail_sidebar.html",
        {
            "bdc": bdc,
            "lignes": lignes,
            "historique": historique,
            "transitions": transitions,
            "form_edition": form_edition,
            "error_message": error_message,
            "checklist_transitions": checklist_transitions,
        },
    )
    response["HX-Trigger"] = "bdc-updated"
    return response


@login_required
def changer_statut_bdc(request, pk: int):
    """POST-only : applique une transition de statut sur le BDC."""
    if request.method != "POST":
        return redirect("bdc:detail", pk=pk)

    bdc = get_object_or_404(BonDeCommande, pk=pk)
    nouveau_statut = request.POST.get("nouveau_statut", "")

    try:
        changer_statut(bdc, nouveau_statut, request.user)
        messages.success(request, f"Statut changé en « {bdc.get_statut_display()} ».")
    except TransitionInvalide:
        messages.error(request, "Cette transition de statut n'est pas autorisée.")
    except BDCIncomplet as e:
        messages.error(request, str(e))

    return redirect("bdc:detail", pk=pk)


def _msg_attribution(bdc, reattribution=False):
    """Construit le message flash d'attribution avec lien retour."""
    lien_retour = reverse("bdc:index") + "?statut=A_FAIRE"
    verbe = "réattribué" if reattribution else "attribué"
    base = f"BDC n°{bdc.numero_bdc} {verbe} à {bdc.sous_traitant}. "
    if bdc.sous_traitant and bdc.sous_traitant.email:
        base += "Un email lui a été adressé. "
    lien = f'<a href="{lien_retour}" class="underline font-medium">Continuer les attributions →</a>'
    return mark_safe(base + lien)


# ─── Attribution / Réattribution ─────────────────────────────────────────


def _get_checklist_attribution(bdc):
    """Retourne les items de checklist pour la transition d'attribution du BDC."""
    if bdc.statut == StatutChoices.A_FAIRE:
        transition = TransitionChoices.ATTRIBUTION
    else:
        return []
    return list(ChecklistItem.objects.filter(actif=True, transition=transition).order_by("ordre"))


def _save_checklist_from_post(bdc, request, items):
    """Enregistre les résultats de checklist depuis les données POST."""
    for item in items:
        coche = request.POST.get(f"checklist_{item.pk}") == "on"
        ChecklistResultat.objects.update_or_create(bdc=bdc, item=item, defaults={"coche": coche})


@login_required
def attribuer_bdc(request, pk: int):
    """GET : formulaire d'attribution — POST : attribue le BDC à un ST."""
    bdc = get_object_or_404(BonDeCommande.objects.select_related("bailleur"), pk=pk)

    if bdc.statut != StatutChoices.A_FAIRE:
        messages.error(request, "Ce BDC n'est pas en statut « À attribuer ».")
        return redirect("bdc:detail", pk=pk)

    checklist_items = _get_checklist_attribution(bdc)
    ctx = {
        "bdc": bdc,
        "checklist_items": checklist_items,
        "prix_forfaitaires": PrixForfaitaire.objects.filter(actif=True),
    }

    if request.method == "GET":
        ctx["form"] = AttributionForm()
        return render(request, "bdc/attribuer.html", ctx)

    form = AttributionForm(request.POST)
    if not form.is_valid():
        ctx["form"] = form
        return render(request, "bdc/attribuer.html", ctx)

    _save_checklist_from_post(bdc, request, checklist_items)

    mode = form.cleaned_data.get("mode_attribution", "pourcentage")
    lignes_forfait = _parse_lignes_forfait(request.POST) if mode == "forfait" else None

    try:
        attribuer_st(
            bdc,
            form.cleaned_data["sous_traitant"],
            form.cleaned_data.get("pourcentage_st"),
            request.user,
            commentaire=form.cleaned_data.get("commentaire", ""),
            mode=mode,
            lignes_forfait=lignes_forfait,
        )
    except (TransitionInvalide, BDCIncomplet) as e:
        messages.error(request, str(e))
        return redirect("bdc:detail", pk=pk)

    notifier_st_attribution(bdc)
    messages.success(request, _msg_attribution(bdc))
    return redirect("bdc:detail", pk=pk)


@login_required
def reattribuer_bdc(request, pk: int):
    """GET : formulaire pré-rempli — POST : réattribue le BDC à un autre ST."""
    bdc = get_object_or_404(BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk)

    if bdc.statut != StatutChoices.EN_COURS:
        messages.error(request, "Ce BDC n'est pas en statut « En cours ».")
        return redirect("bdc:detail", pk=pk)

    if request.method == "GET":
        form = AttributionForm(
            initial={
                "sous_traitant": bdc.sous_traitant_id,
                "pourcentage_st": bdc.pourcentage_st,
            }
        )
        return render(
            request,
            "bdc/attribuer.html",
            {
                "bdc": bdc,
                "form": form,
                "reattribution": True,
                "prix_forfaitaires": PrixForfaitaire.objects.filter(actif=True),
            },
        )

    form = AttributionForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "bdc/attribuer.html",
            {
                "bdc": bdc,
                "form": form,
                "reattribution": True,
                "prix_forfaitaires": PrixForfaitaire.objects.filter(actif=True),
            },
        )

    mode = form.cleaned_data.get("mode_attribution", "pourcentage")
    lignes_forfait = _parse_lignes_forfait(request.POST) if mode == "forfait" else None

    try:
        reattribuer_st(
            bdc,
            form.cleaned_data["sous_traitant"],
            form.cleaned_data.get("pourcentage_st"),
            request.user,
            commentaire=form.cleaned_data.get("commentaire", ""),
            mode=mode,
            lignes_forfait=lignes_forfait,
        )
    except (TransitionInvalide, BDCIncomplet) as e:
        messages.error(request, str(e))
        return redirect("bdc:detail", pk=pk)

    notifier_st_attribution(bdc)
    messages.success(request, _msg_attribution(bdc, reattribution=True))
    return redirect("bdc:detail", pk=pk)


# ─── Attribution inline (HTMX partial) ──────────────────────────────────────


def _get_repartition_st(date_du=None, date_au=None, statuts=None, date_field="emission"):
    """
    Retourne tous les ST actifs avec leur charge (nb BDC + montant_st total).

    Args:
        date_du/date_au: bornes de periode.
        statuts: liste de StatutChoices a filtrer.
        date_field: "emission" (Coalesce date_emission/created_at) ou "created" (created_at).
    """
    from apps.sous_traitants.models import SousTraitant

    if statuts is None:
        statuts = [StatutChoices.EN_COURS, StatutChoices.A_FACTURER, StatutChoices.FACTURE]

    filtre = Q(bons_de_commande__statut__in=statuts)

    if date_du and date_au:
        if date_field == "created":
            filtre &= Q(
                bons_de_commande__created_at__date__gte=date_du,
                bons_de_commande__created_at__date__lte=date_au,
            )
        else:
            filtre &= Q(
                bons_de_commande__in=BonDeCommande.objects.annotate(
                    _date_ref=Coalesce("date_emission", "created_at__date")
                ).filter(_date_ref__gte=date_du, _date_ref__lte=date_au)
            )

    return (
        SousTraitant.objects.filter(Q(actif=True) | Q(bons_de_commande__statut__in=statuts))
        .distinct()
        .annotate(
            nb_bdc=Count("bons_de_commande", filter=filtre),
            total_montant_st=Sum("bons_de_commande__montant_st", filter=filtre),
        )
        .order_by("nom")
    )


@login_required
def attribution_split(request, pk: int):
    """Page split-screen d'attribution : PDF a gauche, panneau d'action a droite."""
    bdc = get_object_or_404(BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk)
    reattribution = bdc.statut == StatutChoices.EN_COURS

    if bdc.statut not in (StatutChoices.A_FAIRE, StatutChoices.EN_COURS):
        messages.error(request, "Ce BDC ne peut pas être attribué dans son statut actuel.")
        return redirect("bdc:detail", pk=pk)

    date_du, date_au, date_du_n1, date_au_n1, periode_active = _parse_periode_params(request)
    checklist_items = _get_checklist_attribution(bdc)

    def _panel_context(form):
        repartition = list(_get_repartition_st(date_du=date_du, date_au=date_au, date_field="created"))
        return {
            "bdc": bdc,
            "form": form,
            "reattribution": reattribution,
            "repartition": repartition,
            "has_n1": False,
            "periodes": PERIODES_CHOICES,
            "periode_active": periode_active,
            "date_du": date_du.isoformat() if date_du else "",
            "date_au": date_au.isoformat() if date_au else "",
            "hx_url": reverse("bdc:attribution_split", kwargs={"pk": bdc.pk}),
            "hx_target": "#attribution-panel",
            "checklist_items": checklist_items,
            "prix_forfaitaires": PrixForfaitaire.objects.filter(actif=True),
        }

    if request.method == "POST":
        form = AttributionForm(request.POST)
        if form.is_valid():
            st = form.cleaned_data["sous_traitant"]
            pct = form.cleaned_data.get("pourcentage_st")
            commentaire = form.cleaned_data.get("commentaire", "")
            mode = form.cleaned_data.get("mode_attribution", "pourcentage")
            lignes_forfait = _parse_lignes_forfait(request.POST) if mode == "forfait" else None
            _save_checklist_from_post(bdc, request, checklist_items)
            try:
                if reattribution:
                    reattribuer_st(
                        bdc,
                        st,
                        pct,
                        request.user,
                        commentaire=commentaire,
                        mode=mode,
                        lignes_forfait=lignes_forfait,
                    )
                else:
                    attribuer_st(
                        bdc,
                        st,
                        pct,
                        request.user,
                        commentaire=commentaire,
                        mode=mode,
                        lignes_forfait=lignes_forfait,
                    )
            except (TransitionInvalide, BDCIncomplet) as e:
                messages.error(request, str(e))
                return redirect("bdc:detail", pk=pk)
            notifier_st_attribution(bdc)
            messages.success(request, _msg_attribution(bdc, reattribution=reattribution))
            return redirect("bdc:detail", pk=bdc.pk)
        ctx = _panel_context(form)
        if request.headers.get("HX-Request"):
            return render(request, "bdc/partials/_attribution_panel.html", ctx)
        return render(request, "bdc/attribution_split.html", ctx)

    # GET
    initial = {}
    if reattribution and bdc.sous_traitant:
        initial = {"sous_traitant": bdc.sous_traitant, "pourcentage_st": bdc.pourcentage_st}
    form = AttributionForm(initial=initial)
    ctx = _panel_context(form)

    if request.headers.get("HX-Request"):
        return render(request, "bdc/partials/_attribution_panel.html", ctx)
    return render(request, "bdc/attribution_split.html", ctx)


@login_required
def attribution_partial(request, pk: int):
    """Partial HTMX : tableau repartition ST + formulaire attribution/reattribution."""
    bdc = get_object_or_404(BonDeCommande, pk=pk)
    reattribution = bdc.statut == StatutChoices.EN_COURS

    # Detecter le contexte d'appel via le header HX-Target
    hx_target_id = request.headers.get("HX-Target", "attribution-zone")
    hx_target = f"#{hx_target_id}"

    date_du, date_au, date_du_n1, date_au_n1, periode_active = _parse_periode_params(request)
    checklist_items = _get_checklist_attribution(bdc)

    def _build_context(form):
        repartition = list(_get_repartition_st(date_du=date_du, date_au=date_au, date_field="created"))
        return {
            "bdc": bdc,
            "form": form,
            "reattribution": reattribution,
            "repartition": repartition,
            "has_n1": False,
            "periodes": PERIODES_CHOICES,
            "periode_active": periode_active,
            "date_du": date_du.isoformat() if date_du else "",
            "date_au": date_au.isoformat() if date_au else "",
            "hx_url": reverse("bdc:attribution_partial", kwargs={"pk": bdc.pk}),
            "hx_target": hx_target,
            "checklist_items": checklist_items,
            "prix_forfaitaires": PrixForfaitaire.objects.filter(actif=True),
        }

    if request.method == "POST":
        form = AttributionForm(request.POST)
        if form.is_valid():
            st = form.cleaned_data["sous_traitant"]
            pct = form.cleaned_data.get("pourcentage_st")
            commentaire = form.cleaned_data.get("commentaire", "")
            mode = form.cleaned_data.get("mode_attribution", "pourcentage")
            lignes_forfait = _parse_lignes_forfait(request.POST) if mode == "forfait" else None
            _save_checklist_from_post(bdc, request, checklist_items)
            try:
                if reattribution:
                    reattribuer_st(
                        bdc,
                        st,
                        pct,
                        request.user,
                        commentaire=commentaire,
                        mode=mode,
                        lignes_forfait=lignes_forfait,
                    )
                else:
                    attribuer_st(
                        bdc,
                        st,
                        pct,
                        request.user,
                        commentaire=commentaire,
                        mode=mode,
                        lignes_forfait=lignes_forfait,
                    )
            except (TransitionInvalide, BDCIncomplet) as e:
                messages.error(request, str(e))
                return redirect("bdc:detail", pk=pk)
            notifier_st_attribution(bdc)
            messages.success(request, _msg_attribution(bdc, reattribution=reattribution))
            response = HttpResponse(status=204)
            response["HX-Redirect"] = reverse("bdc:detail", kwargs={"pk": bdc.pk})
            return response
        return render(request, "bdc/partials/attribution_form.html", _build_context(form))

    # GET
    initial = {}
    if reattribution and bdc.sous_traitant:
        initial = {"sous_traitant": bdc.sous_traitant, "pourcentage_st": bdc.pourcentage_st}
    form = AttributionForm(initial=initial)
    return render(request, "bdc/partials/attribution_form.html", _build_context(form))


# ─── Validation réalisation / Facturation ────────────────────────────────────


@login_required
def valider_realisation_bdc(request, pk: int):
    """POST-only : le CDT valide la réalisation (EN_COURS → A_FACTURER)."""
    if request.method != "POST":
        return redirect("bdc:detail", pk=pk)

    bdc = get_object_or_404(BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk)

    try:
        valider_realisation(bdc, request.user)
    except TransitionInvalide as e:
        if request.headers.get("HX-Request"):
            return _render_sidebar(request, bdc, error_message=str(e))
        messages.error(request, str(e))
        return redirect("bdc:detail", pk=pk)

    if request.headers.get("HX-Request"):
        return _render_sidebar(request, bdc, success_message=f"BDC n°{bdc.numero_bdc} : réalisation validée.")

    messages.success(request, f"BDC n°{bdc.numero_bdc} : réalisation validée.")
    return redirect("bdc:detail", pk=pk)


@login_required
def valider_facturation_bdc(request, pk: int):
    """POST-only : le CDT passe le BDC en facturation (A_FACTURER → FACTURE)."""
    if request.method != "POST":
        return redirect("bdc:detail", pk=pk)

    bdc = get_object_or_404(BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk)

    try:
        valider_facturation(bdc, request.user)
    except (TransitionInvalide, BDCIncomplet) as e:
        if request.headers.get("HX-Request"):
            return _render_sidebar(request, bdc, error_message=str(e))
        messages.error(request, str(e))
        return redirect("bdc:detail", pk=pk)
    except Exception:
        logger.exception("Erreur inattendue lors de la facturation du BDC n°%s", bdc.numero_bdc)
        msg = f"Erreur lors du passage en facturation du BDC n°{bdc.numero_bdc}. Veuillez réessayer."
        if request.headers.get("HX-Request"):
            return _render_sidebar(request, bdc, error_message=msg)
        messages.error(request, msg)
        return redirect("bdc:detail", pk=pk)

    if request.headers.get("HX-Request"):
        return _render_sidebar(request, bdc, success_message=f"BDC n°{bdc.numero_bdc} : passé en facturation.")

    messages.success(request, f"BDC n°{bdc.numero_bdc} : passé en facturation.")
    return redirect("bdc:detail", pk=pk)


# Map transition_key → (service_function, success_message)
_TRANSITION_ACTIONS = {
    "EN_COURS__A_FACTURER": (valider_realisation, "réalisation validée"),
    "A_FACTURER__FACTURE": (valider_facturation, "passé en facturation"),
}


@login_required
def sidebar_checklist(request, pk: int):
    """GET: affiche la checklist pour une transition. POST: sauvegarde + tente la transition."""
    bdc = get_object_or_404(BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk)
    transition_key = request.GET.get("transition") or request.POST.get("transition", "")

    items = list(ChecklistItem.objects.filter(actif=True, transition=transition_key))

    if request.method == "POST":
        # Sauvegarder les résultats
        for item in items:
            coche = f"check_{item.pk}" in request.POST
            ChecklistResultat.objects.update_or_create(
                bdc=bdc,
                item=item,
                defaults={"coche": coche},
            )

        # Tenter la transition
        action_info = _TRANSITION_ACTIONS.get(transition_key)
        if action_info:
            try:
                action_info[0](bdc, request.user)
                return _render_sidebar(
                    request,
                    bdc,
                    success_message=f"BDC n°{bdc.numero_bdc} : {action_info[1]}.",
                )
            except (TransitionInvalide, BDCIncomplet) as e:
                items_deja_coches = set(
                    bdc.checklist_resultats.filter(item__transition=transition_key, coche=True).values_list(
                        "item_id", flat=True
                    )
                )
                return render(
                    request,
                    "bdc/partials/_checklist_transition.html",
                    {
                        "bdc": bdc,
                        "checklist_items": items,
                        "transition_key": transition_key,
                        "items_deja_coches": items_deja_coches,
                        "error_message": str(e),
                    },
                )

        return _render_sidebar(request, bdc)

    # GET: si pas d'items, faire la transition directement
    if not items:
        action_info = _TRANSITION_ACTIONS.get(transition_key)
        if action_info:
            try:
                action_info[0](bdc, request.user)
                return _render_sidebar(
                    request,
                    bdc,
                    success_message=f"BDC n°{bdc.numero_bdc} : {action_info[1]}.",
                )
            except (TransitionInvalide, BDCIncomplet) as e:
                return _render_sidebar(request, bdc, error_message=str(e))

    items_deja_coches = set(
        bdc.checklist_resultats.filter(item__transition=transition_key, coche=True).values_list("item_id", flat=True)
    )
    return render(
        request,
        "bdc/partials/_checklist_transition.html",
        {
            "bdc": bdc,
            "checklist_items": items,
            "transition_key": transition_key,
            "items_deja_coches": items_deja_coches,
        },
    )


# ─── Renvoi CDT → Secrétaire ────────────────────────────────────────────────


@login_required
def renvoyer_controle_bdc(request, pk: int):
    """POST: CDT renvoie un BDC A_FAIRE au contrôle avec un commentaire."""
    if request.method != "POST":
        return redirect("bdc:detail", pk=pk)

    bdc = get_object_or_404(BonDeCommande, pk=pk)
    commentaire = request.POST.get("commentaire", "").strip()

    if not commentaire:
        messages.error(request, "Le commentaire est obligatoire pour renvoyer un BDC.")
        return redirect("bdc:detail", pk=pk)

    try:
        renvoyer_controle(bdc, commentaire, request.user)
        messages.success(request, f"BDC n°{bdc.numero_bdc} renvoyé au contrôle.")
    except TransitionInvalide as e:
        messages.error(request, str(e))

    return redirect("bdc:detail", pk=pk)


# ─── Recoupement par sous-traitant ────────────────────────────────────────────


@login_required
def recoupement_st_liste(request):
    """Liste des sous-traitants avec compteurs BDC par statut, filtrable par periode."""
    statuts = [StatutChoices.EN_COURS, StatutChoices.A_FACTURER, StatutChoices.FACTURE]

    date_du, date_au, date_du_n1, date_au_n1, periode_active = _parse_periode_params(request)

    sous_traitants = list(_get_repartition_st(date_du=date_du, date_au=date_au, statuts=statuts).filter(nb_bdc__gt=0))

    has_n1 = _attach_n1_data(sous_traitants, date_du_n1, date_au_n1, statuts=statuts, with_delta=True)

    context = {
        "sous_traitants": sous_traitants,
        "has_n1": has_n1,
        "periodes": PERIODES_CHOICES,
        "periode_active": periode_active,
        "date_du": date_du.isoformat() if date_du else "",
        "date_au": date_au.isoformat() if date_au else "",
        "hx_url": reverse("bdc:recoupement_liste"),
        "hx_target": "#recoupement-content",
    }

    if request.headers.get("HX-Request"):
        return render(request, "bdc/_recoupement_content.html", context)

    return render(request, "bdc/recoupement_liste.html", context)


@login_required
def recoupement_st_detail(request, st_pk: int):
    """BDC d'un sous-traitant donné, avec filtre par statut."""
    from apps.sous_traitants.models import SousTraitant

    sous_traitant = get_object_or_404(SousTraitant, pk=st_pk)
    queryset = BonDeCommande.objects.filter(sous_traitant=sous_traitant).select_related("bailleur")

    filtre_statut = request.GET.get("statut", "")
    if filtre_statut in [StatutChoices.EN_COURS, StatutChoices.A_FACTURER, StatutChoices.FACTURE]:
        queryset = queryset.filter(statut=filtre_statut)

    return render(
        request,
        "bdc/recoupement_detail.html",
        {
            "sous_traitant": sous_traitant,
            "bdc_list": queryset,
            "filtre_statut": filtre_statut,
            "statut_choices": StatutChoices,
        },
    )


# ─── Export facturation ──────────────────────────────────────────────────────


@login_required
def export_facturation(request):
    """GET : formulaire de filtres avec aperçu. POST : téléchargement Excel."""
    from .exports import generer_export_excel
    from .forms import ExportFacturationForm

    form = ExportFacturationForm(request.GET or None)

    # Queryset de base : BDC à facturer + facturés
    queryset = BonDeCommande.objects.filter(
        statut__in=[StatutChoices.A_FACTURER, StatutChoices.FACTURE]
    ).select_related("bailleur", "sous_traitant")

    # Appliquer les filtres
    if form.is_valid():
        if form.cleaned_data.get("statut"):
            queryset = queryset.filter(statut=form.cleaned_data["statut"])
        if form.cleaned_data.get("sous_traitant"):
            queryset = queryset.filter(sous_traitant=form.cleaned_data["sous_traitant"])
        if form.cleaned_data.get("date_du"):
            queryset = queryset.filter(date_realisation__gte=form.cleaned_data["date_du"])
        if form.cleaned_data.get("date_au"):
            queryset = queryset.filter(date_realisation__lte=form.cleaned_data["date_au"])

    count = queryset.count()

    if request.method == "POST":
        return generer_export_excel(queryset)

    return render(
        request,
        "bdc/export_facturation.html",
        {
            "form": form,
            "count": count,
        },
    )


# ─── Contrôle BDC (split-screen PDF + checklist) ─────────────────────────────


@login_required
def controle_bdc(request, pk: int):
    """Page de contrôle BDC : split-screen PDF + checklist + formulaire d'édition."""
    bdc = get_object_or_404(BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk)
    est_editable = bdc.statut == StatutChoices.A_TRAITER

    items = ChecklistItem.objects.filter(actif=True, transition=TransitionChoices.CONTROLE)

    if request.method == "POST" and est_editable:
        # Sauver le formulaire d'édition
        form = BDCEditionForm(request.POST, instance=bdc)
        form_valid = form.is_valid()
        if form_valid:
            form.save()
            enregistrer_action(bdc, request.user, ActionChoices.MODIFICATION)

        # Sauver les coches checklist
        for item in items:
            coche = request.POST.get(f"check_{item.pk}") == "on"
            note = request.POST.get(f"note_{item.pk}", "").strip()
            ChecklistResultat.objects.update_or_create(
                bdc=bdc,
                item=item,
                defaults={"coche": coche, "note": note},
            )

        # Transition si demandée ET formulaire valide
        nouveau_statut = request.POST.get("nouveau_statut")
        if nouveau_statut and form_valid:
            try:
                changer_statut(bdc, nouveau_statut, request.user)
                messages.success(
                    request,
                    f"BDC n°{bdc.numero_bdc} validé — statut : À attribuer.",
                )
                return redirect("bdc:index")
            except (TransitionInvalide, BDCIncomplet) as e:
                messages.error(request, str(e))

        bdc.refresh_from_db()
        # form conservé avec ses erreurs (pas remplacé par un formulaire vierge)
    else:
        form = BDCEditionForm(instance=bdc) if est_editable else None

    # Build combined checklist data for template
    resultats = {r.item_id: r for r in bdc.checklist_resultats.filter(item__actif=True)}
    checklist_items = []
    for item in items:
        res = resultats.get(item.pk)
        checklist_items.append(
            {
                "item": item,
                "coche": res.coche if res else False,
                "note": res.note if res else "",
            }
        )

    # Check for recent renvoi (CDT comment)
    dernier_renvoi = bdc.historique.filter(action=ActionChoices.RENVOI).order_by("-created_at").first()

    return render(
        request,
        "bdc/controle.html",
        {
            "bdc": bdc,
            "form_edition": form,
            "checklist_items": checklist_items,
            "est_editable": est_editable,
            "dernier_renvoi": dernier_renvoi,
        },
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────


# ─── Relevés de facturation ─────────────────────────────────────────────────


@login_required
def releve_creer(request, st_pk: int):
    """POST-only : crée un relevé brouillon pour un ST."""
    from apps.sous_traitants.models import SousTraitant

    from .releves import ReleveError, creer_releve

    if request.method != "POST":
        return redirect("bdc:recoupement_liste")

    sous_traitant = get_object_or_404(SousTraitant, pk=st_pk)
    try:
        releve = creer_releve(sous_traitant, request.user)
        messages.success(request, f"Relevé n°{releve.numero} créé pour {sous_traitant.nom}.")
        return redirect("bdc:releve_detail", pk=releve.pk)
    except ReleveError as e:
        messages.error(request, str(e))
        return redirect("bdc:recoupement_liste")


@login_required
def releve_detail(request, pk: int):
    """Détail d'un relevé : liste des BDC, montant total, actions."""
    from .models import ActionChoices, HistoriqueAction, ReleveFacturation

    releve = get_object_or_404(
        ReleveFacturation.objects.select_related("sous_traitant", "cree_par"),
        pk=pk,
    )
    bdc_list = list(releve.bdc.select_related("bailleur").order_by("date_realisation"))

    # Annoter chaque BDC avec sa date d'attribution (depuis HistoriqueAction)
    bdc_ids = [b.pk for b in bdc_list]
    attributions = {}
    if bdc_ids:
        for ha in HistoriqueAction.objects.filter(
            bdc_id__in=bdc_ids,
            action=ActionChoices.ATTRIBUTION,
        ).order_by("bdc_id", "-created_at"):
            if ha.bdc_id not in attributions:
                attributions[ha.bdc_id] = ha.created_at

    for bdc in bdc_list:
        bdc.date_attribution = attributions.get(bdc.pk)

    return render(
        request,
        "bdc/releve_detail.html",
        {
            "releve": releve,
            "bdc_list": bdc_list,
        },
    )


@login_required
def releve_valider(request, pk: int):
    """POST-only : valide un relevé brouillon."""
    from .models import ReleveFacturation
    from .releves import ReleveError
    from .releves import valider_releve as _valider

    if request.method != "POST":
        return redirect("bdc:releve_detail", pk=pk)

    releve = get_object_or_404(ReleveFacturation, pk=pk)
    try:
        _valider(releve, request.user)
        messages.success(request, f"Relevé n°{releve.numero} validé.")
    except ReleveError as e:
        messages.error(request, str(e))
    return redirect("bdc:releve_detail", pk=pk)


@login_required
def releve_retirer_bdc(request, pk: int, bdc_pk: int):
    """POST-only : retire un BDC d'un relevé brouillon."""
    from .models import ReleveFacturation
    from .releves import ReleveError, retirer_bdc_du_releve

    if request.method != "POST":
        return redirect("bdc:releve_detail", pk=pk)

    releve = get_object_or_404(ReleveFacturation, pk=pk)
    bdc = get_object_or_404(BonDeCommande, pk=bdc_pk)
    try:
        retirer_bdc_du_releve(releve, bdc)
        messages.success(request, f"BDC {bdc.numero_bdc} retiré du relevé.")
    except ReleveError as e:
        messages.error(request, str(e))
    return redirect("bdc:releve_detail", pk=pk)


@login_required
def releve_historique(request, st_pk: int):
    """Historique des relevés d'un ST."""
    from apps.sous_traitants.models import SousTraitant

    from .models import ReleveFacturation

    sous_traitant = get_object_or_404(SousTraitant, pk=st_pk)
    releves = ReleveFacturation.objects.filter(
        sous_traitant=sous_traitant,
    ).order_by("-date_creation")

    return render(
        request,
        "bdc/releve_historique.html",
        {
            "sous_traitant": sous_traitant,
            "releves": releves,
        },
    )


@login_required
def releve_pdf(request, pk: int):
    """Génère et télécharge le PDF du relevé."""
    from .models import ReleveFacturation
    from .releves_export import generer_releve_pdf

    releve = get_object_or_404(
        ReleveFacturation.objects.select_related("sous_traitant"),
        pk=pk,
    )
    return generer_releve_pdf(releve)


@login_required
def releve_excel(request, pk: int):
    """Génère et télécharge l'Excel du relevé."""
    from .models import ReleveFacturation
    from .releves_export import generer_releve_excel

    releve = get_object_or_404(
        ReleveFacturation.objects.select_related("sous_traitant"),
        pk=pk,
    )
    return generer_releve_excel(releve)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _serialiser_pour_session(donnees: dict) -> dict:
    """
    Convertit le dict d'extraction en format JSON-sérialisable pour la session Django.
    Decimal → str, date → ISO string, list de dicts → list normalisée.
    """
    result = {}
    for key, value in donnees.items():
        if isinstance(value, Decimal):
            result[key] = str(value)
        elif isinstance(value, date):
            result[key] = value.isoformat()
        elif isinstance(value, list):
            result[key] = [{k: str(v) if isinstance(v, Decimal) else v for k, v in ligne.items()} for ligne in value]
        else:
            result[key] = value
    return result


# ── Preview fiche chantier ST (tel qu'envoyée au ST) ─────────────────────


@login_required
def pdf_masque_preview(request, pk: int):
    """Sert la fiche chantier PDF générée, telle qu'envoyée au ST."""
    from .fiche_chantier import generer_fiche_chantier

    bdc = get_object_or_404(BonDeCommande.objects.select_related("bailleur"), pk=pk)
    pdf_bytes = generer_fiche_chantier(bdc)

    if not pdf_bytes:
        return HttpResponse("Impossible de générer la fiche chantier.", status=500)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="fiche_chantier_{bdc.numero_bdc}.pdf"'
    return response
