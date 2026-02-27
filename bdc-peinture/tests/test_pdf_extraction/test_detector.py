"""
Tests unitaires de detecter_parser() — pdfplumber mocké.
"""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from apps.pdf_extraction.detector import (
    MARQUEUR_ERILIA,
    MARQUEUR_GDH,
    PDFTypeInconnu,
    detecter_parser,
)
from apps.pdf_extraction.erilia_parser import ERILIAParser
from apps.pdf_extraction.gdh_parser import GDHParser

PDF_FICTIF = Path("/tmp/test.pdf")


def _mock_pdf(texte_page1: str):
    """Crée un mock pdfplumber.PDF avec une seule page retournant le texte donné."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = texte_page1

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    return mock_pdf


@patch("apps.pdf_extraction.detector.pdfplumber.open")
def test_detection_gdh(mock_open):
    """Un PDF contenant le marqueur GDH retourne un GDHParser."""
    mock_open.return_value = _mock_pdf(f"En-tête : {MARQUEUR_GDH}\nBon de Commande N° : 450098")

    parser = detecter_parser(PDF_FICTIF)

    assert isinstance(parser, GDHParser)
    assert parser.pdf_path == PDF_FICTIF


@patch("apps.pdf_extraction.detector.pdfplumber.open")
def test_detection_gdh_insensible_casse(mock_open):
    """La détection GDH est insensible à la casse."""
    mock_open.return_value = _mock_pdf("grand delta habitat - bon de commande")

    parser = detecter_parser(PDF_FICTIF)

    assert isinstance(parser, GDHParser)


@patch("apps.pdf_extraction.detector.pdfplumber.open")
def test_detection_erilia(mock_open):
    """Un PDF contenant le marqueur ERILIA retourne un ERILIAParser."""
    mock_open.return_value = _mock_pdf(f"SOCIÉTÉ : {MARQUEUR_ERILIA}\nBon de Commande N° : E-2024-001")

    parser = detecter_parser(PDF_FICTIF)

    assert isinstance(parser, ERILIAParser)
    assert parser.pdf_path == PDF_FICTIF


@patch("apps.pdf_extraction.detector.pdfplumber.open")
def test_detection_erilia_insensible_casse(mock_open):
    """La détection ERILIA est insensible à la casse."""
    mock_open.return_value = _mock_pdf("erilia - bon de commande")

    parser = detecter_parser(PDF_FICTIF)

    assert isinstance(parser, ERILIAParser)


@patch("apps.pdf_extraction.detector.pdfplumber.open")
def test_detection_pdf_inconnu(mock_open):
    """Un PDF sans marqueur reconnu lève PDFTypeInconnu."""
    mock_open.return_value = _mock_pdf("Société XYZ - Devis n° 1234")

    with pytest.raises(PDFTypeInconnu) as exc_info:
        detecter_parser(PDF_FICTIF)

    assert "non reconnu" in str(exc_info.value).lower()


@patch("apps.pdf_extraction.detector.pdfplumber.open")
def test_detection_pdf_vide(mock_open):
    """Un PDF sans pages lève PDFTypeInconnu."""
    mock_pdf = MagicMock()
    mock_pdf.pages = []
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_open.return_value = mock_pdf

    with pytest.raises(PDFTypeInconnu):
        detecter_parser(PDF_FICTIF)


@patch("apps.pdf_extraction.detector.pdfplumber.open")
def test_detection_priorite_gdh_sur_erilia(mock_open):
    """GDH est prioritaire si les deux marqueurs apparaissent (cas hypothétique)."""
    mock_open.return_value = _mock_pdf(f"{MARQUEUR_GDH} et {MARQUEUR_ERILIA}")

    parser = detecter_parser(PDF_FICTIF)

    assert isinstance(parser, GDHParser)
