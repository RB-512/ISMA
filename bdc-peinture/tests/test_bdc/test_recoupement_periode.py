"""Tests de la page recoupement avec filtre de periode."""
from datetime import date
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from apps.bdc.models import BonDeCommande, StatutChoices
from apps.bdc.services import attribuer_st
from apps.sous_traitants.models import SousTraitant


@pytest.fixture
def client_cdt(utilisateur_cdt) -> Client:
    client = Client()
    client.login(username="cdt_test", password="testpass123")
    return client


@pytest.fixture
def setup_recoupement(db, bailleur_gdh, utilisateur_secretaire, utilisateur_cdt):
    """2 ST avec BDC sur des mois differents."""
    st1 = SousTraitant.objects.create(nom="Recoup Alpha", telephone="0600000001", actif=True)
    st2 = SousTraitant.objects.create(nom="Recoup Beta", telephone="0600000002", actif=True)

    for num, st, emission in [
        ("R-JAN", st1, date(2026, 1, 10)),
        ("R-FEV", st1, date(2026, 2, 15)),
        ("R-FEV2", st2, date(2026, 2, 20)),
    ]:
        bdc = BonDeCommande.objects.create(
            numero_bdc=num, bailleur=bailleur_gdh,
            adresse="Test", code_postal="84000", ville="Avignon",
            objet_travaux="Test", occupation="OCCUPE",
            type_acces="BADGE_CODE", modalite_acces="Badge",
            cree_par=utilisateur_secretaire, statut=StatutChoices.A_FAIRE,
            date_emission=emission, montant_ht=Decimal("1000"),
        )
        attribuer_st(bdc, st, Decimal("65"), utilisateur_cdt)
    return st1, st2


class TestRecoupementAvecPeriode:
    """Tests de la vue recoupement avec filtre de periode."""

    def test_sans_filtre_cumul_global(self, client_cdt, setup_recoupement):
        resp = client_cdt.get(reverse("bdc:recoupement_liste"))
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Recoup Alpha" in content
        assert "Recoup Beta" in content

    def test_filtre_mois_fevrier(self, client_cdt, setup_recoupement):
        url = reverse("bdc:recoupement_liste") + "?date_du=2026-02-01&date_au=2026-02-28"
        resp = client_cdt.get(url)
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Recoup Alpha" in content

    def test_filtre_periode_raccourci(self, client_cdt, setup_recoupement):
        url = reverse("bdc:recoupement_liste") + "?periode=mois"
        resp = client_cdt.get(url)
        assert resp.status_code == 200

    def test_comparaison_n1_presente(self, client_cdt, setup_recoupement):
        url = reverse("bdc:recoupement_liste") + "?periode=mois&date=2026-02-15"
        resp = client_cdt.get(url)
        content = resp.content.decode()
        # La colonne N-1 doit etre presente
        assert "N-1" in content or "riode pr" in content  # "Periode prec."

    def test_htmx_retourne_partial(self, client_cdt, setup_recoupement):
        url = reverse("bdc:recoupement_liste") + "?periode=mois"
        resp = client_cdt.get(url, HTTP_HX_REQUEST="true")
        assert resp.status_code == 200
        content = resp.content.decode()
        # Pas de balise <html> dans un partial
        assert "<html" not in content.lower()
