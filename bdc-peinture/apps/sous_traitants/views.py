from django.views.generic import ListView

from .models import SousTraitant


class SousTraitantListView(ListView):
    model = SousTraitant
    template_name = "sous_traitants/list.html"
    context_object_name = "sous_traitants"
    queryset = SousTraitant.objects.filter(actif=True)
