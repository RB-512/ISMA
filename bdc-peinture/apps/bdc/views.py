"""
Vues du workflow BDC Peinture.
"""
import os
import tempfile
import uuid
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import group_required
from apps.pdf_extraction.detector import PDFTypeInconnu, detecter_parser

from .filters import BonDeCommandeFilter
from .forms import AttributionForm, BDCEditionForm, BonDeCommandeForm
from .models import ActionChoices, Bailleur, BonDeCommande, LignePrestation, StatutChoices
from .notifications import notifier_st_attribution
from .services import (
    BDCIncomplet,
    TransitionInvalide,
    attribuer_st,
    changer_statut,
    enregistrer_action,
    reattribuer_st,
)

# ─── Dashboard / Liste BDC ───────────────────────────────────────────────────

@login_required
def liste_bdc(request):
    """Tableau de bord : liste paginée des BDC avec filtres et recherche."""
    queryset = BonDeCommande.objects.select_related("bailleur").all()

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
    compteurs = {row["statut"]: row["count"] for row in compteurs_qs}
    total = sum(compteurs.values())

    return render(request, "bdc/liste.html", {
        "page_obj": page_obj,
        "filtre": filtre,
        "recherche": recherche,
        "compteurs": compteurs,
        "total": total,
        "statut_choices": StatutChoices,
    })


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
    GET  → Formulaire pré-rempli depuis la session (données extraites du PDF).
    POST → Valide, crée le BDC, crée les lignes, trace l'historique, redirige.
    """
    donnees_session = request.session.get("bdc_extrait", {})
    lignes_session = donnees_session.pop("lignes_prestation", [])

    # Pré-remplissage : lookup du bailleur par son code
    initial = dict(donnees_session)
    bailleur_code = initial.pop("bailleur_code", None)
    if bailleur_code:
        try:
            initial["bailleur"] = Bailleur.objects.get(code=bailleur_code)
        except Bailleur.DoesNotExist:
            pass

    if request.method == "GET":
        form = BonDeCommandeForm(initial=initial)
        return render(request, "bdc/creer_bdc.html", {
            "form": form,
            "lignes_session": lignes_session,
        })

    # POST : création du BDC
    form = BonDeCommandeForm(request.POST)
    if not form.is_valid():
        return render(request, "bdc/creer_bdc.html", {
            "form": form,
            "lignes_session": lignes_session,
        })

    bdc = form.save(commit=False)
    bdc.cree_par = request.user
    bdc.statut = StatutChoices.A_TRAITER
    bdc.save()

    # Statut conditionnel : A_FAIRE si occupation renseignée
    if bdc.occupation:
        try:
            changer_statut(bdc, StatutChoices.A_FAIRE, request.user)
        except BDCIncomplet:
            pass  # Ne devrait pas arriver (occupation déjà renseignée)

    # Lignes de prestation depuis la session
    for i, ligne_data in enumerate(lignes_session):
        LignePrestation.objects.create(
            bdc=bdc,
            designation=ligne_data.get("designation", ""),
            quantite=Decimal(str(ligne_data.get("quantite", "0"))),
            unite=ligne_data.get("unite", ""),
            prix_unitaire=Decimal(str(ligne_data.get("prix_unitaire", "0"))),
            montant=Decimal(str(ligne_data.get("montant", "0"))),
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
def detail_bdc(request, pk: int):
    """Fiche de détail d'un BDC — accessible à tous les utilisateurs authentifiés."""
    from .services import TRANSITIONS

    bdc = get_object_or_404(
        BonDeCommande.objects.select_related("bailleur", "sous_traitant"), pk=pk
    )
    lignes = bdc.lignes_prestation.all()
    historique = bdc.historique.all()[:10]

    is_secretaire = request.user.groups.filter(name="Secretaire").exists()
    is_cdt = request.user.groups.filter(name="CDT").exists()
    form_edition = BDCEditionForm(instance=bdc) if is_secretaire else None

    # Transitions de statut pour la secrétaire
    # Masquer A_FAIRE → EN_COURS (cette transition passe par l'attribution CDT)
    transitions_possibles = TRANSITIONS.get(bdc.statut, [])
    if bdc.statut == StatutChoices.A_FAIRE:
        transitions_possibles = [s for s in transitions_possibles if s != StatutChoices.EN_COURS]
    transitions = [
        (statut, StatutChoices(statut).label)
        for statut in transitions_possibles
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
        messages.error(request, "Ce BDC n'est pas en statut « À faire ».")
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
