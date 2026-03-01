"""
Vues du workflow BDC Peinture.
"""
import os
import tempfile
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.accounts.decorators import group_required
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
    StatutChoices,
)
from .notifications import notifier_st_attribution
from .services import (
    BDCIncomplet,
    TransitionInvalide,
    attribuer_st,
    changer_statut,
    enregistrer_action,
    reattribuer_st,
    valider_facturation,
    valider_realisation,
)


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
            Q(numero_bdc__icontains=recherche)
            | Q(adresse__icontains=recherche)
            | Q(occupant_nom__icontains=recherche)
        )

    # Filtres django-filter
    filtre = BonDeCommandeFilter(request.GET, queryset=queryset)
    queryset_filtre = filtre.qs

    # Pagination
    paginator = Paginator(queryset_filtre, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Compteurs par statut (sur l'ensemble, pas le filtré)
    compteurs_qs = (
        BonDeCommande.objects.values("statut")
        .annotate(count=Count("id"))
    )
    compteurs = {s.value: 0 for s in StatutChoices}
    for row in compteurs_qs:
        compteurs[row["statut"]] = row["count"]
    total = sum(compteurs.values())

    is_cdt = request.user.groups.filter(name="CDT").exists()

    # Alertes délais (CDT uniquement)
    alertes_retard = []
    alertes_proches = []
    if is_cdt:
        from apps.notifications.alertes import get_bdc_delai_proche, get_bdc_en_retard

        alertes_retard = get_bdc_en_retard()
        alertes_proches = get_bdc_delai_proche()

    context = {
        "page_obj": page_obj,
        "filtre": filtre,
        "recherche": recherche,
        "compteurs": compteurs,
        "total": total,
        "statut_choices": StatutChoices,
        "is_cdt": is_cdt,
        "alertes_retard": alertes_retard,
        "alertes_proches": alertes_proches,
    }

    # HTMX: return only the dashboard fragment, not the full layout
    if request.headers.get("HX-Request"):
        return render(request, "bdc/_liste_partial.html", context)

    return render(request, "bdc/liste.html", context)


# ─── Upload PDF ───────────────────────────────────────────────────────────────

@group_required("Secretaire")
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

    except PDFTypeInconnu:
        messages.error(request, "Type de PDF non reconnu. Formats supportés : GDH, ERILIA.")
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

@group_required("Secretaire")
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
        return render(request, "bdc/creer_bdc.html", {
            "donnees": donnees,
            "lignes_session": lignes_session,
        })

    # POST : création du BDC depuis les données session
    bailleur_code = donnees.pop("bailleur_code", None)
    bailleur = None
    if bailleur_code:
        try:
            bailleur = Bailleur.objects.get(code=bailleur_code)
        except Bailleur.DoesNotExist:
            messages.error(request, f"Bailleur « {bailleur_code} » introuvable.")
            return render(request, "bdc/creer_bdc.html", {
                "donnees": donnees_session,
                "lignes_session": lignes_session,
                "error_message": f"Bailleur « {bailleur_code} » introuvable en base.",
            })

    numero_bdc = donnees.get("numero_bdc", "").strip()
    if not numero_bdc:
        return render(request, "bdc/creer_bdc.html", {
            "donnees": donnees_session,
            "lignes_session": lignes_session,
            "error_message": "Le numéro BDC n'a pas pu être extrait du PDF.",
        })

    if BonDeCommande.objects.filter(numero_bdc=numero_bdc).exists():
        return render(request, "bdc/creer_bdc.html", {
            "donnees": donnees_session,
            "lignes_session": lignes_session,
            "error_message": f"Le BDC n°{numero_bdc} existe déjà dans le système.",
        })

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

@login_required
def detail_sidebar(request, pk: int):
    """Partial HTML for the HTMX sidebar — no base layout."""

    bdc = get_object_or_404(
        BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk
    )
    lignes = bdc.lignes_prestation.all()
    historique = bdc.historique.all()[:10]

    is_secretaire = request.user.groups.filter(name="Secretaire").exists()
    is_cdt = request.user.groups.filter(name="CDT").exists()

    transitions = []
    if is_secretaire:
        transitions = [
            (statut, StatutChoices(statut).label)
            for statut in SIDEBAR_TRANSITIONS.get(bdc.statut, [])
        ]

    form_edition = BDCEditionForm(instance=bdc) if is_secretaire else None

    return render(request, "bdc/_detail_sidebar.html", {
        "bdc": bdc,
        "lignes": lignes,
        "historique": historique,
        "transitions": transitions,
        "form_edition": form_edition,
        "is_secretaire": is_secretaire,
        "is_cdt": is_cdt,
    })


@login_required
def detail_bdc(request, pk: int):
    """Fiche de détail d'un BDC — accessible à tous les utilisateurs authentifiés."""

    bdc = get_object_or_404(
        BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk
    )
    lignes = bdc.lignes_prestation.all()
    historique = bdc.historique.all()[:10]

    is_secretaire = request.user.groups.filter(name="Secretaire").exists()
    is_cdt = request.user.groups.filter(name="CDT").exists()
    form_edition = BDCEditionForm(instance=bdc) if is_secretaire else None

    transitions = [
        (statut, StatutChoices(statut).label)
        for statut in SIDEBAR_TRANSITIONS.get(bdc.statut, [])
    ] if is_secretaire else []

    return render(request, "bdc/detail.html", {
        "bdc": bdc,
        "lignes": lignes,
        "historique": historique,
        "form_edition": form_edition,
        "transitions": transitions,
        "is_secretaire": is_secretaire,
        "is_cdt": is_cdt,
    })


@group_required("Secretaire")
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


@group_required("Secretaire")
def sidebar_save_and_transition(request, pk: int):
    """POST: save edition form + optional status transition, return updated sidebar partial."""
    if request.method != "POST":
        return redirect("bdc:detail", pk=pk)

    bdc = get_object_or_404(
        BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk
    )
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

    is_secretaire = request.user.groups.filter(name="Secretaire").exists()
    is_cdt = request.user.groups.filter(name="CDT").exists()

    transitions = []
    if is_secretaire:
        transitions = [
            (statut, StatutChoices(statut).label)
            for statut in SIDEBAR_TRANSITIONS.get(bdc.statut, [])
        ]

    form_edition = BDCEditionForm(instance=bdc)

    response = render(request, "bdc/_detail_sidebar.html", {
        "bdc": bdc,
        "lignes": lignes,
        "historique": historique,
        "transitions": transitions,
        "form_edition": form_edition,
        "is_secretaire": is_secretaire,
        "is_cdt": is_cdt,
        "error_message": error_message,
    })
    response["HX-Trigger"] = "bdc-updated"
    return response


@group_required("Secretaire")
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


# ─── Attribution / Réattribution ─────────────────────────────────────────

@group_required("CDT")
def attribuer_bdc(request, pk: int):
    """GET : formulaire d'attribution — POST : attribue le BDC à un ST."""
    bdc = get_object_or_404(
        BonDeCommande.objects.select_related("bailleur"), pk=pk
    )

    if bdc.statut != StatutChoices.A_FAIRE:
        messages.error(request, "Ce BDC n'est pas en statut « À attribuer ».")
        return redirect("bdc:detail", pk=pk)

    if request.method == "GET":
        form = AttributionForm()
        return render(request, "bdc/attribuer.html", {"bdc": bdc, "form": form})

    form = AttributionForm(request.POST)
    if not form.is_valid():
        return render(request, "bdc/attribuer.html", {"bdc": bdc, "form": form})

    try:
        attribuer_st(
            bdc,
            form.cleaned_data["sous_traitant"],
            form.cleaned_data["pourcentage_st"],
            request.user,
        )
    except TransitionInvalide as e:
        messages.error(request, str(e))
        return redirect("bdc:detail", pk=pk)

    notifier_st_attribution(bdc)
    messages.success(
        request,
        f"BDC attribué à {bdc.sous_traitant} ({bdc.pourcentage_st} %).",
    )
    return redirect("bdc:detail", pk=pk)


@group_required("CDT")
def reattribuer_bdc(request, pk: int):
    """GET : formulaire pré-rempli — POST : réattribue le BDC à un autre ST."""
    bdc = get_object_or_404(
        BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk
    )

    if bdc.statut != StatutChoices.EN_COURS:
        messages.error(request, "Ce BDC n'est pas en statut « En cours ».")
        return redirect("bdc:detail", pk=pk)

    if request.method == "GET":
        form = AttributionForm(initial={
            "sous_traitant": bdc.sous_traitant_id,
            "pourcentage_st": bdc.pourcentage_st,
        })
        return render(request, "bdc/attribuer.html", {
            "bdc": bdc, "form": form, "reattribution": True,
        })

    form = AttributionForm(request.POST)
    if not form.is_valid():
        return render(request, "bdc/attribuer.html", {
            "bdc": bdc, "form": form, "reattribution": True,
        })

    try:
        reattribuer_st(
            bdc,
            form.cleaned_data["sous_traitant"],
            form.cleaned_data["pourcentage_st"],
            request.user,
        )
    except TransitionInvalide as e:
        messages.error(request, str(e))
        return redirect("bdc:detail", pk=pk)

    notifier_st_attribution(bdc)
    messages.success(
        request,
        f"BDC réattribué à {bdc.sous_traitant} ({bdc.pourcentage_st} %).",
    )
    return redirect("bdc:detail", pk=pk)


# ─── Attribution inline (HTMX partial) ──────────────────────────────────────


def _get_repartition_st(date_du=None, date_au=None, statuts=None):
    """
    Retourne tous les ST actifs avec leur charge (nb BDC + montant_st total).

    Args:
        date_du/date_au: bornes de periode (filtre sur Coalesce(date_emission, created_at)).
        statuts: liste de StatutChoices a filtrer (defaut: [EN_COURS]).
    """
    from apps.sous_traitants.models import SousTraitant

    if statuts is None:
        statuts = [StatutChoices.EN_COURS]

    filtre = Q(bons_de_commande__statut__in=statuts)

    if date_du and date_au:
        filtre &= Q(
            bons_de_commande__in=BonDeCommande.objects.annotate(
                _date_ref=Coalesce("date_emission", "created_at__date")
            ).filter(_date_ref__gte=date_du, _date_ref__lte=date_au)
        )

    return (
        SousTraitant.objects.filter(actif=True)
        .annotate(
            nb_bdc=Count("bons_de_commande", filter=filtre),
            total_montant_st=Sum("bons_de_commande__montant_st", filter=filtre),
        )
        .order_by("nom")
    )


@group_required("CDT")
def attribution_split(request, pk: int):
    """Page split-screen d'attribution : PDF a gauche, panneau d'action a droite."""
    bdc = get_object_or_404(BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk)
    reattribution = bdc.statut == StatutChoices.EN_COURS

    if bdc.statut not in (StatutChoices.A_FAIRE, StatutChoices.EN_COURS):
        messages.error(request, "Ce BDC ne peut pas être attribué dans son statut actuel.")
        return redirect("bdc:detail", pk=pk)

    date_du, date_au, date_du_n1, date_au_n1, periode_active = _parse_periode_params(request)

    def _panel_context(form):
        repartition = list(_get_repartition_st(date_du=date_du, date_au=date_au))
        has_n1 = _attach_n1_data(repartition, date_du_n1, date_au_n1)
        return {
            "bdc": bdc, "form": form, "reattribution": reattribution,
            "repartition": repartition, "has_n1": has_n1,
            "periodes": PERIODES_CHOICES,
            "periode_active": periode_active,
            "date_du": date_du.isoformat() if date_du else "",
            "date_au": date_au.isoformat() if date_au else "",
            "hx_url": reverse("bdc:attribution_split", kwargs={"pk": bdc.pk}),
            "hx_target": "#attribution-panel",
        }

    if request.method == "POST":
        form = AttributionForm(request.POST)
        if form.is_valid():
            st = form.cleaned_data["sous_traitant"]
            pct = form.cleaned_data["pourcentage_st"]
            try:
                if reattribution:
                    reattribuer_st(bdc, st, pct, request.user)
                else:
                    attribuer_st(bdc, st, pct, request.user)
            except TransitionInvalide as e:
                messages.error(request, str(e))
                return redirect("bdc:detail", pk=pk)
            notifier_st_attribution(bdc)
            msg = "réattribué" if reattribution else "attribué"
            messages.success(request, f"BDC n°{bdc.numero_bdc} {msg} à {st}.")
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


@group_required("CDT")
def attribution_partial(request, pk: int):
    """Partial HTMX : tableau repartition ST + formulaire attribution/reattribution."""
    bdc = get_object_or_404(BonDeCommande, pk=pk)
    reattribution = bdc.statut == StatutChoices.EN_COURS

    # Detecter le contexte d'appel via le header HX-Target
    hx_target_id = request.headers.get("HX-Target", "attribution-zone")
    hx_target = f"#{hx_target_id}"

    date_du, date_au, date_du_n1, date_au_n1, periode_active = _parse_periode_params(request)

    def _build_context(form):
        repartition = list(_get_repartition_st(date_du=date_du, date_au=date_au))
        has_n1 = _attach_n1_data(repartition, date_du_n1, date_au_n1)
        return {
            "bdc": bdc, "form": form, "reattribution": reattribution,
            "repartition": repartition, "has_n1": has_n1,
            "periodes": PERIODES_CHOICES,
            "periode_active": periode_active,
            "date_du": date_du.isoformat() if date_du else "",
            "date_au": date_au.isoformat() if date_au else "",
            "hx_url": reverse("bdc:attribution_partial", kwargs={"pk": bdc.pk}),
            "hx_target": hx_target,
        }

    if request.method == "POST":
        form = AttributionForm(request.POST)
        if form.is_valid():
            st = form.cleaned_data["sous_traitant"]
            pct = form.cleaned_data["pourcentage_st"]
            try:
                if reattribution:
                    reattribuer_st(bdc, st, pct, request.user)
                else:
                    attribuer_st(bdc, st, pct, request.user)
            except TransitionInvalide as e:
                messages.error(request, str(e))
                return redirect("bdc:detail", pk=pk)
            notifier_st_attribution(bdc)
            msg = "réattribué" if reattribution else "attribué"
            messages.success(request, f"BDC n°{bdc.numero_bdc} {msg} à {st}.")
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

@group_required("CDT")
def valider_realisation_bdc(request, pk: int):
    """POST-only : le CDT valide la réalisation (EN_COURS → A_FACTURER)."""
    if request.method != "POST":
        return redirect("bdc:detail", pk=pk)

    bdc = get_object_or_404(BonDeCommande, pk=pk)

    try:
        valider_realisation(bdc, request.user)
        messages.success(request, f"BDC n°{bdc.numero_bdc} : réalisation validée.")
    except TransitionInvalide as e:
        messages.error(request, str(e))

    return redirect("bdc:detail", pk=pk)


@group_required("CDT")
def valider_facturation_bdc(request, pk: int):
    """POST-only : le CDT passe le BDC en facturation (A_FACTURER → FACTURE)."""
    if request.method != "POST":
        return redirect("bdc:detail", pk=pk)

    bdc = get_object_or_404(BonDeCommande, pk=pk)

    try:
        valider_facturation(bdc, request.user)
        messages.success(request, f"BDC n°{bdc.numero_bdc} : passé en facturation.")
    except TransitionInvalide as e:
        messages.error(request, str(e))

    return redirect("bdc:detail", pk=pk)


# ─── Recoupement par sous-traitant ────────────────────────────────────────────

@group_required("CDT")
def recoupement_st_liste(request):
    """Liste des sous-traitants avec compteurs BDC par statut, filtrable par periode."""
    statuts = [StatutChoices.EN_COURS, StatutChoices.A_FACTURER, StatutChoices.FACTURE]

    date_du, date_au, date_du_n1, date_au_n1, periode_active = _parse_periode_params(request)

    sous_traitants = list(
        _get_repartition_st(date_du=date_du, date_au=date_au, statuts=statuts).filter(nb_bdc__gt=0)
    )

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


@group_required("CDT")
def recoupement_st_detail(request, st_pk: int):
    """BDC d'un sous-traitant donné, avec filtre par statut."""
    from apps.sous_traitants.models import SousTraitant

    sous_traitant = get_object_or_404(SousTraitant, pk=st_pk)
    queryset = BonDeCommande.objects.filter(sous_traitant=sous_traitant).select_related("bailleur")

    filtre_statut = request.GET.get("statut", "")
    if filtre_statut in [StatutChoices.EN_COURS, StatutChoices.A_FACTURER, StatutChoices.FACTURE]:
        queryset = queryset.filter(statut=filtre_statut)

    return render(request, "bdc/recoupement_detail.html", {
        "sous_traitant": sous_traitant,
        "bdc_list": queryset,
        "filtre_statut": filtre_statut,
        "statut_choices": StatutChoices,
    })


# ─── Export facturation ──────────────────────────────────────────────────────

@group_required("CDT")
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

    return render(request, "bdc/export_facturation.html", {
        "form": form,
        "count": count,
    })


# ─── Contrôle BDC (split-screen PDF + checklist) ─────────────────────────────


@login_required
def controle_bdc(request, pk: int):
    """Page de contrôle BDC : split-screen PDF + checklist + formulaire d'édition."""
    bdc = get_object_or_404(BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk)
    is_secretaire = request.user.groups.filter(name="Secretaire").exists()
    est_editable = is_secretaire and bdc.statut == StatutChoices.A_TRAITER

    items = ChecklistItem.objects.filter(actif=True)

    if request.method == "POST" and est_editable:
        # Sauver le formulaire d'édition
        form = BDCEditionForm(request.POST, instance=bdc)
        if form.is_valid():
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

        # Transition si demandée
        nouveau_statut = request.POST.get("nouveau_statut")
        if nouveau_statut:
            try:
                changer_statut(bdc, nouveau_statut, request.user)
                return redirect("bdc:index")
            except (TransitionInvalide, BDCIncomplet) as e:
                messages.error(request, str(e))

        bdc.refresh_from_db()

    form = BDCEditionForm(instance=bdc) if est_editable else None

    # Build combined checklist data for template
    resultats = {r.item_id: r for r in bdc.checklist_resultats.filter(item__actif=True)}
    checklist_items = []
    for item in items:
        res = resultats.get(item.pk)
        checklist_items.append({
            "item": item,
            "coche": res.coche if res else False,
            "note": res.note if res else "",
        })

    return render(request, "bdc/controle.html", {
        "bdc": bdc,
        "form_edition": form,
        "checklist_items": checklist_items,
        "est_editable": est_editable,
    })


# ─── Téléchargement PDF terrain ───────────────────────────────────────────────

@login_required
def telecharger_terrain(request, pk: int):
    """Sert le PDF terrain (sans prix) en téléchargement."""
    bdc = get_object_or_404(BonDeCommande, pk=pk)

    if not bdc.pdf_terrain:
        raise Http404("Aucun PDF terrain disponible pour ce BDC.")

    return FileResponse(
        bdc.pdf_terrain.open("rb"),
        content_type="application/pdf",
        as_attachment=True,
        filename=f"BDC_{bdc.numero_bdc}_terrain.pdf",
    )


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
            result[key] = [
                {
                    k: str(v) if isinstance(v, Decimal) else v
                    for k, v in ligne.items()
                }
                for ligne in value
            ]
        else:
            result[key] = value
    return result
