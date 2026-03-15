"""
Service de generation de la fiche chantier PDF pour le sous-traitant.

Genere un PDF propre a partir des donnees en base (pas de manipulation du PDF bailleur).
Utilise un template Django HTML converti en PDF via WeasyPrint (prod) ou xhtml2pdf (dev/Windows).
"""

import io
import logging

from django.template.loader import render_to_string

from .models import BonDeCommande

logger = logging.getLogger(__name__)


def _html_to_pdf_weasyprint(html_string: str) -> bytes:
    from weasyprint import HTML

    return HTML(string=html_string).write_pdf()


def _html_to_pdf_xhtml2pdf(html_string: str) -> bytes:
    from xhtml2pdf import pisa

    buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_string, dest=buffer)
    if pisa_status.err:
        raise RuntimeError(f"xhtml2pdf error: {pisa_status.err}")
    return buffer.getvalue()


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
        lignes = bdc.lignes_prestation.all()

        html_string = render_to_string("bdc/fiche_chantier_st.html", {
            "bdc": bdc,
            "lignes": lignes,
            "commentaire": commentaire,
        })

        try:
            pdf_bytes = _html_to_pdf_weasyprint(html_string)
        except (OSError, ImportError):
            logger.info("WeasyPrint indisponible, fallback xhtml2pdf pour BDC %s", bdc.numero_bdc)
            pdf_bytes = _html_to_pdf_xhtml2pdf(html_string)

        logger.info("Fiche chantier generee pour BDC %s (%d bytes)", bdc.numero_bdc, len(pdf_bytes))
        return pdf_bytes
    except Exception:
        logger.warning("Echec generation fiche chantier BDC %s", bdc.numero_bdc, exc_info=True)
        return None
