"""
Tests du workflow de statuts BDC.
Vérifie les transitions autorisées, invalides, et les règles métier.
"""
import pytest

from apps.bdc.models import StatutChoices
from apps.bdc.services import BDCIncomplet, TransitionInvalide, changer_statut


class TestTransitionsValides:
    def test_a_traiter_vers_a_faire(self, bdc_a_traiter, utilisateur_secretaire):
        bdc_a_traiter.occupation = "VACANT"
        bdc_a_traiter.type_acces = "BADGE_CODE"
        bdc_a_traiter.modalite_acces = "Badge gardien"
        bdc_a_traiter.save()

        bdc = changer_statut(bdc_a_traiter, StatutChoices.A_FAIRE, utilisateur_secretaire)
        assert bdc.statut == StatutChoices.A_FAIRE

    def test_a_faire_vers_en_cours(self, bdc_a_faire, utilisateur_cdt):
        bdc = changer_statut(bdc_a_faire, StatutChoices.EN_COURS, utilisateur_cdt)
        assert bdc.statut == StatutChoices.EN_COURS

    def test_a_faire_retour_a_traiter(self, bdc_a_faire, utilisateur_secretaire):
        bdc = changer_statut(bdc_a_faire, StatutChoices.A_TRAITER, utilisateur_secretaire)
        assert bdc.statut == StatutChoices.A_TRAITER

    def test_en_cours_vers_a_facturer(self, db, bailleur_gdh, utilisateur_cdt):

        from apps.bdc.models import BonDeCommande

        bdc = BonDeCommande.objects.create(
            numero_bdc="TEST_EN_COURS",
            bailleur=bailleur_gdh,
            adresse="1 Rue Test",
            objet_travaux="Test",
            occupation="VACANT",
            statut=StatutChoices.EN_COURS,
            cree_par=utilisateur_cdt,
        )
        bdc = changer_statut(bdc, StatutChoices.A_FACTURER, utilisateur_cdt)
        assert bdc.statut == StatutChoices.A_FACTURER

    def test_a_facturer_vers_facture(self, db, bailleur_gdh, utilisateur_cdt):
        from apps.bdc.models import BonDeCommande

        bdc = BonDeCommande.objects.create(
            numero_bdc="TEST_A_FACTURER",
            bailleur=bailleur_gdh,
            adresse="1 Rue Test",
            objet_travaux="Test",
            occupation="VACANT",
            statut=StatutChoices.A_FACTURER,
            cree_par=utilisateur_cdt,
        )
        bdc = changer_statut(bdc, StatutChoices.FACTURE, utilisateur_cdt)
        assert bdc.statut == StatutChoices.FACTURE


class TestTransitionsInvalides:
    def test_a_traiter_vers_en_cours_impossible(self, bdc_a_traiter, utilisateur_cdt):
        with pytest.raises(TransitionInvalide):
            changer_statut(bdc_a_traiter, StatutChoices.EN_COURS, utilisateur_cdt)

    def test_a_traiter_vers_a_facturer_impossible(self, bdc_a_traiter, utilisateur_cdt):
        with pytest.raises(TransitionInvalide):
            changer_statut(bdc_a_traiter, StatutChoices.A_FACTURER, utilisateur_cdt)

    def test_a_traiter_vers_facture_impossible(self, bdc_a_traiter, utilisateur_cdt):
        with pytest.raises(TransitionInvalide):
            changer_statut(bdc_a_traiter, StatutChoices.FACTURE, utilisateur_cdt)


class TestEtatTerminalFacture:
    def test_facture_est_terminal(self, db, bailleur_gdh, utilisateur_cdt):
        from apps.bdc.models import BonDeCommande

        bdc = BonDeCommande.objects.create(
            numero_bdc="TEST_FACTURE",
            bailleur=bailleur_gdh,
            adresse="1 Rue Test",
            objet_travaux="Test",
            occupation="VACANT",
            statut=StatutChoices.FACTURE,
            cree_par=utilisateur_cdt,
        )
        for statut in [
            StatutChoices.A_TRAITER,
            StatutChoices.A_FAIRE,
            StatutChoices.EN_COURS,
            StatutChoices.A_FACTURER,
        ]:
            with pytest.raises(TransitionInvalide):
                changer_statut(bdc, statut, utilisateur_cdt)


class TestReglesMetier:
    def test_occupation_obligatoire_avant_a_faire(self, bdc_a_traiter, utilisateur_secretaire):
        """Le champ occupation doit être renseigné avant passage en À attribuer."""
        assert bdc_a_traiter.occupation == ""  # pas renseigné

        with pytest.raises(BDCIncomplet):
            changer_statut(bdc_a_traiter, StatutChoices.A_FAIRE, utilisateur_secretaire)

    def test_type_acces_obligatoire_avant_a_faire(self, bdc_a_traiter, utilisateur_secretaire):
        """Le type d'accès doit être renseigné avant passage en À attribuer."""
        bdc_a_traiter.occupation = "VACANT"
        bdc_a_traiter.modalite_acces = "Badge gardien"
        bdc_a_traiter.save()

        with pytest.raises(BDCIncomplet, match="type d'accès"):
            changer_statut(bdc_a_traiter, StatutChoices.A_FAIRE, utilisateur_secretaire)

    def test_modalite_acces_obligatoire_avant_a_faire(self, bdc_a_traiter, utilisateur_secretaire):
        """La modalité d'accès doit être renseignée avant passage en À attribuer."""
        bdc_a_traiter.occupation = "VACANT"
        bdc_a_traiter.type_acces = "BADGE_CODE"
        bdc_a_traiter.save()

        with pytest.raises(BDCIncomplet, match="modalité d'accès"):
            changer_statut(bdc_a_traiter, StatutChoices.A_FAIRE, utilisateur_secretaire)

    def test_occupation_renseignee_permet_a_faire(self, bdc_a_traiter, utilisateur_secretaire):
        bdc_a_traiter.occupation = "VACANT"
        bdc_a_traiter.type_acces = "BADGE_CODE"
        bdc_a_traiter.modalite_acces = "Badge gardien"
        bdc_a_traiter.save()

        bdc = changer_statut(bdc_a_traiter, StatutChoices.A_FAIRE, utilisateur_secretaire)
        assert bdc.statut == StatutChoices.A_FAIRE


class TestLabelRenommage:
    def test_a_faire_label_est_a_attribuer(self):
        """Le label du statut A_FAIRE doit être 'À attribuer'."""
        assert StatutChoices.A_FAIRE.label == "À attribuer"
