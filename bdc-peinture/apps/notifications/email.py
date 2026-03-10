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


def _obtenir_fiche_chantier(bdc: BonDeCommande, commentaire: str = "") -> bytes | None:
    """Génère la fiche chantier PDF à partir des données en base."""
    try:
        from apps.bdc.fiche_chantier import generer_fiche_chantier

        return generer_fiche_chantier(bdc, commentaire=commentaire)
    except Exception:
        logger.warning("Fiche chantier indisponible pour BDC %s", bdc.numero_bdc, exc_info=True)
    return None


def envoyer_email_attribution(bdc: BonDeCommande, commentaire: str = "") -> bool:
    """
    Envoie un email d'attribution au sous-traitant avec le PDF terrain en pièce jointe.
    Ne bloque jamais l'attribution en cas d'erreur.

    Args:
        bdc: Le bon de commande attribué.
        commentaire: Commentaire optionnel du CDT, ajouté dans le corps du mail.

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

    # Variables de substitution
    variables = {
        "numero_bdc": bdc.numero_bdc,
        "adresse": bdc.adresse or "",
        "ville": bdc.ville or "",
        "travaux": bdc.objet_travaux or "Non précisé",
        "delai": bdc.delai_execution.strftime("%d/%m/%Y") if bdc.delai_execution else "Non précisé",
        "commentaire": f"Commentaire :\n{commentaire}" if commentaire else "",
    }

    # Utiliser le template personnalisé si configuré
    from apps.bdc.models import ConfigEmail

    config = ConfigEmail.get()
    if config.sujet and config.corps:
        sujet = config.sujet.format_map(variables)
        corps = config.corps.format_map(variables)
    else:
        sujet = f"BDC {bdc.numero_bdc} — Attribution"
        corps = (
            f"Bonjour,\n\n"
            f"Le BDC n°{bdc.numero_bdc} vous a été attribué.\n\n"
            f"Adresse : {bdc.adresse}, {bdc.ville}\n"
            f"Travaux : {bdc.objet_travaux or 'Non précisé'}\n"
        )
        if bdc.delai_execution:
            corps += f"Délai : {bdc.delai_execution.strftime('%d/%m/%Y')}\n"
        if commentaire:
            corps += f"\nCommentaire :\n{commentaire}\n"
        corps += "\nCordialement,\nBDC Peinture"

    email = EmailMessage(
        subject=sujet,
        body=corps,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email_st],
    )

    pdf_contenu = _obtenir_fiche_chantier(bdc, commentaire=commentaire)
    if pdf_contenu:
        email.attach(f"fiche_chantier_{bdc.numero_bdc}.pdf", pdf_contenu, "application/pdf")
    else:
        email.body += (
            "\n\nNote : le document n'a pas pu être joint. Veuillez le récupérer auprès du conducteur de travaux."
        )

    email.send(fail_silently=False)
    logger.info("Email attribution envoyé à %s pour BDC %s", email_st, bdc.numero_bdc)
    return True


def envoyer_email_reattribution(bdc: BonDeCommande, ancien_st_email: str, commentaire: str = "") -> bool:
    """
    Envoie un email d'annulation à l'ancien ST et un email d'attribution au nouveau.

    Args:
        commentaire: Commentaire optionnel du CDT, ajouté dans l'email au nouveau ST.

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
    if not envoyer_email_attribution(bdc, commentaire=commentaire):
        succes = False

    return succes
