"""
Services d'extraction PDF : extraction texte, preview, test a blanc.
"""

from pathlib import Path

import pdfplumber

from .template_parser import CHAMPS_STANDARD, TemplateParser, extraire_valeur_par_label


def extraire_texte_pdf(pdf_path: str | Path) -> str:
    """Extrait le texte integral d'un PDF (toutes les pages)."""
    pdf_path = Path(pdf_path)
    pages_texte = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            texte = page.extract_text() or ""
            pages_texte.append(texte)
    return "\n".join(pages_texte)


def preview_extraction(texte_pdf: str, modele_extraction: dict) -> list[dict]:
    """
    Applique les labels configures sur un texte PDF et retourne les resultats.

    Returns:
        Liste de dicts {champ, label, valeur} pour chaque champ configure.
    """
    resultats = []
    for champ in CHAMPS_STANDARD:
        config = modele_extraction.get(champ, {})
        label = config.get("label", "") if isinstance(config, dict) else ""
        if not label:
            continue
        valeur = extraire_valeur_par_label(texte_pdf, label)
        resultats.append(
            {
                "champ": champ,
                "label": label,
                "valeur": valeur or "(non trouvé)",
            }
        )
    return resultats


def tester_extraction_pdf(pdf_path: str | Path, bailleur) -> list[dict]:
    """
    Test a blanc : applique le modele d'extraction du bailleur sur un PDF.
    Retourne les resultats sans rien creer en base.
    """
    parser = TemplateParser(pdf_path, bailleur)
    donnees = parser.extraire()

    resultats = []
    modele = bailleur.modele_extraction or {}
    for champ in CHAMPS_STANDARD:
        config = modele.get(champ, {})
        label = config.get("label", "") if isinstance(config, dict) else ""
        if not label:
            continue
        valeur = donnees.get(champ)
        if valeur is None or valeur == "":
            valeur_str = "(non trouvé)"
        else:
            valeur_str = str(valeur)
        resultats.append(
            {
                "champ": champ,
                "label": label,
                "valeur": valeur_str,
            }
        )
    return resultats
