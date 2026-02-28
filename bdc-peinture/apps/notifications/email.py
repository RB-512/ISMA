"""
Service d'envoi d'emails aux sous-traitants.
Les emails ne contiennent JAMAIS de prix.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import EmailMessage

if TYPE_CHECKING:
    from apps.bdc.models import BonDeCommande

logger = logging.getLogger(__name__)


def _obtenir_pdf_terrain(bdc: BonDeCommande) -> bytes | None:
    """Retourne le contenu du PDF terrain, ou None si indisponible."""
    try:
        if bdc.pdf_terrain and bdc.pdf_terrain.name:
            bdc.pdf_terrain.open("rb")
            contenu = bdc.pdf_terrain.read()
            bdc.pdf_terrain.close()
            return contenu
    except Exception:
        logger.warning("PDF terrain indisponible pour BDC %s", bdc.numero_bdc, exc_info=True)
    return None


def envoyer_email_attribution(bdc: BonDeCommande) -> bool:
    """
    Envoie un email d'attribution au sous-traitant avec le PDF terrain en pièce jointe.
    Ne bloque jamais l'attribution en cas d'erreur.

    Returns:
        True si l'email a été envoyé avec succès, False sinon.
    """
    if not bdc.sous_traitant:
        logger.warning("Email attribution : pas de ST pour BDC %s", bdc.numero_bdc)
        return False

    email_st = bdc.sous_traitant.email
    if not email_st:
        logger.warning("Email attribution : ST %s sans email", bdc.sous_traitant.nom)
        return False

    sujet = f"BDC {bdc.numero_bdc} — Attribution"
    corps = (
        f"Bonjour,\n\n"
        f"Le BDC n°{bdc.numero_bdc} vous a été attribué.\n\n"
        f"Adresse : {bdc.adresse}, {bdc.ville}\n"
        f"Travaux : {bdc.objet_travaux or 'Non précisé'}\n"
    )
    if bdc.delai_execution:
        corps += f"Délai : {bdc.delai_execution.strftime('%d/%m/%Y')}\n"
    corps += "\nCordialement,\nBDC Peinture"

    email = EmailMessage(
        subject=sujet,
        body=corps,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email_st],
    )

    pdf_contenu = _obtenir_pdf_terrain(bdc)
    if pdf_contenu:
        email.attach(f"{bdc.numero_bdc}_terrain.pdf", pdf_contenu, "application/pdf")
    else:
        email.body += (
            "\n\nNote : le document terrain n'a pas pu être joint. "
            "Veuillez le récupérer auprès du conducteur de travaux."
        )

    email.send(fail_silently=False)
    logger.info("Email attribution envoyé à %s pour BDC %s", email_st, bdc.numero_bdc)
    return True


def envoyer_email_reattribution(bdc: BonDeCommande, ancien_st_email: str) -> bool:
    """
    Envoie un email d'annulation à l'ancien ST et un email d'attribution au nouveau.

    Returns:
        True si tous les emails ont été envoyés avec succès.
    """
    succes = True

    # Email d'annulation à l'ancien ST
    if ancien_st_email:
        email_annulation = EmailMessage(
            subject=f"BDC {bdc.numero_bdc} — Attribution annulée",
            body=(
                f"Bonjour,\n\n"
                f"L'attribution du BDC n°{bdc.numero_bdc} a été annulée.\n"
                f"Ce BDC a été réattribué à un autre sous-traitant.\n\n"
                f"Cordialement,\nBDC Peinture"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[ancien_st_email],
        )
        try:
            email_annulation.send(fail_silently=False)
        except Exception:
            logger.warning("Échec email annulation pour BDC %s", bdc.numero_bdc, exc_info=True)
            succes = False

    # Email d'attribution au nouveau ST
    if not envoyer_email_attribution(bdc):
        succes = False

    return succes
