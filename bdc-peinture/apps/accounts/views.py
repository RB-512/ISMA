"""
Vues d'authentification.
Le login/logout est géré par django-allauth, mais on fournit
des vues custom pour styler avec Tailwind.
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.crypto import get_random_string
from django.views.generic import TemplateView

from apps.accounts.forms import CreerUtilisateurForm, ModifierRoleForm, ModifierUtilisateurForm
from apps.bdc.models import Bailleur, ChecklistItem

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
    if request.method == "POST":
        libelle = request.POST.get("libelle", "").strip()
        if libelle:
            max_ordre = ChecklistItem.objects.aggregate(m=models.Max("ordre"))["m"] or 0
            ChecklistItem.objects.create(libelle=libelle, ordre=max_ordre + 1)
            messages.success(request, f"Point de contrôle « {libelle} » ajouté.")
        else:
            messages.error(request, "Le libellé ne peut pas être vide.")
        return redirect("gestion:checklist_liste")
    items = ChecklistItem.objects.order_by("ordre")
    return render(request, "accounts/checklist.html", {"items": items})


@login_required
def checklist_modifier(request, pk):
    item = get_object_or_404(ChecklistItem, pk=pk)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "toggle":
            item.actif = not item.actif
            item.save()
            etat = "activé" if item.actif else "désactivé"
            messages.success(request, f"« {item.libelle} » {etat}.")
            return redirect("gestion:checklist_liste")
        libelle = request.POST.get("libelle", "").strip()
        ordre = request.POST.get("ordre", "").strip()
        if libelle:
            item.libelle = libelle
        if ordre.isdigit():
            item.ordre = int(ordre)
        item.save()
        messages.success(request, f"Point de contrôle « {item.libelle} » mis à jour.")
        return redirect("gestion:checklist_liste")
    return render(request, "accounts/partials/_modifier_checklist.html", {"item": item})


@login_required
def checklist_supprimer(request, pk):
    item = get_object_or_404(ChecklistItem, pk=pk)
    if request.method == "POST":
        libelle = item.libelle
        item.delete()
        messages.success(request, f"Point de contrôle « {libelle} » supprimé.")
    return redirect("gestion:checklist_liste")


# ── Config masquage PDF par bailleur ─────────────────────────────────────


@login_required
def config_bailleurs(request):
    from apps.bdc.masquage_pdf import CHAMPS_DISPONIBLES

    bailleurs = Bailleur.objects.all()

    if request.method == "POST":
        bailleur_id = request.POST.get("bailleur_id")
        bailleur = get_object_or_404(Bailleur, pk=bailleur_id)
        champs = request.POST.getlist("champs_masques")
        bailleur.champs_masques = champs
        bailleur.save(update_fields=["champs_masques"])
        messages.success(request, f"Configuration de masquage mise à jour pour {bailleur.nom}.")
        if request.headers.get("HX-Request"):
            return render(
                request,
                "accounts/partials/_config_bailleur_form.html",
                {
                    "bailleur": bailleur,
                    "champs_disponibles": CHAMPS_DISPONIBLES,
                },
            )
        return redirect("gestion:config_bailleurs")

    return render(
        request,
        "accounts/config_bailleur.html",
        {
            "bailleurs": bailleurs,
            "champs_disponibles": CHAMPS_DISPONIBLES,
        },
    )


@login_required
def config_bailleur_form(request, pk):
    from apps.bdc.masquage_pdf import CHAMPS_DISPONIBLES

    bailleur = get_object_or_404(Bailleur, pk=pk)
    return render(
        request,
        "accounts/partials/_config_bailleur_form.html",
        {
            "bailleur": bailleur,
            "champs_disponibles": CHAMPS_DISPONIBLES,
        },
    )
