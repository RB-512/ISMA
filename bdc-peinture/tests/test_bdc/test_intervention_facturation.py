"""
Tests — date d'intervention (EN_COURS → A_FACTURER) et N° / date de facture (A_FACTURER → FACTURE).
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.bdc.models import BonDeCommande, HistoriqueAction, StatutChoices
from apps.bdc.services import BDCIncomplet, changer_statut, valider_facturation, valider_realisation


@pytest.fixture
def bdc_en_cours(db, bailleur_gdh, utilisateur_cdt, sous_traitant):
    return BonDeCommande.objects.create(
        numero_bdc="INT-001",
        bailleur=bailleur_gdh,
        adresse="1 Rue de l'Intervention",
        occupation="VACANT",
        statut=StatutChoices.EN_COURS,
        sous_traitant=sous_traitant,
        pourcentage_st=Decimal("65"),
        cree_par=utilisateur_cdt,
    )


@pytest.fixture
def bdc_a_facturer(db, bailleur_gdh, utilisateur_cdt, sous_traitant):
    return BonDeCommande.objects.create(
        numero_bdc="FAC-001",
        bailleur=bailleur_gdh,
        adresse="2 Rue de la Facture",
        occupation="VACANT",
        statut=StatutChoices.A_FACTURER,
        sous_traitant=sous_traitant,
        date_realisation=date(2026, 1, 20),
        date_intervention=date(2026, 1, 15),
        cree_par=utilisateur_cdt,
    )


# ─── Service : date d'intervention ──────────────────────────────────────────


class TestDateIntervention:
    def test_obligatoire(self, bdc_en_cours, utilisateur_cdt):
        with pytest.raises(BDCIncomplet, match="date d'intervention est obligatoire"):
            valider_realisation(bdc_en_cours, utilisateur_cdt)
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.EN_COURS

    def test_refus_date_future(self, bdc_en_cours, utilisateur_cdt):
        demain = date.today() + timedelta(days=1)
        with pytest.raises(BDCIncomplet, match="futur"):
            valider_realisation(bdc_en_cours, utilisateur_cdt, date_intervention=demain)

    def test_enregistree(self, bdc_en_cours, utilisateur_cdt):
        valider_realisation(bdc_en_cours, utilisateur_cdt, date_intervention=date(2026, 1, 15))
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.A_FACTURER
        assert bdc_en_cours.date_intervention == date(2026, 1, 15)
        action = HistoriqueAction.objects.get(bdc=bdc_en_cours, action="VALIDATION")
        assert action.details["date_intervention"] == "2026-01-15"

    def test_changer_statut_generique_bloque_sans_date(self, bdc_en_cours, utilisateur_cdt):
        with pytest.raises(BDCIncomplet):
            changer_statut(bdc_en_cours, StatutChoices.A_FACTURER, utilisateur_cdt)

    def test_retour_en_cours_efface_date(self, bdc_a_facturer, utilisateur_cdt):
        changer_statut(bdc_a_facturer, StatutChoices.EN_COURS, utilisateur_cdt)
        bdc_a_facturer.refresh_from_db()
        assert bdc_a_facturer.date_intervention is None


# ─── Service : N° et date de facture ────────────────────────────────────────


class TestInfosFacturation:
    def test_numero_obligatoire(self, bdc_a_facturer, utilisateur_cdt):
        with pytest.raises(BDCIncomplet, match="N° de facture"):
            valider_facturation(bdc_a_facturer, utilisateur_cdt, numero_facture="  ", date_facturation=date.today())

    def test_date_obligatoire(self, bdc_a_facturer, utilisateur_cdt):
        with pytest.raises(BDCIncomplet, match="date de facturation"):
            valider_facturation(bdc_a_facturer, utilisateur_cdt, numero_facture="F-001")
        bdc_a_facturer.refresh_from_db()
        assert bdc_a_facturer.statut == StatutChoices.A_FACTURER

    def test_enregistrees(self, bdc_a_facturer, utilisateur_cdt):
        valider_facturation(
            bdc_a_facturer, utilisateur_cdt, numero_facture=" F-2026-042 ", date_facturation=date(2026, 2, 1)
        )
        bdc_a_facturer.refresh_from_db()
        assert bdc_a_facturer.statut == StatutChoices.FACTURE
        assert bdc_a_facturer.numero_facture == "F-2026-042"
        assert bdc_a_facturer.date_facturation == date(2026, 2, 1)
        action = HistoriqueAction.objects.get(bdc=bdc_a_facturer, action="FACTURATION")
        assert action.details == {"numero_facture": "F-2026-042", "date_facturation": "2026-02-01"}

    def test_changer_statut_generique_bloque_sans_facture(self, bdc_a_facturer, utilisateur_cdt):
        with pytest.raises(BDCIncomplet):
            changer_statut(bdc_a_facturer, StatutChoices.FACTURE, utilisateur_cdt)


# ─── Vues ────────────────────────────────────────────────────────────────────


class TestVues:
    def test_valider_realisation_sans_date_affiche_erreur(self, client_cdt, bdc_en_cours):
        url = reverse("bdc:valider_realisation", args=[bdc_en_cours.pk])
        resp = client_cdt.post(url, HTTP_HX_REQUEST="true")
        assert "date d&#x27;intervention est obligatoire" in resp.content.decode()
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.EN_COURS

    def test_panneau_realisation_affiche_champ_date(self, client_cdt, bdc_en_cours):
        url = reverse("bdc:sidebar_checklist", args=[bdc_en_cours.pk]) + "?transition=EN_COURS__A_FACTURER"
        content = client_cdt.get(url).content.decode()
        assert 'name="date_intervention"' in content

    def test_panneau_facturation_affiche_champs(self, client_cdt, bdc_a_facturer):
        url = reverse("bdc:sidebar_checklist", args=[bdc_a_facturer.pk]) + "?transition=A_FACTURER__FACTURE"
        content = client_cdt.get(url).content.decode()
        assert 'name="numero_facture"' in content
        assert 'name="date_facturation"' in content

    def test_panneau_facturation_sans_numero_garde_saisie(self, client_cdt, bdc_a_facturer):
        url = reverse("bdc:sidebar_checklist", args=[bdc_a_facturer.pk])
        data = {"transition": "A_FACTURER__FACTURE", "numero_facture": "", "date_facturation": "2026-02-01"}
        content = client_cdt.post(url, data, HTTP_HX_REQUEST="true").content.decode()
        assert "N° de facture est obligatoire" in content
        assert 'value="2026-02-01"' in content
        bdc_a_facturer.refresh_from_db()
        assert bdc_a_facturer.statut == StatutChoices.A_FACTURER

    def test_tableau_de_bord_affiche_infos(self, client_cdt, bdc_a_facturer):
        bdc_a_facturer.statut = StatutChoices.FACTURE
        bdc_a_facturer.numero_facture = "F-2026-042"
        bdc_a_facturer.date_facturation = date(2026, 2, 1)
        bdc_a_facturer.save()
        content = client_cdt.get(reverse("bdc:index")).content.decode()
        assert "15/01/2026" in content  # date d'intervention
        assert "F-2026-042" in content
        assert "01/02/2026" in content

    def test_recherche_par_numero_facture(self, client_cdt, bdc_a_facturer, bdc_en_cours):
        bdc_a_facturer.numero_facture = "F-2026-042"
        bdc_a_facturer.save()
        content = client_cdt.get(reverse("bdc:index") + "?q=F-2026-042").content.decode()
        assert "FAC-001" in content
        assert "INT-001" not in content
