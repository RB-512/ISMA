"""
Tests unitaires de GDHParser — pdfplumber mocké.
"""
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from apps.pdf_extraction.gdh_parser import GDHParser

PDF_FICTIF = Path("/tmp/gdh_test.pdf")

# ─── Texte GDH simulé ─────────────────────────────────────────────────────────

TEXTE_GDH_COMPLET = """
GRAND DELTA HABITAT
Bon de Commande N° : 450098
N° Marché : MRC-2024-001
Date : 15/01/2024

Programme : Résidence Les Oliviers
Adresse : 12 Rue de la République
84000 AVIGNON
N° logement : B23
Type logement : T3
Étage : 2ème
Porte : G

Objet des travaux : Peinture complète après sinistre dégât des eaux
Délai d'exécution : 30/01/2024

Émetteur : Jean Dupont
Tél. : 04 90 12 34 56

Montant HT : 1 250,00 €
TVA : 125,00 €
Montant TTC : 1 375,00 €
"""

TEXTE_GDH_PAGE2 = """
BON D'INTERVENTION
Occupant : Marie Martin
Tél. occupant : 06 12 34 56 78
Email occupant : marie.martin@email.fr
"""

TABLE_PRESTATIONS = [
    [
        ["Désignation", "Quantité", "Unité", "Prix unitaire", "Montant"],
        ["M-P préparation et mise en peinture", "15", "m²", "11,19", "167,85"],
        ["Fourniture peinture Tollens", "2", "kg", "25,00", "50,00"],
        ["TOTAL HT", "", "", "", "217,85"],
    ]
]


def _mock_pdf(texte_p1: str, texte_p2: str = "", tables_p1: list | None = None):
    """Crée un mock pdfplumber avec pages simulées."""
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = texte_p1
    mock_page1.extract_tables.return_value = tables_p1 or []

    pages = [mock_page1]
    if texte_p2:
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = texte_p2
        pages.append(mock_page2)

    mock_pdf = MagicMock()
    mock_pdf.pages = pages
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    return mock_pdf


# ─── Tests de l'extraction complète ──────────────────────────────────────────

@patch("apps.pdf_extraction.gdh_parser.pdfplumber.open")
def test_extraire_retourne_dict_complet(mock_open):
    """extraire() retourne un dict avec toutes les clés attendues."""
    mock_open.return_value = _mock_pdf(TEXTE_GDH_COMPLET)
    parser = GDHParser(PDF_FICTIF)

    result = parser.extraire()

    cles_attendues = [
        "bailleur_code", "numero_bdc", "numero_marche", "date_emission",
        "programme_residence", "adresse", "code_postal", "ville",
        "logement_numero", "logement_type", "logement_etage", "logement_porte",
        "objet_travaux", "delai_execution",
        "occupant_nom", "occupant_telephone", "occupant_email",
        "emetteur_nom", "emetteur_telephone",
        "montant_ht", "montant_tva", "montant_ttc",
        "lignes_prestation",
    ]
    for cle in cles_attendues:
        assert cle in result, f"Clé manquante : {cle}"


@patch("apps.pdf_extraction.gdh_parser.pdfplumber.open")
def test_extraire_bailleur_code(mock_open):
    """Le bailleur_code est toujours 'GDH'."""
    mock_open.return_value = _mock_pdf(TEXTE_GDH_COMPLET)
    result = GDHParser(PDF_FICTIF).extraire()
    assert result["bailleur_code"] == "GDH"


@patch("apps.pdf_extraction.gdh_parser.pdfplumber.open")
def test_extraire_numero_bdc(mock_open):
    """Le numéro BDC est extrait correctement."""
    mock_open.return_value = _mock_pdf(TEXTE_GDH_COMPLET)
    result = GDHParser(PDF_FICTIF).extraire()
    assert result["numero_bdc"] == "450098"


@patch("apps.pdf_extraction.gdh_parser.pdfplumber.open")
def test_extraire_montants_decimal(mock_open):
    """Les montants sont des Decimal avec 2 décimales."""
    mock_open.return_value = _mock_pdf(TEXTE_GDH_COMPLET)
    result = GDHParser(PDF_FICTIF).extraire()
    assert result["montant_ht"] == Decimal("1250.00")
    assert result["montant_tva"] == Decimal("125.00")
    assert result["montant_ttc"] == Decimal("1375.00")


@patch("apps.pdf_extraction.gdh_parser.pdfplumber.open")
def test_extraire_lignes_prestation(mock_open):
    """Les lignes de prestation sont extraites depuis le tableau."""
    mock_open.return_value = _mock_pdf(TEXTE_GDH_COMPLET, tables_p1=TABLE_PRESTATIONS[0:1])
    result = GDHParser(PDF_FICTIF).extraire()

    lignes = result["lignes_prestation"]
    assert len(lignes) == 2  # 2 lignes de données (pas les totaux ni en-têtes)
    assert lignes[0]["designation"] == "M-P préparation et mise en peinture"
    assert lignes[0]["quantite"] == Decimal("15.00")
    assert lignes[0]["unite"] == "m²"
    assert lignes[0]["montant"] == Decimal("167.85")


@patch("apps.pdf_extraction.gdh_parser.pdfplumber.open")
def test_extraire_occupant_depuis_page2(mock_open):
    """Les infos occupant sont extraites depuis la page 2 si disponible."""
    mock_open.return_value = _mock_pdf(TEXTE_GDH_COMPLET, TEXTE_GDH_PAGE2)
    result = GDHParser(PDF_FICTIF).extraire()

    assert "Marie Martin" in result["occupant_nom"]
    assert "06" in result["occupant_telephone"]


@patch("apps.pdf_extraction.gdh_parser.pdfplumber.open")
def test_extraire_champ_absent_retourne_vide(mock_open):
    """Un champ absent retourne '' (pas d'exception)."""
    texte_minimal = "GRAND DELTA HABITAT\nBon de Commande N° : 450098"
    mock_open.return_value = _mock_pdf(texte_minimal)
    result = GDHParser(PDF_FICTIF).extraire()

    assert result["numero_marche"] == ""
    assert result["adresse"] == ""
    assert result["montant_ht"] is None
    assert result["lignes_prestation"] == []


@patch("apps.pdf_extraction.gdh_parser.pdfplumber.open")
def test_extraire_pdf_une_seule_page(mock_open):
    """Un PDF GDH à 1 page extrait les données sans erreur."""
    mock_open.return_value = _mock_pdf(TEXTE_GDH_COMPLET)  # une seule page
    result = GDHParser(PDF_FICTIF).extraire()

    assert result["bailleur_code"] == "GDH"
    assert result["numero_bdc"] == "450098"
    # Pas d'exception même si page 2 absente
