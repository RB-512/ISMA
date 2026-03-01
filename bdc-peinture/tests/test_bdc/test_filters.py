"""Tests unitaires du BonDeCommandeFilter."""

import pytest

from apps.bdc.filters import BonDeCommandeFilter
from apps.bdc.models import BonDeCommande, StatutChoices

pytestmark = pytest.mark.django_db


@pytest.fixture
def bdc_erilia(bailleur_erilia, utilisateur_secretaire):
    return BonDeCommande.objects.create(
        numero_bdc="ERI-001",
        bailleur=bailleur_erilia,
        adresse="10 Boulevard Michelet",
        ville="Marseille",
        cree_par=utilisateur_secretaire,
        statut=StatutChoices.EN_COURS,
    )


class TestBonDeCommandeFilter:
    def test_filtre_statut(self, bdc_a_traiter, bdc_a_faire):
        f = BonDeCommandeFilter({"statut": "A_FAIRE"}, queryset=BonDeCommande.objects.all())
        assert list(f.qs) == [bdc_a_faire]

    def test_filtre_statut_vide_retourne_tout(self, bdc_a_traiter, bdc_a_faire):
        f = BonDeCommandeFilter({}, queryset=BonDeCommande.objects.all())
        assert f.qs.count() == 2

    def test_filtre_bailleur(self, bdc_a_traiter, bdc_erilia):
        f = BonDeCommandeFilter(
            {"bailleur": bdc_erilia.bailleur.pk},
            queryset=BonDeCommande.objects.all(),
        )
        assert list(f.qs) == [bdc_erilia]

    def test_filtre_ville_icontains(self, bdc_a_traiter, bdc_erilia):
        f = BonDeCommandeFilter({"ville": "marseille"}, queryset=BonDeCommande.objects.all())
        assert list(f.qs) == [bdc_erilia]

    def test_filtre_ville_partiel(self, bdc_a_traiter, bdc_erilia):
        f = BonDeCommandeFilter({"ville": "Avi"}, queryset=BonDeCommande.objects.all())
        assert list(f.qs) == [bdc_a_traiter]

    def test_filtre_date_du(self, bdc_a_traiter):
        f = BonDeCommandeFilter(
            {"date_du": "2020-01-01"},
            queryset=BonDeCommande.objects.all(),
        )
        assert bdc_a_traiter in f.qs

    def test_filtre_date_au_exclut_futur(self, bdc_a_traiter):
        f = BonDeCommandeFilter(
            {"date_au": "2020-01-01"},
            queryset=BonDeCommande.objects.all(),
        )
        assert bdc_a_traiter not in f.qs

    def test_combinaison_statut_et_bailleur(self, bdc_a_traiter, bdc_a_faire, bdc_erilia):
        f = BonDeCommandeFilter(
            {"statut": "A_TRAITER", "bailleur": bdc_a_traiter.bailleur.pk},
            queryset=BonDeCommande.objects.all(),
        )
        assert list(f.qs) == [bdc_a_traiter]
