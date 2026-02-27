"""
Détecte automatiquement le type de PDF (GDH ou ERILIA) et retourne le parser approprié.
"""
from pathlib import Path

import pdfplumber

from .base import PDFParser

# ─── Marqueurs de détection ───────────────────────────────────────────────────

MARQUEUR_GDH = "GRAND DELTA HABITAT"
MARQUEUR_ERILIA = "ERILIA"


class PDFTypeInconnu(Exception):  # noqa: N818
    """Levée quand le type de PDF ne peut pas être déterminé."""


def detecter_parser(pdf_path: str | Path) -> PDFParser:
    """
    Analyse la première page du PDF et retourne le parser approprié.

    Args:
        pdf_path: Chemin vers le fichier PDF

    Returns:
        Instance du parser adapté au type de bailleur

    Raises:
        PDFTypeInconnu: Si le type de bailleur ne peut pas être détecté
    """
    # Import local pour éviter tout risque de circularité
    from .erilia_parser import ERILIAParser
    from .gdh_parser import GDHParser

    pdf_path = Path(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            raise PDFTypeInconnu(f"Le PDF '{pdf_path.name}' ne contient aucune page.")

        texte_page1 = pdf.pages[0].extract_text() or ""
        texte_upper = texte_page1.upper()

    if MARQUEUR_GDH in texte_upper:
        return GDHParser(pdf_path)

    if MARQUEUR_ERILIA in texte_upper:
        return ERILIAParser(pdf_path)

    raise PDFTypeInconnu(
        f"Type de PDF non reconnu pour '{pdf_path.name}'. "
        f"Formats supportés : GDH, ERILIA"
    )
