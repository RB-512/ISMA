"""
Tests du champ type_bon (Simple / Mixte) sur BonDeCommande.
"""

import pytest
from django.urls import reverse

from apps.bdc.models import BonDeCommande, StatutChoices, TypeBonChoices


@pytest.fixture
def client_secretaire(client, utilisateur_secretaire):
    client.force_login(utilisateur_secretaire)
    return client


class TestTypeBonDefaut:
    def test_valeur_par_defaut_simple(self, bdc_a_traiter):
        assert bdc_a_traiter.type_bon == TypeBonChoices.SIMPLE

    def test_get_display(self, bdc_a_traiter):
        assert bdc_a_traiter.get_type_bon_display() == "Simple"

    def test_set_mixte(self, bdc_a_traiter):
        bdc_a_traiter.type_bon = TypeBonChoices.MIXTE
        bdc_a_traiter.save()
        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.type_bon == TypeBonChoices.MIXTE
        assert bdc_a_traiter.get_type_bon_display() == "Mixte"


class TestTypeBonFormulaire:
    def test_controle_sauvegarde_type_bon(self, client_secretaire, bdc_a_traiter):
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        data = {
            "type_bon": "MIXTE",
            "occupation": "VACANT",
            "type_acces": "BADGE_CODE",
            "acces_complement": "Code 1234",
            "rdv_date": "",
            "notes": "",
            "nouveau_statut": "",
        }
        resp = client_secretaire.post(url, data)
        assert resp.status_code == 200
        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.type_bon == TypeBonChoices.MIXTE


class TestTypeBonFiltre:
    def test_filtre_type_bon_simple(self, client_secretaire, bdc_a_traiter):
        resp = client_secretaire.get(reverse("bdc:index"), {"type_bon": "SIMPLE"})
        assert resp.status_code == 200
        assert bdc_a_traiter in resp.context["page_obj"]

    def test_filtre_type_bon_mixte_exclut_simple(self, client_secretaire, bdc_a_traiter):
        resp = client_secretaire.get(reverse("bdc:index"), {"type_bon": "MIXTE"})
        assert resp.status_code == 200
        assert bdc_a_traiter not in resp.context["page_obj"]

    def test_filtre_sans_type_montre_tous(self, client_secretaire, bdc_a_traiter):
        resp = client_secretaire.get(reverse("bdc:index"))
        assert resp.status_code == 200
        assert bdc_a_traiter in resp.context["page_obj"]
