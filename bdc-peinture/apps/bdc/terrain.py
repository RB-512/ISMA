"""
Generation du PDF terrain (sans prix) pour les sous-traitants.

Strategie unique : generation PyMuPDF depuis les donnees en base.
Fonctionne pour tous les bailleurs sans configuration specifique.
"""

import logging
import textwrap

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
_INTERLIGNE = 14    # espacement entre lignes
_SECTION_GAP = 10   # espace supplementaire entre sections
_PAGE_W = 595       # largeur A4
_PAGE_H = 842       # hauteur A4

# --- Coordonnees entreprise emettrice (en dur pour l'instant) ---------------

_ENTREPRISE_NOM = "ISMA Peinture"
_ENTREPRISE_TEL = "04 90 XX XX XX"
_ENTREPRISE_EMAIL = "contact@isma-peinture.fr"


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
    label_width = fitz.get_text_length(f"{label} : ", fontsize=10, fontname="helv")
    page.insert_text((_MARGE_G + label_width, y), valeur, fontsize=10, fontname="helv")
    y += _INTERLIGNE
    return y


def _draw_text_wrapped(page: fitz.Page, x: float, y: float, text: str, max_width: float, fontsize=9) -> float:
    """Dessine du texte avec retour a la ligne automatique. Retourne le nouveau y."""
    # Estimer le nombre de caracteres par ligne
    char_width = fitz.get_text_length("m", fontsize=fontsize, fontname="helv")
    max_chars = int(max_width / char_width)
    if max_chars < 10:
        max_chars = 10
    lines = textwrap.wrap(text, width=max_chars)
    for line in lines:
        page.insert_text((x, y), line, fontsize=fontsize, fontname="helv")
        y += _INTERLIGNE
    return y


def _generer_pdf_terrain_pymupdf(bdc: BonDeCommande) -> bytes:
    """
    Genere un PDF terrain (sans prix) depuis les donnees en base.

    Contenu :
    - En-tete gauche : nom bailleur + numero BDC
    - En-tete droite : coordonnees entreprise emettrice + emplacement logo
    - Localisation, travaux, contact occupant
    - Prestations : designation complete, quantite, unite (SANS PRIX)
    - Zone commentaire (vide, a remplir)
    - Zone signature pour accuser bonne realisation
    - Mention DOCUMENT TERRAIN — SANS PRIX
    """
    doc = fitz.open()
    page = doc.new_page(width=_PAGE_W, height=_PAGE_H)
    width = page.rect.width
    y = _Y_START

    # == En-tete gauche : bailleur =============================================
    bailleur_nom = bdc.bailleur.nom.upper() if bdc.bailleur else "BAILLEUR"
    page.insert_text((_MARGE_G, y), bailleur_nom, fontsize=21, fontname="helv", color=(0.1, 0.1, 0.1))

    # == En-tete droite : entreprise emettrice =================================
    right_x = width - _MARGE_D - 120
    # Emplacement logo en haut (rectangle pointille centre)
    logo_w, logo_h = 60, 40
    logo_cx = right_x + 60  # centre horizontal du bloc
    logo_rect = fitz.Rect(logo_cx - logo_w / 2, y - 15, logo_cx + logo_w / 2, y - 15 + logo_h)
    page.draw_rect(logo_rect, color=(0.7, 0.7, 0.7), width=0.5, dashes="[3] 0")
    page.insert_text((logo_cx - 10, y + 8), "LOGO", fontsize=7, fontname="helv", color=(0.7, 0.7, 0.7))
    # Coordonnees entreprise en dessous du logo
    info_y = y - 15 + logo_h + 6
    nom_w = fitz.get_text_length(_ENTREPRISE_NOM, fontsize=9, fontname="helv")
    page.insert_text((logo_cx - nom_w / 2, info_y), _ENTREPRISE_NOM, fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))
    info_y += 12
    tel_w = fitz.get_text_length(_ENTREPRISE_TEL, fontsize=8, fontname="helv")
    page.insert_text((logo_cx - tel_w / 2, info_y), _ENTREPRISE_TEL, fontsize=8, fontname="helv", color=(0.4, 0.4, 0.4))
    info_y += 10
    email_w = fitz.get_text_length(_ENTREPRISE_EMAIL, fontsize=8, fontname="helv")
    page.insert_text((logo_cx - email_w / 2, info_y), _ENTREPRISE_EMAIL, fontsize=8, fontname="helv", color=(0.4, 0.4, 0.4))

    y += 22
    page.insert_text((_MARGE_G, y), f"BON DE COMMANDE TERRAIN N\u00b0 {bdc.numero_bdc}", fontsize=14, fontname="helv")
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
    # Ligne de separation en-tete (sous le bloc entreprise)
    y = max(y + 8, info_y + 10)
    page.draw_line(fitz.Point(_MARGE_G, y), fitz.Point(width - _MARGE_D, y), color=(0.2, 0.2, 0.2), width=1)
    y += _INTERLIGNE

    # == Localisation ==========================================================
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

    # == Travaux ===============================================================
    y = _draw_section_title(page, y, "Travaux", width)
    y = _draw_field(page, y, "Objet", bdc.objet_travaux)
    if bdc.delai_execution:
        y = _draw_field(page, y, "D\u00e9lai", bdc.delai_execution.strftime("%d/%m/%Y"))

    # == Contact occupant ======================================================
    if bdc.occupant_nom or bdc.occupant_telephone:
        y = _draw_section_title(page, y, "Contact occupant", width)
        y = _draw_field(page, y, "Nom", bdc.occupant_nom)
        y = _draw_field(page, y, "T\u00e9l\u00e9phone", bdc.occupant_telephone)

    # == Prestations (SANS PRIX) ===============================================
    lignes = list(bdc.lignes_prestation.all().order_by("ordre"))
    if lignes:
        y = _draw_section_title(page, y, "Prestations", width)
        # En-tete tableau
        col_qte_x = width - _MARGE_D - 100
        col_unite_x = width - _MARGE_D - 40
        max_desig_width = col_qte_x - _MARGE_G - 10  # largeur dispo pour designation
        page.insert_text((_MARGE_G, y), "D\u00e9signation", fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
        page.insert_text((col_qte_x, y), "Qt\u00e9", fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
        page.insert_text((col_unite_x, y), "Unit\u00e9", fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
        y += 4
        page.draw_line(
            fitz.Point(_MARGE_G, y), fitz.Point(width - _MARGE_D, y), color=(0.85, 0.85, 0.85), width=0.5
        )
        y += _INTERLIGNE - 2

        for ligne in lignes:
            designation = str(ligne.designation)
            qte = str(ligne.quantite.normalize())
            unite = ligne.unite or ""
            # Designation avec retour a la ligne
            y_before = y
            y = _draw_text_wrapped(page, _MARGE_G, y, designation, max_desig_width, fontsize=9)
            # Quantite et unite sur la premiere ligne de la designation
            page.insert_text((col_qte_x, y_before), qte, fontsize=9, fontname="helv")
            page.insert_text((col_unite_x, y_before), unite, fontsize=9, fontname="helv")
            y += 2  # petit espace entre prestations

    # == Commentaire (emplacement vide) ========================================
    y = _draw_section_title(page, y, "Commentaire", width)
    comment_rect = fitz.Rect(_MARGE_G, y, width - _MARGE_D, y + 50)
    page.draw_rect(comment_rect, color=(0.8, 0.8, 0.8), width=0.5)
    y += 60

    # == Signature =============================================================
    y = _draw_section_title(page, y, "Signature — Bonne r\u00e9alisation des travaux", width)
    # Encadre signature avec date + nom + signature
    sig_rect = fitz.Rect(_MARGE_G, y, width - _MARGE_D, y + 60)
    page.draw_rect(sig_rect, color=(0.8, 0.8, 0.8), width=0.5)
    sig_y = y + 14
    page.insert_text((_MARGE_G + 10, sig_y), "Date :", fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
    page.draw_line(fitz.Point(_MARGE_G + 45, sig_y + 2), fitz.Point(_MARGE_G + 180, sig_y + 2), color=(0.8, 0.8, 0.8), width=0.5)
    sig_y += 18
    page.insert_text((_MARGE_G + 10, sig_y), "Nom :", fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
    page.draw_line(fitz.Point(_MARGE_G + 45, sig_y + 2), fitz.Point(_MARGE_G + 180, sig_y + 2), color=(0.8, 0.8, 0.8), width=0.5)
    # Zone signature a droite
    mid_x = width / 2
    page.insert_text((mid_x + 10, y + 14), "Signature :", fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
    y += 70

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
