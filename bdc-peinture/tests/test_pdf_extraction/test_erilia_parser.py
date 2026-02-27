"""
Tests unitaires de ERILIAParser — pdfplumber mocké.
"""
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

from apps.pdf_extraction.erilia_parser import ERILIAParser

PDF_FICTIF = Path("/tmp/erilia_test.pdf")

# ─── Texte ERILIA simulé ──────────────────────────────────────────────────────

TEXTE_ERILIA_COMPLET = """
ERILIA
Bon de Commande N° : E-2024-1056
N° Marché : MRC-ERILIA-2024
Date d'émission : 20/01/2024

Résidence : Les Pinèdes
Adresse des travaux : 5 Avenue du Mistral
13100 AIX-EN-PROVENCE
N° logement : A12
Type logement : T2
Étage : 3
Porte : D

Objet des travaux : Remise en état peinture — logement vacant
Délai d'exécution : 15/02/2024

Occupant : VACANT
Émetteur : Claire Bernard
Tél. : 04 42 56 78 90

Montant HT : 890,00 €
TVA : 89,00 €
Montant TTC : 979,00 €
"""

TABLE_PRESTATIONS_ERILIA = [
    ["Désignation", "Quantité", "Unité", "Prix unitaire", "Montant"],
    ["Peinture plafonds", "20", "m²", "8,50", "170,00"],
    ["Peinture murs", "60", "m²", "7,00", "420,00"],
    ["TOTAL HT", "", "", "", "590,00"],
]


def _mock_pdf(texte_p1: str, tables_p1: list | None = None):
    """Crée un mock pdfplumber avec une seule page."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = texte_p1
    mock_page.extract_tables.return_value = [tables_p1] if tables_p1 else []

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    return mock_pdf


# ─── Tests ────────────────────────────────────────────────────────────────────

@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_retourne_dict_complet(mock_open):
    """extraire() retourne un dict avec toutes les clés attendues."""
    mock_open.return_value = _mock_pdf(TEXTE_ERILIA_COMPLET)
    result = ERILIAParser(PDF_FICTIF).extraire()

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


@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_bailleur_code(mock_open):
    mock_open.return_value = _mock_pdf(TEXTE_ERILIA_COMPLET)
    assert ERILIAParser(PDF_FICTIF).extraire()["bailleur_code"] == "ERILIA"


@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_numero_bdc(mock_open):
    mock_open.return_value = _mock_pdf(TEXTE_ERILIA_COMPLET)
    assert ERILIAParser(PDF_FICTIF).extraire()["numero_bdc"] == "E-2024-1056"


@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_montants_decimal(mock_open):
    mock_open.return_value = _mock_pdf(TEXTE_ERILIA_COMPLET)
    result = ERILIAParser(PDF_FICTIF).extraire()
    assert result["montant_ht"] == Decimal("890.00")
    assert result["montant_tva"] == Decimal("89.00")
    assert result["montant_ttc"] == Decimal("979.00")


@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_emetteur(mock_open):
    mock_open.return_value = _mock_pdf(TEXTE_ERILIA_COMPLET)
    result = ERILIAParser(PDF_FICTIF).extraire()
    assert "Claire Bernard" in result["emetteur_nom"]


@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_lignes_prestation(mock_open):
    mock_open.return_value = _mock_pdf(TEXTE_ERILIA_COMPLET, TABLE_PRESTATIONS_ERILIA)
    result = ERILIAParser(PDF_FICTIF).extraire()

    lignes = result["lignes_prestation"]
    assert len(lignes) == 2  # 2 lignes de données
    assert lignes[0]["designation"] == "Peinture plafonds"
    assert lignes[0]["quantite"] == Decimal("20.00")


@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_champ_absent_retourne_vide(mock_open):
    texte_minimal = "ERILIA\nBon de Commande N° : E-2024-001"
    mock_open.return_value = _mock_pdf(texte_minimal)
    result = ERILIAParser(PDF_FICTIF).extraire()

    assert result["adresse"] == ""
    assert result["montant_ht"] is None
    assert result["lignes_prestation"] == []
