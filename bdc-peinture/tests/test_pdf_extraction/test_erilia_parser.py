"""
Tests unitaires de ERILIAParser — pdfplumber mocké avec texte au format réel.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

from apps.pdf_extraction.erilia_parser import ERILIAParser

PDF_FICTIF = Path("/tmp/erilia_test.pdf")

# ─── Texte ERILIA au format réel pdfplumber ──────────────────────────────────

TEXTE_ERILIA_PAGE1 = (
    "ERILIA\n"
    "PAGE N° 1\n"
    "NOM ET ADRESSE DE L'EXPÉDITEUR\n"
    "BON DE TRAVAUX\n"
    "ERILIA N° 2026 20205\n"
    "AGENCE AVIGNON\n"
    "2 bis, avenue de la synagogue\n"
    "84000 AVIGNON\n"
    "Tél : 04 32 74 32 90 GROUPEMENT NOUVOSOL- B-Y PEINT\n"
    "Réf. fournisseur F / 24251 CHEZ NOUVOSOL\n"
    "Marché n° 2025 356 4 1 84000 AVIGNON\n"
    "Provenance\n"
    "Objet Récl. Tech. n° 2026/15635\n"
    "SERVICE SERVICES AVIGNON ÉMETTEUR ARCQ GWENAEL Tél 0432743295\n"
    "LOCALISATION ADRESSE 5 RUE DE LA PETITE VITESSE\n"
    "Programme 1398 LES TERRASSES DE MERCURE 84000 AVIGNON\n"
    "Tranche TLO1 Ensemble BAT Escalier D étage 01\n"
    "Logement 50 Module E13980050L\n"
    "Réclamation n° 2026 15635 1\n"
    "DÉLAI D'EXÉCUTION 10 JOURS PÉRIODE DU 06-02-2026 AU 15-02-2026\n"
    "TOTAL H.T. 1.071,40\n"
    "T.V.A. 10,00 % 107,14\n"
    "TOTAL T.T.C. 1.178,54\n"
)

TEXTE_ERILIA_PAGE2 = (
    "ERILIA\n"
    "PAGE N° 2\n"
    "TOTAL H.T. 1.071,40\n"
    "T.V.A. 10,00 % 107,14\n"
    "TOTAL T.T.C. 1.178,54\n"
    "Édité le\n"
    "06-02-2026\n"
    "Le Service émetteur\n"
)


TABLES_ERILIA_P1 = [
    # Table 0 : en-tête (non utilisée pour les lignes)
    [
        ["ERILIA\nPAGE N° 1", None],
    ],
    # Table 1 : prestations
    [
        ["ARTICLE DÉSIGNATION UNITÉ QUANTITÉ PRIX UNITAIRE H.T. TOTAL T.T.C."],
        [
            "PP4-31 Peinture finition A sur murs, plafond, FOR 1,00 180,27 198,30\n"
            "boiseries et métalleries - WC\n"
            "EDL : Peinture plafond logement - Peinture\n"
            "cuisine - peinture WC\n"
            "PP4-33 Peinture finition A sur murs, plafond, FOR 1,00 313,10 344,41\n"
            "boiseries et métalleries - cuisine\n"
            "EDL : Peinture plafond logement - Peinture\n"
            "cuisine - peinture WC\n"
            "PP4-43 Peinture finition A sur plafonds - FOR 1,00 578,03 635,83\n"
            "logement complet T3\n"
            "EDL : Peinture plafond logement - Peinture\n"
            "cuisine - peinture WC"
        ],
        ["TOTAL H.T. 1.071,40"],
        ["T.V.A. 10,00 % 107,14"],
        ["TOTAL T.T.C. 1.178,54"],
    ],
]


def _mock_pdf(texte_pages: list[str], tables_p1: list | None = None):
    """Crée un mock pdfplumber avec N pages."""
    pages = []
    for i, texte in enumerate(texte_pages):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = texte
        mock_page.extract_tables.return_value = tables_p1 if (i == 0 and tables_p1) else []
        pages.append(mock_page)

    mock_pdf = MagicMock()
    mock_pdf.pages = pages
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    return mock_pdf


# ─── Tests ────────────────────────────────────────────────────────────────────


@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_retourne_dict_complet(mock_open):
    """extraire() retourne un dict avec toutes les clés attendues."""
    mock_open.return_value = _mock_pdf([TEXTE_ERILIA_PAGE1, TEXTE_ERILIA_PAGE2], TABLES_ERILIA_P1)
    result = ERILIAParser(PDF_FICTIF).extraire()

    cles_attendues = [
        "bailleur_code",
        "numero_bdc",
        "numero_marche",
        "date_emission",
        "programme_residence",
        "adresse",
        "code_postal",
        "ville",
        "logement_numero",
        "logement_type",
        "logement_etage",
        "logement_porte",
        "objet_travaux",
        "delai_execution",
        "occupant_nom",
        "occupant_telephone",
        "occupant_email",
        "emetteur_nom",
        "emetteur_telephone",
        "montant_ht",
        "montant_tva",
        "montant_ttc",
        "lignes_prestation",
    ]
    for cle in cles_attendues:
        assert cle in result, f"Clé manquante : {cle}"


@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_bailleur_code(mock_open):
    mock_open.return_value = _mock_pdf([TEXTE_ERILIA_PAGE1, TEXTE_ERILIA_PAGE2], TABLES_ERILIA_P1)
    assert ERILIAParser(PDF_FICTIF).extraire()["bailleur_code"] == "ERILIA"


@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_numero_bdc(mock_open):
    mock_open.return_value = _mock_pdf([TEXTE_ERILIA_PAGE1, TEXTE_ERILIA_PAGE2], TABLES_ERILIA_P1)
    assert ERILIAParser(PDF_FICTIF).extraire()["numero_bdc"] == "2026 20205"


@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_date_emission(mock_open):
    mock_open.return_value = _mock_pdf([TEXTE_ERILIA_PAGE1, TEXTE_ERILIA_PAGE2], TABLES_ERILIA_P1)
    assert ERILIAParser(PDF_FICTIF).extraire()["date_emission"] == date(2026, 2, 6)


@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_montants_decimal(mock_open):
    mock_open.return_value = _mock_pdf([TEXTE_ERILIA_PAGE1, TEXTE_ERILIA_PAGE2], TABLES_ERILIA_P1)
    result = ERILIAParser(PDF_FICTIF).extraire()
    assert result["montant_ht"] == Decimal("1071.40")
    assert result["montant_tva"] == Decimal("107.14")
    assert result["montant_ttc"] == Decimal("1178.54")


@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_emetteur(mock_open):
    mock_open.return_value = _mock_pdf([TEXTE_ERILIA_PAGE1, TEXTE_ERILIA_PAGE2], TABLES_ERILIA_P1)
    result = ERILIAParser(PDF_FICTIF).extraire()
    assert "ARCQ GWENAEL" in result["emetteur_nom"]
    assert result["emetteur_telephone"] == "0432743295"


@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_lignes_prestation(mock_open):
    """Extraction de 3 lignes de prestation ERILIA depuis la table."""
    mock_open.return_value = _mock_pdf([TEXTE_ERILIA_PAGE1, TEXTE_ERILIA_PAGE2], TABLES_ERILIA_P1)
    lignes = ERILIAParser(PDF_FICTIF).extraire()["lignes_prestation"]
    assert len(lignes) == 3
    # Première ligne
    assert lignes[0]["code"] == "PP4-31"
    assert lignes[0]["prix_unitaire"] == Decimal("180.27")
    assert lignes[0]["quantite"] == Decimal("1.00")
    assert lignes[0]["montant_ht"] == Decimal("180.27")
    assert lignes[0]["unite"] == "FOR"
    assert "WC" in lignes[0]["designation"]
    assert lignes[0]["ordre"] == 0
    # Troisième ligne
    assert lignes[2]["code"] == "PP4-43"
    assert lignes[2]["prix_unitaire"] == Decimal("578.03")
    assert lignes[2]["montant_ht"] == Decimal("578.03")
    assert lignes[2]["ordre"] == 2


@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_champ_absent_retourne_vide(mock_open):
    texte_minimal = "ERILIA\nERILIA N° 2026 00001\nBON DE TRAVAUX"
    mock_open.return_value = _mock_pdf([texte_minimal])
    result = ERILIAParser(PDF_FICTIF).extraire()

    assert result["adresse"] == ""
    assert result["montant_ht"] is None
    assert result["lignes_prestation"] == []


@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_programme(mock_open):
    mock_open.return_value = _mock_pdf([TEXTE_ERILIA_PAGE1, TEXTE_ERILIA_PAGE2], TABLES_ERILIA_P1)
    result = ERILIAParser(PDF_FICTIF).extraire()
    assert "TERRASSES DE MERCURE" in result["programme_residence"]


@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_adresse(mock_open):
    mock_open.return_value = _mock_pdf([TEXTE_ERILIA_PAGE1, TEXTE_ERILIA_PAGE2], TABLES_ERILIA_P1)
    result = ERILIAParser(PDF_FICTIF).extraire()
    assert "PETITE VITESSE" in result["adresse"]
    assert result["code_postal"] == "84000"
    assert result["ville"] == "AVIGNON"


@patch("apps.pdf_extraction.erilia_parser.pdfplumber.open")
def test_extraire_logement(mock_open):
    mock_open.return_value = _mock_pdf([TEXTE_ERILIA_PAGE1, TEXTE_ERILIA_PAGE2], TABLES_ERILIA_P1)
    result = ERILIAParser(PDF_FICTIF).extraire()
    assert result["logement_numero"] == "50"
    assert result["logement_etage"] == "01"
