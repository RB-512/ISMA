"""
Génération du PDF terrain (sans prix) pour les sous-traitants.

Stratégies :
- GDH : extraction de la page 2 du PDF original (bon d'intervention, nativement sans prix)
- ERILIA / défaut : génération HTML → PDF via WeasyPrint
"""

import logging

import fitz  # PyMuPDF
from django.core.files.base import ContentFile
from django.template.loader import render_to_string

from .models import BonDeCommande

logger = logging.getLogger(__name__)


class GenerationTerrainError(Exception):
    """Levée quand la génération du PDF terrain échoue."""


# ─── Stratégie GDH : extraction page 2 ──────────────────────────────────────


def _generer_terrain_gdh(bdc: BonDeCommande) -> bytes:
    """
    Extrait la page 2 du PDF original GDH (bon d'intervention sans prix).

    Returns:
        Le contenu binaire du PDF extrait (page 2 uniquement).

    Raises:
        GenerationTerrainError: Si le PDF n'a pas de page 2 ou est illisible.
    """
    if not bdc.pdf_original:
        raise GenerationTerrainError(f"BDC {bdc.numero_bdc} : pas de PDF original pour extraire la page 2.")

    try:
        with bdc.pdf_original.open("rb") as f:
            pdf_data = f.read()

        doc = fitz.open(stream=pdf_data, filetype="pdf")

        nb_pages = len(doc)
        if nb_pages < 2:
            doc.close()
            raise GenerationTerrainError(
                f"BDC {bdc.numero_bdc} : le PDF original n'a que {nb_pages} page(s), impossible d'extraire la page 2."
            )

        # Créer un nouveau PDF avec uniquement la page 2
        nouveau = fitz.open()
        nouveau.insert_pdf(doc, from_page=1, to_page=1)

        pdf_bytes = nouveau.tobytes()
        nouveau.close()
        doc.close()

        return pdf_bytes

    except GenerationTerrainError:
        raise
    except Exception as e:
        raise GenerationTerrainError(f"BDC {bdc.numero_bdc} : erreur lors de l'extraction page 2 — {e}") from e


# ─── Stratégie ERILIA / défaut : HTML → PDF ─────────────────────────────────


def _generer_terrain_erilia(bdc: BonDeCommande) -> bytes:
    """
    Génère un PDF terrain sans prix à partir des données du BDC via WeasyPrint.

    Returns:
        Le contenu binaire du PDF généré.
    """
    lignes = bdc.lignes_prestation.all()

    html_string = render_to_string(
        "bdc/terrain_erilia.html",
        {
            "bdc": bdc,
            "lignes": lignes,
        },
    )

    from weasyprint import HTML

    pdf_bytes = HTML(string=html_string).write_pdf()
    return pdf_bytes


# ─── Fonction principale ─────────────────────────────────────────────────────


def generer_pdf_terrain(bdc: BonDeCommande) -> BonDeCommande:
    """
    Génère le PDF terrain (sans prix) et le stocke sur le BDC.

    Dispatch selon le code bailleur :
    - GDH : extraction page 2 du PDF original
    - Autre (ERILIA, etc.) : génération HTML → PDF

    Returns:
        Le BDC avec le champ pdf_terrain mis à jour.
    """
    code = bdc.bailleur.code.upper() if bdc.bailleur else ""

    if code == "GDH":
        pdf_bytes = _generer_terrain_gdh(bdc)
    else:
        pdf_bytes = _generer_terrain_erilia(bdc)

    filename = f"{bdc.numero_bdc}_terrain.pdf"
    bdc.pdf_terrain.save(filename, ContentFile(pdf_bytes), save=True)

    return bdc
