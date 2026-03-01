"""
Tests d'intégration ERILIAParser avec le vrai PDF modèle (docs/Modèle_bdc_ERILIA.pdf).
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from apps.pdf_extraction.erilia_parser import ERILIAParser

PDF_MODELE = Path(__file__).resolve().parents[2] / ".." / "docs" / "Modèle_bdc_ERILIA.pdf"

pytestmark = pytest.mark.skipif(
    not PDF_MODELE.exists(),
    reason=f"PDF modèle ERILIA introuvable : {PDF_MODELE}",
)


@pytest.fixture(scope="module")
def resultat():
    """Exécute l'extraction une seule fois pour tous les tests."""
    return ERILIAParser(PDF_MODELE).extraire()


class TestERILIAIntegration:
    def test_bailleur_code(self, resultat):
        assert resultat["bailleur_code"] == "ERILIA"

    def test_numero_bdc(self, resultat):
        assert resultat["numero_bdc"] == "2026 20205"

    def test_date_emission(self, resultat):
        assert resultat["date_emission"] == date(2026, 2, 6)

    def test_numero_marche(self, resultat):
        assert "2025 356 4 1" in resultat["numero_marche"]

    def test_objet_travaux(self, resultat):
        assert "2026/15635" in resultat["objet_travaux"]

    def test_adresse(self, resultat):
        assert "PETITE VITESSE" in resultat["adresse"]

    def test_code_postal(self, resultat):
        assert resultat["code_postal"] == "84000"

    def test_ville(self, resultat):
        assert resultat["ville"] == "AVIGNON"

    def test_logement_numero(self, resultat):
        assert resultat["logement_numero"] == "50"

    def test_logement_etage(self, resultat):
        assert resultat["logement_etage"] == "01"

    def test_programme_residence(self, resultat):
        assert "TERRASSES DE MERCURE" in resultat["programme_residence"]

    def test_emetteur_nom(self, resultat):
        assert "ARCQ GWENAEL" in resultat["emetteur_nom"]

    def test_emetteur_telephone(self, resultat):
        assert resultat["emetteur_telephone"] == "0432743295"

    def test_delai_execution(self, resultat):
        assert resultat["delai_execution"] == date(2026, 2, 15)

    def test_montant_ht(self, resultat):
        assert resultat["montant_ht"] == Decimal("1071.40")

    def test_montant_tva(self, resultat):
        assert resultat["montant_tva"] == Decimal("107.14")

    def test_montant_ttc(self, resultat):
        assert resultat["montant_ttc"] == Decimal("1178.54")

    def test_lignes_prestation(self, resultat):
        lignes = resultat["lignes_prestation"]
        assert len(lignes) == 3
        # Première ligne : PP4-31
        assert lignes[0]["code"] == "PP4-31"
        assert lignes[0]["prix_unitaire"] == Decimal("180.27")
        assert lignes[0]["quantite"] == Decimal("1.00")
        assert lignes[0]["montant_ht"] == Decimal("180.27")
        assert lignes[0]["unite"] == "FOR"
        assert lignes[0]["ordre"] == 0
        # Deuxième ligne : PP4-33
        assert lignes[1]["code"] == "PP4-33"
        assert lignes[1]["prix_unitaire"] == Decimal("313.10")
        assert lignes[1]["montant_ht"] == Decimal("313.10")
        # Troisième ligne : PP4-43
        assert lignes[2]["code"] == "PP4-43"
        assert lignes[2]["prix_unitaire"] == Decimal("578.03")
        assert lignes[2]["montant_ht"] == Decimal("578.03")
        assert lignes[2]["ordre"] == 2

    def test_occupant_vide(self, resultat):
        # Le PDF ERILIA modèle ne contient pas d'info occupant
        assert resultat["occupant_nom"] == ""
