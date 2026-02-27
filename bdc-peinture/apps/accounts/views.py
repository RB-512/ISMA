"""
Vues d'authentification.
Le login/logout est géré par django-allauth, mais on fournit
des vues custom pour styler avec Tailwind.
"""
from django.shortcuts import redirect
from django.views.generic import TemplateView


class HomeRedirectView(TemplateView):
    """Redirige vers le dashboard BDC."""

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("bdc:index")
        return redirect("account_login")
