"""Tests de _get_repartition_st avec filtres de periode."""
from datetime import date
from decimal import Decimal

import pytest
from django.test import Client

from apps.bdc.models import BonDeCommande, StatutChoices
from apps.bdc.services import attribuer_st
from apps.bdc.views import _get_repartition_st
from apps.sous_traitants.models import SousTraitant


@pytest.fixture
def client_cdt(utilisateur_cdt) -> Client:
    client = Client()
    client.login(username="cdt_test", password="testpass123")
    return client


@pytest.fixture
def st_alpha(db):
    return SousTraitant.objects.create(nom="Alpha Peinture", telephone="0600000001", actif=True)


@pytest.fixture
def st_beta(db):
    return SousTraitant.objects.create(nom="Beta Deco", telephone="0600000002", actif=True)


@pytest.fixture
def bdcs_multi_dates(db, bailleur_gdh, utilisateur_secretaire, st_alpha, st_beta, utilisateur_cdt):
    """Cree des BDC EN_COURS avec des date_emission differentes."""
    bdcs = []
    for num, st, emission, montant_ht in [
        ("P-JAN", st_alpha, date(2026, 1, 15), Decimal("1000")),
        ("P-FEV1", st_alpha, date(2026, 2, 10), Decimal("2000")),
        ("P-FEV2", st_beta, date(2026, 2, 20), Decimal("3000")),
        ("P-MAR", st_beta, date(2026, 3, 5), Decimal("4000")),
    ]:
        bdc = BonDeCommande.objects.create(
            numero_bdc=num,
            bailleur=bailleur_gdh,
            adresse="Test",
            code_postal="84000",
            ville="Avignon",
            objet_travaux="Test",
            occupation="OCCUPE",
            type_acces="BADGE_CODE",
            modalite_acces="Badge",
            cree_par=utilisateur_secretaire,
            statut=StatutChoices.A_FAIRE,
            date_emission=emission,
            montant_ht=montant_ht,
        )
        attribuer_st(bdc, st, Decimal("65"), utilisateur_cdt)
        bdcs.append(bdc)
    return bdcs


class TestGetRepartitionSTAvecPeriode:
    """Tests du helper _get_repartition_st avec filtres de dates."""

    def test_sans_filtre_retourne_tout(self, bdcs_multi_dates, st_alpha, st_beta):
        qs = _get_repartition_st()
        data = {st.nom: st for st in qs}
        assert data["Alpha Peinture"].nb_bdc == 2
        assert data["Beta Deco"].nb_bdc == 2

    def test_filtre_fevrier(self, bdcs_multi_dates, st_alpha, st_beta):
        qs = _get_repartition_st(date_du=date(2026, 2, 1), date_au=date(2026, 2, 28))
        data = {st.nom: st for st in qs}
        assert data["Alpha Peinture"].nb_bdc == 1
        assert data["Beta Deco"].nb_bdc == 1

    def test_filtre_montant_st(self, bdcs_multi_dates):
        qs = _get_repartition_st(date_du=date(2026, 2, 1), date_au=date(2026, 2, 28))
        data = {st.nom: st for st in qs}
        # Alpha: 2000 * 65% = 1300, Beta: 3000 * 65% = 1950
        assert data["Alpha Peinture"].total_montant_st == Decimal("1300.00")
        assert data["Beta Deco"].total_montant_st == Decimal("1950.00")

    def test_fallback_created_at_si_pas_date_emission(
        self, db, bailleur_gdh, utilisateur_secretaire, st_alpha, utilisateur_cdt
    ):
        bdc = BonDeCommande.objects.create(
            numero_bdc="NO-DATE",
            bailleur=bailleur_gdh,
            adresse="Test",
            code_postal="84000",
            ville="Avignon",
            objet_travaux="Test",
            occupation="OCCUPE",
            type_acces="BADGE_CODE",
            modalite_acces="Badge",
            cree_par=utilisateur_secretaire,
            statut=StatutChoices.A_FAIRE,
            date_emission=None,  # pas de date_emission
        )
        attribuer_st(bdc, st_alpha, Decimal("65"), utilisateur_cdt)
        # created_at est aujourd'hui -> filtre sur le mois courant doit l'inclure
        today = date.today()
        import calendar

        dernier = calendar.monthrange(today.year, today.month)[1]
        qs = _get_repartition_st(date_du=today.replace(day=1), date_au=today.replace(day=dernier))
        data = {st.nom: st for st in qs}
        assert data["Alpha Peinture"].nb_bdc == 1

    def test_statuts_filtre(self, bdcs_multi_dates, st_alpha):
        # Par defaut EN_COURS seulement
        qs = _get_repartition_st(statuts=[StatutChoices.EN_COURS])
        data = {st.nom: st for st in qs}
        assert data["Alpha Peinture"].nb_bdc == 2

    def test_st_sans_bdc_affiche_zero(self, bdcs_multi_dates, db):
        SousTraitant.objects.create(nom="Zeta Vide", telephone="0600000099", actif=True)
        qs = _get_repartition_st(date_du=date(2026, 2, 1), date_au=date(2026, 2, 28))
        data = {st.nom: st for st in qs}
        assert data["Zeta Vide"].nb_bdc == 0
