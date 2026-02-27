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
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import group_required
from apps.pdf_extraction.detector import PDFTypeInconnu, detecter_parser

from .forms import BonDeCommandeForm
from .models import ActionChoices, Bailleur, BonDeCommande, LignePrestation, StatutChoices
from .services import BDCIncomplet, changer_statut, enregistrer_action

# ─── Dashboard ────────────────────────────────────────────────────────────────

@login_required
def index(request):
    return HttpResponse("BDC Peinture — Dashboard (à implémenter)")


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
    bdc = get_object_or_404(BonDeCommande, pk=pk)
    lignes = bdc.lignes_prestation.all()
    historique = bdc.historique.all()[:10]
    return render(request, "bdc/detail.html", {
        "bdc": bdc,
        "lignes": lignes,
        "historique": historique,
    })


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
