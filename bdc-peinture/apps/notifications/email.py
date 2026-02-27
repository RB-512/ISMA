"""
Module d'envoi d'emails aux sous-traitants.
À implémenter dans SPEC-003 (Attribution).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.bdc.models import BonDeCommande


def envoyer_email_bdc_terrain(bdc: BonDeCommande) -> bool:
    """
    Envoie le BDC terrain PDF par email au sous-traitant.

    Returns:
        True si l'email a été envoyé avec succès.
    """
    # TODO: Implémenter — SPEC-003
    raise NotImplementedError("envoyer_email_bdc_terrain() à implémenter dans SPEC-003")
