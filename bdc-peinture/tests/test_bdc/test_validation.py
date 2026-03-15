"""
Tests unitaires — validation réalisation, facturation, retour, vues CDT,
boutons template et recoupement par sous-traitant.
"""

from datetime import date
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.bdc.models import BonDeCommande, HistoriqueAction, StatutChoices
from apps.bdc.services import TransitionInvalide, changer_statut, valider_facturation, valider_realisation

# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def bdc_en_cours(db, bailleur_gdh, utilisateur_cdt, sous_traitant):
    """BDC en statut EN_COURS avec un ST attribué."""
    return BonDeCommande.objects.create(
        numero_bdc="VAL-001",
        bailleur=bailleur_gdh,
        adresse="10 Rue de la Validation",
        occupation="OCCUPE",
        statut=StatutChoices.EN_COURS,
        sous_traitant=sous_traitant,
        pourcentage_st=Decimal("65"),
        cree_par=utilisateur_cdt,
    )


@pytest.fixture
def bdc_a_facturer(db, bailleur_gdh, utilisateur_cdt, sous_traitant):
    """BDC en statut A_FACTURER."""
    return BonDeCommande.objects.create(
        numero_bdc="VAL-002",
        bailleur=bailleur_gdh,
        adresse="11 Rue de la Facturation",
        occupation="VACANT",
        statut=StatutChoices.A_FACTURER,
        sous_traitant=sous_traitant,
        pourcentage_st=Decimal("65"),
        date_realisation=date(2026, 2, 20),
        cree_par=utilisateur_cdt,
    )


# ─── 6.1 Tests valider_realisation ──────────────────────────────────────────


class TestValiderRealisation:
    def test_transition_ok(self, bdc_en_cours, utilisateur_cdt):
        bdc = valider_realisation(bdc_en_cours, utilisateur_cdt)
        assert bdc.statut == StatutChoices.A_FACTURER

    def test_date_realisation_remplie(self, bdc_en_cours, utilisateur_cdt):
        bdc = valider_realisation(bdc_en_cours, utilisateur_cdt)
        assert bdc.date_realisation == date.today()

    def test_historique_validation_cree(self, bdc_en_cours, utilisateur_cdt):
        valider_realisation(bdc_en_cours, utilisateur_cdt)
        action = HistoriqueAction.objects.filter(bdc=bdc_en_cours, action="VALIDATION").first()
        assert action is not None
        assert action.details["date_realisation"] == str(date.today())

    def test_refus_si_pas_en_cours(self, bdc_a_facturer, utilisateur_cdt):
        with pytest.raises(TransitionInvalide, match="En cours"):
            valider_realisation(bdc_a_facturer, utilisateur_cdt)

    def test_refus_si_a_traiter(self, bdc_a_traiter, utilisateur_cdt):
        with pytest.raises(TransitionInvalide):
            valider_realisation(bdc_a_traiter, utilisateur_cdt)


# ─── 6.2 Tests valider_facturation ──────────────────────────────────────────


class TestValiderFacturation:
    def test_transition_ok(self, bdc_a_facturer, utilisateur_cdt):
        bdc = valider_facturation(bdc_a_facturer, utilisateur_cdt)
        assert bdc.statut == StatutChoices.FACTURE

    def test_historique_facturation_cree(self, bdc_a_facturer, utilisateur_cdt):
        valider_facturation(bdc_a_facturer, utilisateur_cdt)
        action = HistoriqueAction.objects.filter(bdc=bdc_a_facturer, action="FACTURATION").first()
        assert action is not None

    def test_refus_si_pas_a_facturer(self, bdc_en_cours, utilisateur_cdt):
        with pytest.raises(TransitionInvalide, match="À facturer"):
            valider_facturation(bdc_en_cours, utilisateur_cdt)


# ─── 6.3 Tests retour A_FACTURER → EN_COURS ────────────────────────────────


class TestRetourAFacturerEnCours:
    def test_date_realisation_remise_a_null(self, bdc_a_facturer, utilisateur_cdt):
        assert bdc_a_facturer.date_realisation is not None
        bdc = changer_statut(bdc_a_facturer, StatutChoices.EN_COURS, utilisateur_cdt)
        assert bdc.statut == StatutChoices.EN_COURS
        assert bdc.date_realisation is None

    def test_date_realisation_nulle_en_db(self, bdc_a_facturer, utilisateur_cdt):
        changer_statut(bdc_a_facturer, StatutChoices.EN_COURS, utilisateur_cdt)
        bdc_a_facturer.refresh_from_db()
        assert bdc_a_facturer.date_realisation is None


# ─── 6.4 Tests vues valider_realisation_bdc et valider_facturation_bdc ──────


class TestVueValiderRealisation:
    def test_post_cdt_ok(self, client, utilisateur_cdt, bdc_en_cours):
        client.force_login(utilisateur_cdt)
        response = client.post(reverse("bdc:valider_realisation", kwargs={"pk": bdc_en_cours.pk}))
        assert response.status_code == 302
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.A_FACTURER

    def test_get_redirige(self, client, utilisateur_cdt, bdc_en_cours):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:valider_realisation", kwargs={"pk": bdc_en_cours.pk}))
        assert response.status_code == 302

    def test_secretaire_cannot_access(self, client, utilisateur_secretaire, bdc_en_cours):
        client.force_login(utilisateur_secretaire)
        response = client.post(reverse("bdc:valider_realisation", kwargs={"pk": bdc_en_cours.pk}))
        assert response.status_code == 403


class TestVueValiderFacturation:
    def test_post_cdt_ok(self, client, utilisateur_cdt, bdc_a_facturer):
        client.force_login(utilisateur_cdt)
        response = client.post(reverse("bdc:valider_facturation", kwargs={"pk": bdc_a_facturer.pk}))
        assert response.status_code == 302
        bdc_a_facturer.refresh_from_db()
        assert bdc_a_facturer.statut == StatutChoices.FACTURE

    def test_get_redirige(self, client, utilisateur_cdt, bdc_a_facturer):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:valider_facturation", kwargs={"pk": bdc_a_facturer.pk}))
        assert response.status_code == 302

    def test_secretaire_cannot_access(self, client, utilisateur_secretaire, bdc_a_facturer):
        client.force_login(utilisateur_secretaire)
        response = client.post(reverse("bdc:valider_facturation", kwargs={"pk": bdc_a_facturer.pk}))
        assert response.status_code == 403


# ─── 6.5 Tests template detail — boutons conditionnels ─────────────────────


class TestTemplateBoutonsValidation:
    def test_bouton_valider_realisation_visible_en_cours(self, client, utilisateur_cdt, bdc_en_cours):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:detail", kwargs={"pk": bdc_en_cours.pk}))
        content = response.content.decode()
        assert "Valider réalisation" in content

    def test_bouton_valider_realisation_absent_a_facturer(self, client, utilisateur_cdt, bdc_a_facturer):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:detail", kwargs={"pk": bdc_a_facturer.pk}))
        content = response.content.decode()
        assert "Valider réalisation" not in content

    def test_bouton_passer_facturation_visible_a_facturer(self, client, utilisateur_cdt, bdc_a_facturer):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:detail", kwargs={"pk": bdc_a_facturer.pk}))
        content = response.content.decode()
        assert "Passer en facturation" in content

    def test_bouton_annuler_validation_visible_a_facturer(self, client, utilisateur_cdt, bdc_a_facturer):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:detail", kwargs={"pk": bdc_a_facturer.pk}))
        content = response.content.decode()
        assert "Annuler validation" in content

    def test_boutons_visibles_pour_secretaire(self, client, utilisateur_secretaire, bdc_en_cours):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:detail", kwargs={"pk": bdc_en_cours.pk}))
        content = response.content.decode()
        assert "Valider réalisation" in content


# ─── 6.6 Tests vues recoupement ─────────────────────────────────────────────


class TestRecoupementListe:
    def test_cdt_accede(self, client, utilisateur_cdt, bdc_en_cours):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:recoupement_liste"))
        assert response.status_code == 200

    def test_secretaire_can_access(self, client, utilisateur_secretaire):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:recoupement_liste"))
        assert response.status_code == 200

    def test_compteurs_affiches(self, client, utilisateur_cdt, bdc_en_cours, sous_traitant):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:recoupement_liste"))
        content = response.content.decode()
        assert sous_traitant.nom in content

    def test_st_sans_bdc_masque(self, client, utilisateur_cdt, db):
        from apps.sous_traitants.models import SousTraitant

        SousTraitant.objects.create(nom="ST Sans BDC", telephone="0600000000")
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:recoupement_liste"))
        content = response.content.decode()
        assert "ST Sans BDC" not in content


class TestRecoupementDetail:
    def test_detail_st_accessible(self, client, utilisateur_cdt, bdc_en_cours, sous_traitant):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:recoupement_detail", kwargs={"st_pk": sous_traitant.pk}))
        assert response.status_code == 200
        content = response.content.decode()
        assert bdc_en_cours.numero_bdc in content

    def test_filtre_statut(self, client, utilisateur_cdt, bdc_en_cours, bdc_a_facturer, sous_traitant):
        client.force_login(utilisateur_cdt)
        response = client.get(
            reverse("bdc:recoupement_detail", kwargs={"st_pk": sous_traitant.pk}) + "?statut=A_FACTURER"
        )
        content = response.content.decode()
        assert bdc_a_facturer.numero_bdc in content
        assert bdc_en_cours.numero_bdc not in content

    def test_lien_vers_detail_bdc(self, client, utilisateur_cdt, bdc_en_cours, sous_traitant):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:recoupement_detail", kwargs={"st_pk": sous_traitant.pk}))
        content = response.content.decode()
        assert reverse("bdc:detail", kwargs={"pk": bdc_en_cours.pk}) in content

    def test_secretaire_can_access(self, client, utilisateur_secretaire, sous_traitant):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:recoupement_detail", kwargs={"st_pk": sous_traitant.pk}))
        assert response.status_code == 200


# ─── RBAC : Secretaire gets 403 on CDT-only workflow views ───────────────


class TestRBACSecretaireBloquee:
    """Verify that Secretaire gets 403 on CDT-only workflow views."""

    def test_secretaire_403_valider_realisation(self, client, utilisateur_secretaire, bdc_en_cours):
        client.force_login(utilisateur_secretaire)
        resp = client.post(reverse("bdc:valider_realisation", kwargs={"pk": bdc_en_cours.pk}))
        assert resp.status_code == 403

    def test_secretaire_403_valider_facturation(self, client, utilisateur_secretaire, bdc_a_facturer):
        client.force_login(utilisateur_secretaire)
        resp = client.post(reverse("bdc:valider_facturation", kwargs={"pk": bdc_a_facturer.pk}))
        assert resp.status_code == 403

    def test_secretaire_can_renvoyer_controle(self, client, utilisateur_secretaire, bdc_a_facturer):
        client.force_login(utilisateur_secretaire)
        from apps.bdc.models import BonDeCommande

        bdc_a_faire = BonDeCommande.objects.create(
            numero_bdc="RBAC-001",
            bailleur=bdc_a_facturer.bailleur,
            adresse="1 Rue RBAC",
            statut=StatutChoices.A_FAIRE,
            cree_par=bdc_a_facturer.cree_par,
        )
        resp = client.post(reverse("bdc:renvoyer_controle", kwargs={"pk": bdc_a_faire.pk}), {"commentaire": "Test"})
        assert resp.status_code == 302  # renvoi OK, redirect

    def test_cdt_can_access_valider_realisation(self, client, utilisateur_cdt, bdc_en_cours):
        client.force_login(utilisateur_cdt)
        resp = client.post(reverse("bdc:valider_realisation", kwargs={"pk": bdc_en_cours.pk}))
        assert resp.status_code == 302

    def test_cdt_can_access_valider_facturation(self, client, utilisateur_cdt, bdc_a_facturer):
        client.force_login(utilisateur_cdt)
        resp = client.post(reverse("bdc:valider_facturation", kwargs={"pk": bdc_a_facturer.pk}))
        assert resp.status_code == 302
