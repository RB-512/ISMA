"""
Contrôle d'accès par groupe Django.
Utiliser @group_required("CDT") sur les vues fonctions,
GroupRequiredMixin sur les vues classes.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


def group_required(*group_names: str):
    """
    Décorateur qui vérifie que l'utilisateur appartient à l'un des groupes spécifiés.
    Requiert également que l'utilisateur soit authentifié.

    Usage:
        @group_required("CDT")
        def attribuer_bdc(request, bdc_id):
            ...

        @group_required("CDT", "Secretaire")
        def voir_dashboard(request):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.groups.filter(name__in=group_names).exists():
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


class GroupRequiredMixin(LoginRequiredMixin):
    """
    Mixin pour les vues classes. Vérifie l'appartenance à un groupe.

    Usage:
        class AttribuerBDCView(GroupRequiredMixin, UpdateView):
            group_required = "CDT"  # str ou list[str]
            ...
    """

    group_required: str | list[str] = ""

    def get_group_required(self) -> list[str]:
        if isinstance(self.group_required, str):
            return [self.group_required]
        return list(self.group_required)

    def dispatch(self, request, *args, **kwargs):
        # Vérifie l'authentification (via LoginRequiredMixin)
        response = super().dispatch(request, *args, **kwargs)

        # Si l'utilisateur n'est pas connecté, LoginRequiredMixin redirige déjà
        if not request.user.is_authenticated:
            return response

        # Vérifie le groupe
        groups = self.get_group_required()
        if groups and not request.user.groups.filter(name__in=groups).exists():
            raise PermissionDenied

        return response
