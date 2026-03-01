"""
Notifications SMS pour les sous-traitants.
V1 : stub — le message est construit et loggé, pas d'envoi réel.
"""

import logging

from .models import BonDeCommande

logger = logging.getLogger(__name__)


def notifier_st_attribution(bdc: BonDeCommande) -> str:
    """
    Construit et logge le message SMS de notification au ST.
    Le message ne contient JAMAIS de prix (règle de confidentialité PRD).

    Returns:
        Le message SMS construit.
    """
    if not bdc.sous_traitant:
        return ""

    parties = [
        f"BDC n°{bdc.numero_bdc}",
        f"Adresse : {bdc.adresse_complete}",
    ]

    if bdc.occupation:
        parties.append(f"Logement : {bdc.get_occupation_display()}")

    if bdc.modalite_acces:
        parties.append(f"Accès : {bdc.modalite_acces}")

    if bdc.objet_travaux:
        parties.append(f"Travaux : {bdc.objet_travaux}")

    if bdc.delai_execution:
        parties.append(f"Délai : {bdc.delai_execution:%d/%m/%Y}")

    message = "\n".join(parties)

    telephone = bdc.sous_traitant.telephone or "N/A"
    logger.info(
        "SMS ST [%s] (%s) :\n%s",
        bdc.sous_traitant.nom,
        telephone,
        message,
    )

    return message
