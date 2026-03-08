"""
Vues d'authentification.
Le login/logout est géré par django-allauth, mais on fournit
des vues custom pour styler avec Tailwind.
"""

import os
import tempfile

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.views.generic import TemplateView

from apps.accounts.forms import CreerUtilisateurForm, ModifierRoleForm, ModifierUtilisateurForm
from apps.bdc.models import Bailleur, ChecklistItem, TransitionChoices

User = get_user_model()


class HomeRedirectView(TemplateView):
    """Redirige vers le dashboard BDC."""

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("bdc:index")
        return redirect("account_login")


@login_required
def liste_utilisateurs(request):
    utilisateurs = User.objects.prefetch_related("groups").order_by("last_name", "first_name")
    form_creer = CreerUtilisateurForm()
    return render(
        request,
        "accounts/utilisateurs.html",
        {
            "utilisateurs": utilisateurs,
            "form_creer": form_creer,
        },
    )


@login_required
def creer_utilisateur(request):
    if request.method != "POST":
        return redirect("gestion:liste")
    form = CreerUtilisateurForm(request.POST)
    if form.is_valid():
        user = form.save()
        messages.success(request, f"Compte créé pour {user.get_full_name() or user.username}.")
        return redirect("gestion:liste")
    utilisateurs = User.objects.prefetch_related("groups").order_by("last_name", "first_name")
    return render(
        request,
        "accounts/utilisateurs.html",
        {
            "utilisateurs": utilisateurs,
            "form_creer": form,
        },
    )


@login_required
def modifier_role(request, pk):
    utilisateur = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = ModifierRoleForm(request.POST)
        if form.is_valid():
            group = Group.objects.get(name=form.cleaned_data["role"])
            utilisateur.groups.set([group])
            messages.success(request, f"Rôle mis à jour pour {utilisateur.get_full_name() or utilisateur.username}.")
    return redirect("gestion:liste")


@login_required
def desactiver_utilisateur(request, pk):
    utilisateur = get_object_or_404(User, pk=pk)
    if utilisateur == request.user:
        messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
        return redirect("gestion:liste")
    if request.method == "POST":
        utilisateur.is_active = False
        utilisateur.save()
        messages.success(request, f"Compte de {utilisateur.get_full_name() or utilisateur.username} désactivé.")
    return redirect("gestion:liste")


@login_required
def modifier_utilisateur(request, pk):
    utilisateur = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = ModifierUtilisateurForm(request.POST, instance=utilisateur)
        # Empecher le CDT de modifier son propre role
        if utilisateur == request.user:
            form.fields["role"].disabled = True
        if form.is_valid():
            form.save()
            messages.success(request, f"Profil mis à jour pour {utilisateur.get_full_name() or utilisateur.username}.")
            return redirect("gestion:liste")
    else:
        form = ModifierUtilisateurForm(instance=utilisateur)
        if utilisateur == request.user:
            form.fields["role"].disabled = True
    return render(request, "accounts/partials/_modifier_utilisateur.html", {"form": form, "utilisateur": utilisateur})


@login_required
def reset_password_utilisateur(request, pk):
    utilisateur = get_object_or_404(User, pk=pk)
    if utilisateur == request.user:
        messages.error(request, "Vous ne pouvez pas réinitialiser votre propre mot de passe ici.")
        return redirect("gestion:liste")
    if request.method == "POST":
        new_password = get_random_string(length=10)
        utilisateur.set_password(new_password)
        utilisateur.save()
        return render(
            request,
            "accounts/partials/_reset_password_result.html",
            {"utilisateur": utilisateur, "new_password": new_password},
        )
    return redirect("gestion:liste")


@login_required
def reactiver_utilisateur(request, pk):
    utilisateur = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        utilisateur.is_active = True
        utilisateur.save()
        messages.success(request, f"Compte de {utilisateur.get_full_name() or utilisateur.username} réactivé.")
    return redirect("gestion:liste")


@login_required
def supprimer_utilisateur(request, pk):
    utilisateur = get_object_or_404(User, pk=pk)
    if utilisateur == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect("gestion:liste")
    if request.method == "POST":
        nom = utilisateur.get_full_name() or utilisateur.username
        try:
            utilisateur.delete()
            messages.success(request, f"Compte de {nom} supprimé.")
        except ProtectedError:
            messages.error(
                request,
                f"Impossible de supprimer {nom} car ce compte est lié à des bons de commande. "
                "Désactivez le compte à la place.",
            )
    return redirect("gestion:liste")


# ── Checklist de contrôle ──────────────────────────────────────────────────


@login_required
def checklist_liste(request):
    transition = request.GET.get("transition", TransitionChoices.CONTROLE)
    if transition not in TransitionChoices.values:
        transition = TransitionChoices.CONTROLE

    if request.method == "POST":
        libelle = request.POST.get("libelle", "").strip()
        post_transition = request.POST.get("transition", transition)
        if libelle:
            max_ordre = (
                ChecklistItem.objects.filter(transition=post_transition).aggregate(m=models.Max("ordre"))["m"] or 0
            )
            ChecklistItem.objects.create(libelle=libelle, ordre=max_ordre + 1, transition=post_transition)
            messages.success(request, f"Point de contrôle « {libelle} » ajouté.")
        else:
            messages.error(request, "Le libellé ne peut pas être vide.")
        return redirect(f"{reverse('gestion:checklist_liste')}?transition={post_transition}")

    items = ChecklistItem.objects.filter(transition=transition).order_by("ordre")
    return render(
        request,
        "accounts/checklist.html",
        {
            "items": items,
            "transitions_list": TransitionChoices.choices,
            "transition_active": transition,
        },
    )


@login_required
def checklist_modifier(request, pk):
    item = get_object_or_404(ChecklistItem, pk=pk)
    redirect_url = f"{reverse('gestion:checklist_liste')}?transition={item.transition}"
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "toggle":
            item.actif = not item.actif
            item.save()
            etat = "activé" if item.actif else "désactivé"
            messages.success(request, f"« {item.libelle} » {etat}.")
            return redirect(redirect_url)
        libelle = request.POST.get("libelle", "").strip()
        ordre = request.POST.get("ordre", "").strip()
        if libelle:
            item.libelle = libelle
        if ordre.isdigit():
            item.ordre = int(ordre)
        item.save()
        messages.success(request, f"Point de contrôle « {item.libelle} » mis à jour.")
        return redirect(redirect_url)
    return render(request, "accounts/partials/_modifier_checklist.html", {"item": item})


@login_required
def checklist_supprimer(request, pk):
    item = get_object_or_404(ChecklistItem, pk=pk)
    redirect_url = f"{reverse('gestion:checklist_liste')}?transition={item.transition}"
    if request.method == "POST":
        libelle = item.libelle
        item.delete()
        messages.success(request, f"Point de contrôle « {libelle} » supprimé.")
    return redirect(redirect_url)


# ── Config masquage PDF par bailleur ─────────────────────────────────────


@login_required
def config_bailleurs(request):
    bailleurs = Bailleur.objects.all()

    if request.method == "POST":
        import json

        bailleur_id = request.POST.get("bailleur_id")
        bailleur = get_object_or_404(Bailleur, pk=bailleur_id)
        zones_json = request.POST.get("zones_masquage", "[]")
        try:
            bailleur.zones_masquage = json.loads(zones_json)
        except (json.JSONDecodeError, TypeError):
            bailleur.zones_masquage = []
        pages_raw = request.POST.get("pages_a_envoyer", "").strip()
        if pages_raw:
            bailleur.pages_a_envoyer = [int(p.strip()) for p in pages_raw.split(",") if p.strip().isdigit()]
        else:
            bailleur.pages_a_envoyer = []
        bailleur.save(update_fields=["zones_masquage", "pages_a_envoyer"])
        messages.success(request, f"Configuration de masquage mise à jour pour {bailleur.nom}.")
        if request.headers.get("HX-Request"):
            return render(
                request,
                "accounts/partials/_config_bailleur_form.html",
                {
                    "bailleur": bailleur,
                },
            )
        return redirect("gestion:config_bailleurs")

    return render(
        request,
        "accounts/config_bailleur.html",
        {
            "bailleurs": bailleurs,
        },
    )


@login_required
def config_bailleur_supprimer(request, pk):
    bailleur = get_object_or_404(Bailleur, pk=pk)
    if request.method == "POST":
        if bailleur.bons_de_commande.exists():
            messages.error(
                request,
                f"Impossible de supprimer « {bailleur.nom} » car des bons de commande y sont rattachés.",
            )
        else:
            nom = bailleur.nom
            bailleur.delete()
            messages.success(request, f"Bailleur « {nom} » supprimé.")
    return redirect("gestion:config_bailleurs")


@login_required
def config_bailleur_form(request, pk):
    bailleur = get_object_or_404(Bailleur, pk=pk)
    return render(
        request,
        "accounts/partials/_config_bailleur_form.html",
        {
            "bailleur": bailleur,
        },
    )


# ── Création bailleur ────────────────────────────────────────────────────


@login_required
def config_bailleur_creer(request):
    if request.method != "POST":
        return redirect("gestion:config_bailleurs")

    nom = request.POST.get("nom", "").strip()
    code = request.POST.get("code", "").strip().upper()
    marqueur = request.POST.get("marqueur_detection", "").strip()

    if not nom or not code:
        messages.error(request, "Le nom et le code sont obligatoires.")
        return redirect("gestion:config_bailleurs")

    if Bailleur.objects.filter(code=code).exists():
        messages.error(request, f"Le code « {code} » existe déjà.")
        return redirect("gestion:config_bailleurs")

    bailleur = Bailleur.objects.create(nom=nom, code=code, marqueur_detection=marqueur)
    messages.success(request, f"Bailleur « {bailleur.nom} » créé.")
    return redirect("gestion:config_extraction", pk=bailleur.pk)


# ── Config extraction PDF par template ────────────────────────────────────


@login_required
def config_extraction(request, pk):
    from apps.pdf_extraction.services import extraire_texte_pdf
    from apps.pdf_extraction.template_parser import CHAMPS_STANDARD

    bailleur = get_object_or_404(Bailleur, pk=pk)

    # Extraire texte du PDF modele si present
    texte_pdf = ""
    if bailleur.pdf_modele and bailleur.pdf_modele.name:
        try:
            texte_pdf = extraire_texte_pdf(bailleur.pdf_modele.path)
        except Exception:
            texte_pdf = "(Erreur de lecture du PDF modèle)"

    # Preparer les champs avec leurs labels actuels
    modele = bailleur.modele_extraction or {}
    champs = []
    for champ in CHAMPS_STANDARD:
        config = modele.get(champ, {})
        label = config.get("label", "") if isinstance(config, dict) else ""
        champs.append({"nom": champ, "label": label})

    return render(
        request,
        "accounts/config_extraction.html",
        {
            "bailleur": bailleur,
            "texte_pdf": texte_pdf,
            "champs": champs,
        },
    )


@login_required
def config_extraction_save(request, pk):
    from apps.pdf_extraction.template_parser import CHAMPS_STANDARD

    bailleur = get_object_or_404(Bailleur, pk=pk)

    if request.method != "POST":
        return redirect("gestion:config_extraction", pk=pk)

    # Upload PDF modele si fourni
    pdf_file = request.FILES.get("pdf_modele")
    if pdf_file:
        bailleur.pdf_modele.save(pdf_file.name, pdf_file, save=True)

    # Marqueur detection
    marqueur = request.POST.get("marqueur_detection", "").strip()
    if marqueur:
        bailleur.marqueur_detection = marqueur

    # Construire le modele d'extraction depuis les champs du formulaire
    modele = {}
    for champ in CHAMPS_STANDARD:
        label = request.POST.get(f"label_{champ}", "").strip()
        if label:
            modele[champ] = {"label": label}

    bailleur.modele_extraction = modele
    bailleur.save(update_fields=["marqueur_detection", "modele_extraction"])

    messages.success(request, f"Configuration d'extraction mise à jour pour {bailleur.nom}.")
    return redirect("gestion:config_extraction", pk=pk)


@login_required
def config_extraction_preview(request, pk):
    from apps.pdf_extraction.services import extraire_texte_pdf, preview_extraction

    bailleur = get_object_or_404(Bailleur, pk=pk)

    # Recevoir les labels en cours (POST HTMX)
    modele = {}
    from apps.pdf_extraction.template_parser import CHAMPS_STANDARD

    for champ in CHAMPS_STANDARD:
        label = request.POST.get(f"label_{champ}", "").strip()
        if label:
            modele[champ] = {"label": label}

    # Extraire texte du PDF modele
    texte_pdf = ""
    if bailleur.pdf_modele and bailleur.pdf_modele.name:
        try:
            texte_pdf = extraire_texte_pdf(bailleur.pdf_modele.path)
        except Exception:
            pass

    resultats = preview_extraction(texte_pdf, modele)

    return render(
        request,
        "accounts/partials/_extraction_preview.html",
        {"resultats": resultats},
    )


@login_required
def config_extraction_test(request, pk):
    from apps.pdf_extraction.services import tester_extraction_pdf

    bailleur = get_object_or_404(Bailleur, pk=pk)

    if request.method != "POST":
        return redirect("gestion:config_extraction", pk=pk)

    pdf_file = request.FILES.get("pdf_test")
    if not pdf_file:
        return render(
            request,
            "accounts/partials/_extraction_test_result.html",
            {"erreur": "Veuillez sélectionner un fichier PDF."},
        )

    # Ecrire dans un fichier temporaire
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    try:
        with os.fdopen(tmp_fd, "wb") as tmp:
            for chunk in pdf_file.chunks():
                tmp.write(chunk)

        resultats = tester_extraction_pdf(tmp_path, bailleur)
    except Exception as e:
        return render(
            request,
            "accounts/partials/_extraction_test_result.html",
            {"erreur": f"Erreur lors de l'extraction : {e}"},
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return render(
        request,
        "accounts/partials/_extraction_test_result.html",
        {"resultats": resultats, "pdf_name": pdf_file.name},
    )


@login_required
def preview_masquage(request, pk):
    from apps.bdc.masquage_pdf import generer_pdf_masque
    from apps.bdc.models import BonDeCommande

    bailleur = get_object_or_404(Bailleur, pk=pk)

    bdc_pk = request.GET.get("bdc") or request.POST.get("bdc")
    if not bdc_pk:
        messages.error(request, "Veuillez sélectionner un BDC.")
        return redirect("gestion:config_bailleurs")

    bdc = get_object_or_404(BonDeCommande, pk=bdc_pk, bailleur=bailleur)
    pages = bailleur.pages_a_envoyer or None
    pdf_bytes = generer_pdf_masque(bdc, pages=pages)

    if not pdf_bytes:
        # Pas de zones configurees : servir le PDF original tel quel
        if bdc.pdf_original and bdc.pdf_original.name:
            try:
                bdc.pdf_original.open("rb")
                pdf_bytes = bdc.pdf_original.read()
                bdc.pdf_original.close()
            except Exception:
                messages.error(request, "Impossible de lire le PDF original.")
                return redirect("gestion:config_bailleurs")
        else:
            messages.error(request, "Aucun PDF disponible pour ce BDC.")
            return redirect("gestion:config_bailleurs")

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="masquage_preview_{bdc.numero_bdc}.pdf"'
    return response
