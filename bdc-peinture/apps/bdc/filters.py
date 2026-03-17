import django_filters

from .models import Bailleur, BonDeCommande, StatutChoices, TypeBonChoices


class BonDeCommandeFilter(django_filters.FilterSet):
    statut = django_filters.ChoiceFilter(
        choices=StatutChoices.choices,
        empty_label="Tous les statuts",
    )
    bailleur = django_filters.ModelChoiceFilter(
        queryset=Bailleur.objects.all(),
        empty_label="Tous les bailleurs",
    )
    ville = django_filters.CharFilter(
        field_name="ville",
        lookup_expr="icontains",
    )
    date_du = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__gte",
    )
    date_au = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__lte",
    )
    type_bon = django_filters.ChoiceFilter(
        choices=TypeBonChoices.choices,
        empty_label="Tous les types",
    )

    class Meta:
        model = BonDeCommande
        fields = ["statut", "bailleur", "ville", "date_du", "date_au", "type_bon"]
