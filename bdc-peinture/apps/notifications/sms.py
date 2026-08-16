"""
Service d'envoi de SMS aux sous-traitants.
Les messages ne contiennent JAMAIS de prix.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .backends import get_sms_backend

if TYPE_CHECKING:
    from apps.bdc.models import BonDeCommande

logger = logging.getLogger(__name__)


def _composer_message_attribution(bdc: BonDeCommande) -> str:
    """Compose le message SMS d'attribution (sans prix)."""
    lignes = [
        f"BDC {bdc.numero_bdc}",
        f"Adresse : {bdc.adresse}, {bdc.ville}",
    ]
    if bdc.occupation:
        lignes.append(f"Logement : {bdc.get_occupation_display()}")
    if bdc.modalite_acces:
        lignes.append(f"Accès : {bdc.modalite_acces}")
    if bdc.objet_travaux:
        lignes.append(f"Travaux : {bdc.objet_travaux}")
    if bdc.delai_execution:
        lignes.append(f"Délai : {bdc.delai_execution.strftime('%d/%m/%Y')}")
    return "\n".join(lignes)


def envoyer_sms_attribution(bdc: BonDeCommande) -> bool:
    """
    Envoie le SMS d'attribution au sous-traitant.
    Ne bloque jamais l'attribution en cas d'erreur.

    Returns:
        True si le SMS a été envoyé avec succès, False sinon.
    """
    if not bdc.sous_traitant:
        logger.warning("SMS attribution : pas de ST pour BDC %s", bdc.numero_bdc)
        return False

    telephone = bdc.sous_traitant.telephone
    if not telephone:
        logger.warning("SMS attribution : ST %s sans téléphone", bdc.sous_traitant.nom)
        return False

    message = _composer_message_attribution(bdc)
    backend = get_sms_backend()
    return backend.send(telephone, message)


def envoyer_sms_annulation(bdc: BonDeCommande, telephone: str, reattribue: bool = False) -> bool:
    """
    Prévient un sous-traitant que le BDC ne lui est plus attribué.

    Le téléphone est passé en argument plutôt que lu sur le BDC : au moment de
    l'envoi, le sous-traitant a déjà été détaché du bon.

    Args:
        reattribue: True si le BDC part chez un autre ST, False s'il repart
            simplement en attente d'attribution.

    Returns:
        True si le SMS a été envoyé (ou s'il n'y avait pas de numéro).
    """
    if not telephone:
        logger.warning("SMS annulation : pas de téléphone pour BDC %s", bdc.numero_bdc)
        return True

    suite = " Ce BDC a été réattribué." if reattribue else ""
    message = f"BDC {bdc.numero_bdc} — Attribution annulée.{suite}"
    return get_sms_backend().send(telephone, message)


def envoyer_sms_reattribution(bdc: BonDeCommande, ancien_st_telephone: str) -> bool:
    """
    Notifie l'ancien ST de l'annulation et le nouveau de l'attribution.

    Returns:
        True si tous les SMS ont été envoyés avec succès.
    """
    succes = envoyer_sms_annulation(bdc, ancien_st_telephone, reattribue=True)

    # SMS d'attribution au nouveau ST
    if not envoyer_sms_attribution(bdc):
        succes = False

    return succes
