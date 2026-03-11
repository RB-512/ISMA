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
from django.http import HttpResponse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.views.generic import TemplateView

from apps.accounts.forms import CreerUtilisateurForm, ModifierRoleForm, ModifierUtilisateurForm
from apps.bdc.models import Bailleur, ChecklistItem, ConfigEmail, TransitionChoices

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
            response = HttpResponse()
            response["HX-Redirect"] = reverse("gestion:liste")
            return response
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


# ── Config bailleurs ──────────────────────────────────────────────────────


@login_required
def config_bailleurs(request):
    bailleurs = Bailleur.objects.all()

    return render(
        request,
        "accounts/config_bailleur.html",
        {
            "bailleurs": bailleurs,
            "config_email": ConfigEmail.get(),
        },
    )


@login_required
def config_email_save(request):
    if request.method != "POST":
        return redirect("gestion:config_bailleurs")
    config = ConfigEmail.get()
    config.sujet = request.POST.get("sujet", "").strip()
    config.corps = request.POST.get("corps", "").strip()
    config.save()
    messages.success(request, "Template email mis à jour.")
    return redirect("gestion:config_bailleurs")


@login_required

# ── Prévisualisation fiche chantier ──────────────────────────────────────


@login_required
def preview_fiche_chantier(request, pk):
    from apps.bdc.fiche_chantier import generer_fiche_chantier
    from apps.bdc.models import BonDeCommande

    bailleur = get_object_or_404(Bailleur, pk=pk)

    bdc_pk = request.GET.get("bdc") or request.POST.get("bdc")
    if not bdc_pk:
        messages.error(request, "Veuillez sélectionner un BDC.")
        return redirect("gestion:config_bailleurs")

    bdc = get_object_or_404(BonDeCommande, pk=bdc_pk, bailleur=bailleur)
    pdf_bytes = generer_fiche_chantier(bdc)

    if not pdf_bytes:
        messages.error(request, "Impossible de générer la fiche chantier.")
        return redirect("gestion:config_bailleurs")

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="fiche_chantier_{bdc.numero_bdc}.pdf"'
    return response
