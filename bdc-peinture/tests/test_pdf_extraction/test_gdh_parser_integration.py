"""
Tests d'intégration GDHParser avec le vrai PDF modèle (docs/Modèle_bdc_GDH.pdf).
"""
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from apps.pdf_extraction.gdh_parser import GDHParser

PDF_MODELE = Path(__file__).resolve().parents[2] / ".." / "docs" / "Modèle_bdc_GDH.pdf"

pytestmark = pytest.mark.skipif(
    not PDF_MODELE.exists(),
    reason=f"PDF modèle GDH introuvable : {PDF_MODELE}",
)


@pytest.fixture(scope="module")
def resultat():
    """Exécute l'extraction une seule fois pour tous les tests."""
    return GDHParser(PDF_MODELE).extraire()


class TestGDHIntegration:

    def test_bailleur_code(self, resultat):
        assert resultat["bailleur_code"] == "GDH"

    def test_numero_bdc(self, resultat):
        assert resultat["numero_bdc"] == "450056"

    def test_date_emission(self, resultat):
        assert resultat["date_emission"] == date(2026, 2, 9)

    def test_numero_marche(self, resultat):
        assert resultat["numero_marche"] == "026322-CPP-003"

    def test_objet_travaux(self, resultat):
        assert "reprise peinture SDB" in resultat["objet_travaux"]
        assert "trx faience" in resultat["objet_travaux"]

    def test_adresse(self, resultat):
        assert "Francois 1er" in resultat["adresse"]

    def test_code_postal(self, resultat):
        assert resultat["code_postal"] == "84000"

    def test_ville(self, resultat):
        assert resultat["ville"] == "AVIGNON"

    def test_logement_numero(self, resultat):
        assert resultat["logement_numero"] == "000756"

    def test_logement_type(self, resultat):
        assert resultat["logement_type"] == "Type 3"

    def test_logement_etage(self, resultat):
        assert resultat["logement_etage"] == "1"

    def test_logement_porte(self, resultat):
        assert resultat["logement_porte"] == "107"

    def test_programme_residence(self, resultat):
        assert "VERONESE" in resultat["programme_residence"]

    def test_occupant_nom(self, resultat):
        assert "MUSELLA" in resultat["occupant_nom"]
        assert "CHRISTIANE" in resultat["occupant_nom"]

    def test_occupant_telephone(self, resultat):
        assert resultat["occupant_telephone"] == "0658714328"

    def test_occupant_email(self, resultat):
        assert resultat["occupant_email"] == "christianemusella@gmail.com"

    def test_emetteur_nom(self, resultat):
        assert "Joseph LONEGRO" in resultat["emetteur_nom"]

    def test_emetteur_telephone(self, resultat):
        assert resultat["emetteur_telephone"] == "0637577004"

    def test_delai_execution(self, resultat):
        assert resultat["delai_execution"] == date(2026, 2, 20)

    def test_montant_ht(self, resultat):
        assert resultat["montant_ht"] == Decimal("167.85")

    def test_montant_tva(self, resultat):
        assert resultat["montant_tva"] == Decimal("16.79")

    def test_montant_ttc(self, resultat):
        assert resultat["montant_ttc"] == Decimal("184.64")

    def test_lignes_prestation_vide(self, resultat):
        assert resultat["lignes_prestation"] == []
