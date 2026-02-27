"""
Module d'envoi de SMS aux sous-traitants.
À implémenter dans SPEC-003 (Attribution).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.bdc.models import BonDeCommande


def envoyer_sms_attribution(bdc: BonDeCommande) -> bool:
    """
    Envoie le SMS d'attribution au sous-traitant.

    Contenu : adresse, type de logement, vacant/occupé, modalité d'accès, RDV, objet des travaux.
    Les prix ne sont JAMAIS inclus.

    Returns:
        True si le SMS a été envoyé avec succès, False sinon.
    """
    # TODO: Implémenter l'envoi SMS — SPEC-003
    raise NotImplementedError("envoyer_sms_attribution() à implémenter dans SPEC-003")


def envoyer_sms_reattribution(bdc: BonDeCommande, ancien_st_telephone: str) -> bool:
    """
    Notifie l'ancien sous-traitant de l'annulation et le nouveau de l'attribution.

    Returns:
        True si tous les SMS ont été envoyés avec succès.
    """
    # TODO: Implémenter — SPEC-003
    raise NotImplementedError("envoyer_sms_reattribution() à implémenter dans SPEC-003")
