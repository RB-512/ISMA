"""
Tests unitaires de GDHParser — pdfplumber mocké avec texte au format réel.
"""
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

from apps.pdf_extraction.gdh_parser import GDHParser

PDF_FICTIF = Path("/tmp/gdh_test.pdf")

# ─── Texte GDH au format réel pdfplumber ─────────────────────────────────────

TEXTE_GDH_PAGE1 = (
    "Bon de commande\n"
    "reprise peinture SDB\n"
    "suite trx faience\n"
    "n° 450056 du 09/02/2026\n"
    "GRAND DELTA HABITAT GROUPEMENT NOUVOSOL / B-Y PEINTURE\n"
    "Secteur Gard Rhodanien\n"
    "10 rue Althen\n"
    "Agence des Sources\n"
    "84000 AVIGNON\n"
    "Emetteur : Joseph LONEGRO Mail : contact@nouvosol.fr\n"
    "Tél : 0637577004 Tél : 0490893893\n"
    "Prestation à réaliser pour le 20/02/2026\n"
    "Marché n° 026322-CPP-003\n"
    "Prestation parties privatives\n"
    "Habitation n° 000756 de type Type 3, Etage 1, porte 107 "
    "Occupant actuel : MUSELLA CHRISTIANE (074143/35)\n"
    "VERONESE BAT 1 ENT 1 (0023-1-1) Portable : 0658714328\n"
    "3 Rue Francois 1er Mail : christianemusella@gmail.com\n"
    "84000 AVIGNON\n"
    "Total HT 167.85 €\n"
    "Total TVA 10.00 % 16.79 €\n"
    "Total TTC 184.64 €\n"
)

TEXTE_GDH_PAGE2 = (
    "Bon d'intervention\n"
    "reprise peinture SDB\n"
    "n° 450056 du 09/02/2026\n"
    "GRAND DELTA HABITAT\n"
    "Personne à contacter : Joseph LONEGRO\n"
    "Habitation n° 000756, porte 107 "
    "Occupant actuel : MUSELLA CHRISTIANE (074143/35)\n"
    "VERONESE BAT 1 ENT 1 (0023-1-1) Portable : 0658714328\n"
    "3 Rue Francois 1er Mail : christianemusella@gmail.com\n"
    "84000 AVIGNON\n"
)

TABLE_P1 = [
    ["Prestation parties privatives", ""],
    [
        (
            "Habitation n° 000756 de type Type 3, Etage 1, porte 107\n"
            "VERONESE BAT 1 ENT 1 (0023-1-1)\n"
            "3 Rue Francois 1er\n"
            "84000 AVIGNON"
        ),
        (
            "Occupant actuel : MUSELLA CHRISTIANE (074143/35)\n"
            "Portable : 0658714328\n"
            "Mail : christianemusella@gmail.com"
        ),
    ],
    ["P.U.H.T (€) Quantité Montant HT (€) TVA", None],
    [
        (
            "M-P : préparation et mis (PS1402) 11.19 15.00 (m²) 167.85 10.00%\n"
            "M-P : préparation et mise en peinture"
        ),
        None,
    ],
]


def _mock_pdf(texte_p1: str, texte_p2: str = "", tables_p1: list | None = None):
    """Crée un mock pdfplumber avec pages simulées."""
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = texte_p1
    mock_page1.extract_tables.return_value = [tables_p1] if tables_p1 else []

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
    mock_open.return_value = _mock_pdf(TEXTE_GDH_PAGE1, TEXTE_GDH_PAGE2, TABLE_P1)
    result = GDHParser(PDF_FICTIF).extraire()

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
    mock_open.return_value = _mock_pdf(TEXTE_GDH_PAGE1, TEXTE_GDH_PAGE2, TABLE_P1)
    assert GDHParser(PDF_FICTIF).extraire()["bailleur_code"] == "GDH"


@patch("apps.pdf_extraction.gdh_parser.pdfplumber.open")
def test_extraire_numero_bdc(mock_open):
    mock_open.return_value = _mock_pdf(TEXTE_GDH_PAGE1, TEXTE_GDH_PAGE2, TABLE_P1)
    assert GDHParser(PDF_FICTIF).extraire()["numero_bdc"] == "450056"


@patch("apps.pdf_extraction.gdh_parser.pdfplumber.open")
def test_extraire_date_emission(mock_open):
    mock_open.return_value = _mock_pdf(TEXTE_GDH_PAGE1, TEXTE_GDH_PAGE2, TABLE_P1)
    assert GDHParser(PDF_FICTIF).extraire()["date_emission"] == date(2026, 2, 9)


@patch("apps.pdf_extraction.gdh_parser.pdfplumber.open")
def test_extraire_montants_decimal(mock_open):
    mock_open.return_value = _mock_pdf(TEXTE_GDH_PAGE1, TEXTE_GDH_PAGE2, TABLE_P1)
    result = GDHParser(PDF_FICTIF).extraire()
    assert result["montant_ht"] == Decimal("167.85")
    assert result["montant_tva"] == Decimal("16.79")
    assert result["montant_ttc"] == Decimal("184.64")


@patch("apps.pdf_extraction.gdh_parser.pdfplumber.open")
def test_extraire_lignes_prestation(mock_open):
    """Extraction d'une ligne de prestation GDH depuis la table."""
    mock_open.return_value = _mock_pdf(TEXTE_GDH_PAGE1, TEXTE_GDH_PAGE2, TABLE_P1)
    lignes = GDHParser(PDF_FICTIF).extraire()["lignes_prestation"]
    assert len(lignes) == 1
    ligne = lignes[0]
    assert ligne["prix_unitaire"] == Decimal("11.19")
    assert ligne["quantite"] == Decimal("15.00")
    assert ligne["montant_ht"] == Decimal("167.85")
    assert ligne["unite"] == "m²"
    assert "peinture" in ligne["designation"]
    assert ligne["ordre"] == 0


@patch("apps.pdf_extraction.gdh_parser.pdfplumber.open")
def test_extraire_occupant(mock_open):
    mock_open.return_value = _mock_pdf(TEXTE_GDH_PAGE1, TEXTE_GDH_PAGE2, TABLE_P1)
    result = GDHParser(PDF_FICTIF).extraire()
    assert "MUSELLA CHRISTIANE" in result["occupant_nom"]
    assert result["occupant_telephone"] == "0658714328"
    assert result["occupant_email"] == "christianemusella@gmail.com"


@patch("apps.pdf_extraction.gdh_parser.pdfplumber.open")
def test_extraire_champ_absent_retourne_vide(mock_open):
    """Un champ absent retourne '' (pas d'exception)."""
    texte_minimal = "Bon de commande\nobjet\nn° 450056 du 09/02/2026\nGRAND DELTA HABITAT"
    mock_open.return_value = _mock_pdf(texte_minimal)
    result = GDHParser(PDF_FICTIF).extraire()

    assert result["numero_marche"] == ""
    assert result["montant_ht"] is None
    assert result["lignes_prestation"] == []


@patch("apps.pdf_extraction.gdh_parser.pdfplumber.open")
def test_extraire_pdf_une_seule_page(mock_open):
    """Un PDF GDH à 1 page extrait les données sans erreur."""
    mock_open.return_value = _mock_pdf(TEXTE_GDH_PAGE1, tables_p1=TABLE_P1)
    result = GDHParser(PDF_FICTIF).extraire()

    assert result["bailleur_code"] == "GDH"
    assert result["numero_bdc"] == "450056"
