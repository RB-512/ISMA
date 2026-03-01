"""
Vues d'authentification.
Le login/logout est géré par django-allauth, mais on fournit
des vues custom pour styler avec Tailwind.
"""
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView

from apps.accounts.decorators import group_required
from apps.accounts.forms import CreerUtilisateurForm, ModifierRoleForm

User = get_user_model()


class HomeRedirectView(TemplateView):
    """Redirige vers le dashboard BDC."""

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("bdc:index")
        return redirect("account_login")


@group_required("CDT")
def liste_utilisateurs(request):
    utilisateurs = User.objects.prefetch_related("groups").order_by("last_name", "first_name")
    form_creer = CreerUtilisateurForm()
    return render(request, "accounts/utilisateurs.html", {
        "utilisateurs": utilisateurs,
        "form_creer": form_creer,
        "is_cdt": True,
    })


@group_required("CDT")
def creer_utilisateur(request):
    if request.method != "POST":
        return redirect("gestion:liste")
    form = CreerUtilisateurForm(request.POST)
    if form.is_valid():
        user = form.save()
        messages.success(request, f"Compte créé pour {user.get_full_name() or user.username}.")
        return redirect("gestion:liste")
    utilisateurs = User.objects.prefetch_related("groups").order_by("last_name", "first_name")
    return render(request, "accounts/utilisateurs.html", {
        "utilisateurs": utilisateurs,
        "form_creer": form,
        "is_cdt": True,
    })


@group_required("CDT")
def modifier_role(request, pk):
    utilisateur = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = ModifierRoleForm(request.POST)
        if form.is_valid():
            group = Group.objects.get(name=form.cleaned_data["role"])
            utilisateur.groups.set([group])
            messages.success(request, f"Rôle mis à jour pour {utilisateur.get_full_name() or utilisateur.username}.")
    return redirect("gestion:liste")


@group_required("CDT")
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
