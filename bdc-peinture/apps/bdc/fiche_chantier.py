"""
Service de generation de la fiche chantier PDF pour le sous-traitant.

Genere un PDF propre a partir des donnees en base (pas de manipulation du PDF bailleur).
Utilise un template Django HTML converti en PDF via WeasyPrint.
"""

import logging

from django.template.loader import render_to_string
from weasyprint import HTML

from .models import BonDeCommande

logger = logging.getLogger(__name__)


def generer_fiche_chantier(bdc: BonDeCommande, commentaire: str = "") -> bytes | None:
    """
    Genere la fiche chantier PDF pour un BDC.

    Args:
        bdc: Le bon de commande.
        commentaire: Consignes du CDT pour le sous-traitant.

    Returns:
        bytes du PDF, ou None en cas d'erreur.
    """
    try:
        lignes = bdc.lignes.select_related().all()

        html_string = render_to_string("bdc/fiche_chantier_st.html", {
            "bdc": bdc,
            "lignes": lignes,
            "commentaire": commentaire,
        })

        pdf_bytes = HTML(string=html_string).write_pdf()
        logger.info("Fiche chantier generee pour BDC %s (%d bytes)", bdc.numero_bdc, len(pdf_bytes))
        return pdf_bytes
    except Exception:
        logger.warning("Echec generation fiche chantier BDC %s", bdc.numero_bdc, exc_info=True)
        return None
