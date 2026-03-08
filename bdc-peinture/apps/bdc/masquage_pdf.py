"""
Service de masquage PDF : applique des zones de masquage (rectangles blancs)
definies dans la config du bailleur sur le PDF original du BDC.

Utilise PyMuPDF (fitz) : add_redact_annot() + apply_redactions().
"""

import logging

import fitz  # PyMuPDF

from .models import BonDeCommande

logger = logging.getLogger(__name__)


def generer_pdf_masque(bdc: BonDeCommande, pages: list[int] | None = None) -> bytes | None:
    """
    Ouvre le PDF original, applique les zones de masquage du bailleur,
    puis filtre les pages si demande.

    Args:
        bdc: Le bon de commande dont on masque le PDF.
        pages: Liste de numeros de page (1-indexes) a inclure. None ou [] = toutes.

    Returns:
        bytes du PDF masque, ou None si pas de PDF ou pas de zones configurees.
    """
    if not bdc.pdf_original or not bdc.pdf_original.name:
        logger.warning("Pas de PDF original pour BDC %s", bdc.numero_bdc)
        return None

    zones = bdc.bailleur.zones_masquage if bdc.bailleur else []
    if not zones:
        logger.info("Aucune zone de masquage pour BDC %s (bailleur %s)", bdc.numero_bdc, bdc.bailleur)
        return None

    try:
        bdc.pdf_original.open("rb")
        pdf_bytes = bdc.pdf_original.read()
        bdc.pdf_original.close()
    except Exception:
        logger.warning("Impossible de lire le PDF original pour BDC %s", bdc.numero_bdc, exc_info=True)
        return None

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # Appliquer les zones de masquage page par page
    pages_modifiees = set()
    for zone in zones:
        page_num = zone.get("page", 1) - 1  # 1-indexed -> 0-indexed
        if page_num < 0 or page_num >= len(doc):
            continue
        page = doc[page_num]
        rect = fitz.Rect(zone["x"], zone["y"], zone["x"] + zone["w"], zone["y"] + zone["h"])
        page.add_redact_annot(rect, fill=(1, 1, 1))
        pages_modifiees.add(page_num)

    for page_num in pages_modifiees:
        doc[page_num].apply_redactions()

    logger.info("PDF masque genere pour BDC %s : %d zone(s) appliquee(s)", bdc.numero_bdc, len(zones))

    # Filtrer les pages si demande
    if pages:
        doc_filtre = fitz.open()
        for p in pages:
            if 1 <= p <= len(doc):
                doc_filtre.insert_pdf(doc, from_page=p - 1, to_page=p - 1)
        doc.close()
        doc = doc_filtre

    result = doc.tobytes()
    doc.close()
    return result
