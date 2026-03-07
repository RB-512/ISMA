"""
Generation du PDF terrain (sans prix) pour les sous-traitants.

Strategie unique : generation PyMuPDF depuis les donnees en base.
Fonctionne pour tous les bailleurs sans configuration specifique.
"""

import logging

import fitz  # PyMuPDF
from django.core.files.base import ContentFile

from .models import BonDeCommande

logger = logging.getLogger(__name__)


class GenerationTerrainError(Exception):
    """Levee quand la generation du PDF terrain echoue."""


# --- Constantes mise en page ------------------------------------------------

_MARGE_G = 50       # marge gauche
_MARGE_D = 50       # marge droite
_Y_START = 60       # debut du contenu
_INTERLIGNE = 16    # espacement entre lignes
_SECTION_GAP = 12   # espace supplementaire entre sections


def _draw_section_title(page: fitz.Page, y: float, titre: str, width: float) -> float:
    """Dessine un titre de section avec une ligne de separation. Retourne le nouveau y."""
    y += _SECTION_GAP
    page.insert_text((_MARGE_G, y), titre.upper(), fontsize=9, fontname="helv", color=(0.33, 0.33, 0.33))
    y += 4
    page.draw_line(
        fitz.Point(_MARGE_G, y),
        fitz.Point(width - _MARGE_D, y),
        color=(0.8, 0.8, 0.8),
        width=0.5,
    )
    y += _INTERLIGNE
    return y


def _draw_field(page: fitz.Page, y: float, label: str, valeur: str) -> float:
    """Dessine un champ label: valeur. Retourne le nouveau y."""
    if not valeur:
        return y
    page.insert_text((_MARGE_G, y), f"{label} : ", fontsize=10, fontname="helv", color=(0.4, 0.4, 0.4))
    # Calculer la position apres le label
    label_width = fitz.get_text_length(f"{label} : ", fontsize=10, fontname="helv")
    page.insert_text((_MARGE_G + label_width, y), valeur, fontsize=10, fontname="helv")
    y += _INTERLIGNE
    return y


def _generer_pdf_terrain_pymupdf(bdc: BonDeCommande) -> bytes:
    """
    Genere un PDF terrain (sans prix) depuis les donnees en base.

    Contenu :
    - En-tete : nom bailleur + numero BDC
    - Localisation : adresse, residence, logement, occupation, acces
    - Travaux : objet, delai
    - Contact occupant : nom, telephone
    - Prestations : designation, quantite, unite (SANS PRIX)
    - Mention DOCUMENT TERRAIN --- SANS PRIX
    """
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    width = page.rect.width
    y = _Y_START

    # -- En-tete ---------------------------------------------------------------
    bailleur_nom = bdc.bailleur.nom.upper() if bdc.bailleur else "BAILLEUR"
    page.insert_text((_MARGE_G, y), bailleur_nom, fontsize=14, fontname="helv", color=(0.1, 0.1, 0.1))
    y += 22
    page.insert_text((_MARGE_G, y), f"BDC Terrain N\u00b0 {bdc.numero_bdc}", fontsize=12, fontname="helv")
    y += 8
    if bdc.numero_marche:
        page.insert_text(
            (_MARGE_G, y + _INTERLIGNE),
            f"March\u00e9 {bdc.numero_marche}",
            fontsize=9,
            fontname="helv",
            color=(0.5, 0.5, 0.5),
        )
        y += _INTERLIGNE
    # Ligne de separation en-tete
    y += 8
    page.draw_line(fitz.Point(_MARGE_G, y), fitz.Point(width - _MARGE_D, y), color=(0.2, 0.2, 0.2), width=1)
    y += _INTERLIGNE

    # -- Localisation ----------------------------------------------------------
    y = _draw_section_title(page, y, "Localisation", width)
    y = _draw_field(page, y, "Adresse", bdc.adresse_complete)
    y = _draw_field(page, y, "R\u00e9sidence", bdc.programme_residence)
    if bdc.logement_numero:
        logement = bdc.logement_type or ""
        if bdc.logement_numero:
            logement += f" n\u00b0{bdc.logement_numero}"
        if bdc.logement_etage:
            logement += f" \u2014 \u00c9tage {bdc.logement_etage}"
        if bdc.logement_porte:
            logement += f" / Porte {bdc.logement_porte}"
        y = _draw_field(page, y, "Logement", logement.strip())
    if bdc.occupation:
        y = _draw_field(page, y, "Occupation", bdc.get_occupation_display())
    y = _draw_field(page, y, "Acc\u00e8s", bdc.modalite_acces)

    # -- Travaux ---------------------------------------------------------------
    y = _draw_section_title(page, y, "Travaux", width)
    y = _draw_field(page, y, "Objet", bdc.objet_travaux)
    if bdc.delai_execution:
        y = _draw_field(page, y, "D\u00e9lai", bdc.delai_execution.strftime("%d/%m/%Y"))

    # -- Contact occupant ------------------------------------------------------
    if bdc.occupant_nom or bdc.occupant_telephone:
        y = _draw_section_title(page, y, "Contact occupant", width)
        y = _draw_field(page, y, "Nom", bdc.occupant_nom)
        y = _draw_field(page, y, "T\u00e9l\u00e9phone", bdc.occupant_telephone)

    # -- Prestations (SANS PRIX) -----------------------------------------------
    lignes = list(bdc.lignes_prestation.all().order_by("ordre"))
    if lignes:
        y = _draw_section_title(page, y, "Prestations", width)
        # En-tete tableau
        col_x = [_MARGE_G, width - _MARGE_D - 100, width - _MARGE_D - 40]
        page.insert_text((col_x[0], y), "D\u00e9signation", fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
        page.insert_text((col_x[1], y), "Qt\u00e9", fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
        page.insert_text((col_x[2], y), "Unit\u00e9", fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
        y += 4
        page.draw_line(
            fitz.Point(_MARGE_G, y), fitz.Point(width - _MARGE_D, y), color=(0.85, 0.85, 0.85), width=0.5
        )
        y += _INTERLIGNE - 2

        for ligne in lignes:
            designation = str(ligne.designation)
            # Tronquer si trop long pour une ligne
            max_len = 60
            if len(designation) > max_len:
                designation = designation[:max_len - 3] + "..."
            page.insert_text((col_x[0], y), designation, fontsize=9, fontname="helv")
            page.insert_text((col_x[1], y), str(ligne.quantite.normalize()), fontsize=9, fontname="helv")
            page.insert_text((col_x[2], y), ligne.unite or "", fontsize=9, fontname="helv")
            y += _INTERLIGNE

    # -- Mention SANS PRIX -----------------------------------------------------
    y += _SECTION_GAP * 2
    mention = "DOCUMENT TERRAIN \u2014 SANS PRIX"
    mention_width = fitz.get_text_length(mention, fontsize=9, fontname="helv")
    x_center = (width - mention_width) / 2
    page.insert_text((x_center, y), mention, fontsize=9, fontname="helv", color=(0.8, 0, 0))

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def generer_pdf_terrain(bdc: BonDeCommande) -> BonDeCommande:
    """
    Genere le PDF terrain (sans prix) et le stocke sur le BDC.

    Processus unique pour tous les bailleurs : generation PyMuPDF
    depuis les donnees en base.

    Returns:
        Le BDC avec le champ pdf_terrain mis a jour.
    """
    pdf_bytes = _generer_pdf_terrain_pymupdf(bdc)
    filename = f"{bdc.numero_bdc}_terrain.pdf"
    bdc.pdf_terrain.save(filename, ContentFile(pdf_bytes), save=True)
    return bdc
