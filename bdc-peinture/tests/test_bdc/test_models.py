"""
Tests des modèles du domaine BDC.
"""
import pytest

from apps.bdc.models import (
    Bailleur,
    BonDeCommande,
    HistoriqueAction,
    LignePrestation,
    StatutChoices,
)


class TestBailleur:
    def test_creation(self, db):
        bailleur = Bailleur.objects.create(nom="Grand Delta Habitat", code="GDH")
        assert bailleur.pk is not None
        assert str(bailleur) == "Grand Delta Habitat (GDH)"

    def test_unicite_code(self, db):
        from django.db import IntegrityError

        Bailleur.objects.create(nom="Grand Delta Habitat", code="GDH")
        with pytest.raises(IntegrityError):
            Bailleur.objects.create(nom="GDH bis", code="GDH")


class TestBonDeCommande:
    def test_creation_minimale(self, bdc_a_traiter):
        assert bdc_a_traiter.pk is not None
        assert bdc_a_traiter.statut == StatutChoices.A_TRAITER
        assert bdc_a_traiter.created_at is not None

    def test_statut_par_defaut(self, db, bailleur_gdh, utilisateur_secretaire):
        bdc = BonDeCommande.objects.create(
            numero_bdc="TEST001",
            bailleur=bailleur_gdh,
            adresse="1 Rue Test",
            objet_travaux="Test",
            cree_par=utilisateur_secretaire,
        )
        assert bdc.statut == StatutChoices.A_TRAITER

    def test_unicite_numero_bdc(self, db, bdc_a_traiter, bailleur_gdh, utilisateur_secretaire):
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            BonDeCommande.objects.create(
                numero_bdc="450056",  # même numéro que bdc_a_traiter
                bailleur=bailleur_gdh,
                adresse="Autre adresse",
                objet_travaux="Autre",
                cree_par=utilisateur_secretaire,
            )

    def test_str_representation(self, bdc_a_traiter):
        assert "450056" in str(bdc_a_traiter)
        assert "GDH" in str(bdc_a_traiter)

    def test_adresse_complete(self, bdc_a_traiter):
        adresse = bdc_a_traiter.adresse_complete
        assert "3 Rue François 1er" in adresse
        assert "Avignon" in adresse


class TestLignePrestation:
    def test_creation(self, db, bdc_a_traiter):
        ligne = LignePrestation.objects.create(
            bdc=bdc_a_traiter,
            designation="M-P préparation et mise en peinture",
            quantite=15,
            unite="m²",
            prix_unitaire="11.19",
            montant="167.85",
            ordre=1,
        )
        assert ligne.pk is not None
        assert ligne.bdc == bdc_a_traiter

    def test_3_lignes_sur_bdc(self, db, bdc_a_traiter):
        for i in range(3):
            LignePrestation.objects.create(
                bdc=bdc_a_traiter,
                designation=f"Prestation {i}",
                quantite=10,
                unite="m²",
                prix_unitaire="10.00",
                montant="100.00",
                ordre=i,
            )
        assert bdc_a_traiter.lignes_prestation.count() == 3

    def test_cascade_delete(self, db, bdc_a_traiter):
        LignePrestation.objects.create(
            bdc=bdc_a_traiter,
            designation="Test",
            quantite=1,
            unite="u",
            prix_unitaire="10.00",
            montant="10.00",
        )
        bdc_id = bdc_a_traiter.pk
        bdc_a_traiter.delete()
        assert LignePrestation.objects.filter(bdc_id=bdc_id).count() == 0


class TestHistoriqueAction:
    def test_creation_automatique_via_service(self, bdc_a_traiter, utilisateur_secretaire):
        from apps.bdc.services import changer_statut

        # On remplit les champs obligatoires pour pouvoir passer en A_FAIRE
        bdc_a_traiter.occupation = "VACANT"
        bdc_a_traiter.type_acces = "BADGE_CODE"
        bdc_a_traiter.save()

        changer_statut(bdc_a_traiter, StatutChoices.A_FAIRE, utilisateur_secretaire)

        historique = HistoriqueAction.objects.filter(bdc=bdc_a_traiter).first()
        assert historique is not None
        assert historique.action == "STATUT_CHANGE"
        assert historique.details["ancien_statut"] == StatutChoices.A_TRAITER
        assert historique.details["nouveau_statut"] == StatutChoices.A_FAIRE
