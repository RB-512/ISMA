"""Tests CRUD Bibliotheque de prix forfaitaires."""

import pytest
from django.urls import reverse

from apps.bdc.models import PrixForfaitaire


@pytest.fixture
def prix_peinture_t2(db):
    return PrixForfaitaire.objects.create(
        reference="PEINT-T2",
        designation="Peinture logement T2",
        unite="u",
        prix_unitaire="800.00",
    )


class TestBibliothequeAcces:
    def test_cdt_peut_acceder(self, client_cdt):
        resp = client_cdt.get(reverse("bdc:bibliotheque"))
        assert resp.status_code == 200

    def test_secretaire_peut_consulter(self, client_secretaire):
        resp = client_secretaire.get(reverse("bdc:bibliotheque"))
        assert resp.status_code == 200


class TestBibliothequeAjouter:
    def test_ajout_ok(self, client_cdt):
        resp = client_cdt.post(
            reverse("bdc:bibliotheque_ajouter"),
            {
                "reference": "PEINT-T3",
                "designation": "Peinture logement T3",
                "unite": "u",
                "prix_unitaire": "1200.00",
            },
        )
        assert resp.status_code == 200
        assert PrixForfaitaire.objects.filter(reference="PEINT-T3").exists()

    def test_ajout_doublon_refuse(self, client_cdt, prix_peinture_t2):
        resp = client_cdt.post(
            reverse("bdc:bibliotheque_ajouter"),
            {
                "reference": "PEINT-T2",
                "designation": "Autre",
                "unite": "u",
                "prix_unitaire": "500.00",
            },
        )
        assert resp.status_code == 200
        assert PrixForfaitaire.objects.filter(reference="PEINT-T2").count() == 1


class TestBibliothequeModifier:
    def test_modification_ok(self, client_cdt, prix_peinture_t2):
        resp = client_cdt.post(
            reverse("bdc:bibliotheque_modifier", args=[prix_peinture_t2.pk]),
            {
                "reference": "PEINT-T2",
                "designation": "Peinture T2 modifie",
                "unite": "u",
                "prix_unitaire": "850.00",
            },
        )
        assert resp.status_code == 200
        prix_peinture_t2.refresh_from_db()
        assert prix_peinture_t2.designation == "Peinture T2 modifie"

    def test_get_retourne_formulaire_edition(self, client_cdt, prix_peinture_t2):
        resp = client_cdt.get(reverse("bdc:bibliotheque_modifier", args=[prix_peinture_t2.pk]))
        assert resp.status_code == 200
        assert "PEINT-T2" in resp.content.decode()


class TestBibliothequeSupprimer:
    def test_suppression_ok(self, client_cdt, prix_peinture_t2):
        resp = client_cdt.post(reverse("bdc:bibliotheque_supprimer", args=[prix_peinture_t2.pk]))
        assert resp.status_code == 200
        assert not PrixForfaitaire.objects.filter(pk=prix_peinture_t2.pk).exists()
