"""
Service d'alertes sur les délais d'exécution des BDC.
"""
from datetime import date, timedelta

from django.db.models import QuerySet

from apps.bdc.models import BonDeCommande, StatutChoices

STATUTS_ACTIFS = [StatutChoices.A_FAIRE, StatutChoices.EN_COURS]


def get_bdc_en_retard() -> QuerySet:
    """Retourne les BDC actifs dont le délai d'exécution est dépassé."""
    return BonDeCommande.objects.filter(
        statut__in=STATUTS_ACTIFS,
        delai_execution__lt=date.today(),
    ).select_related("bailleur", "sous_traitant")


def get_bdc_delai_proche(jours: int = 2) -> QuerySet:
    """Retourne les BDC actifs dont le délai est dans les N prochains jours (non dépassé)."""
    aujourd_hui = date.today()
    limite = aujourd_hui + timedelta(days=jours)
    return BonDeCommande.objects.filter(
        statut__in=STATUTS_ACTIFS,
        delai_execution__gte=aujourd_hui,
        delai_execution__lte=limite,
    ).select_related("bailleur", "sous_traitant")
