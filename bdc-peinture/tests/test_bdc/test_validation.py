"""
Tests unitaires — validation réalisation, facturation, retour, vues CDT,
boutons template et recoupement par sous-traitant.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.bdc.models import BonDeCommande, HistoriqueAction, StatutChoices
from apps.bdc.services import (
    BDCIncomplet,
    TransitionInvalide,
    changer_statut,
    valider_facturation,
    valider_realisation,
)

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


DATE_INTERVENTION = date(2026, 2, 18)
DATE_FACTURE = date(2026, 3, 2)
SAISIE_REALISATION = {"date_intervention": "2026-02-18"}
SAISIE_FACTURATION = {"numero_facture": "FA-2026-001", "date_facturation": "2026-03-02"}

# ─── 6.1 Tests valider_realisation ──────────────────────────────────────────


class TestValiderRealisation:
    def test_transition_ok(self, bdc_en_cours, utilisateur_cdt):
        bdc = valider_realisation(bdc_en_cours, utilisateur_cdt, DATE_INTERVENTION)
        assert bdc.statut == StatutChoices.A_FACTURER

    def test_date_realisation_vaut_date_saisie(self, bdc_en_cours, utilisateur_cdt):
        bdc = valider_realisation(bdc_en_cours, utilisateur_cdt, DATE_INTERVENTION)
        bdc.refresh_from_db()
        assert bdc.date_realisation == DATE_INTERVENTION

    def test_date_du_jour_acceptee(self, bdc_en_cours, utilisateur_cdt):
        bdc = valider_realisation(bdc_en_cours, utilisateur_cdt, date.today())
        assert bdc.date_realisation == date.today()

    def test_historique_validation_cree(self, bdc_en_cours, utilisateur_cdt):
        valider_realisation(bdc_en_cours, utilisateur_cdt, DATE_INTERVENTION)
        action = HistoriqueAction.objects.filter(bdc=bdc_en_cours, action="VALIDATION").first()
        assert action is not None
        assert action.details["date_realisation"] == str(DATE_INTERVENTION)

    def test_refus_sans_date(self, bdc_en_cours, utilisateur_cdt):
        with pytest.raises(BDCIncomplet, match="obligatoire"):
            valider_realisation(bdc_en_cours, utilisateur_cdt, None)
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.EN_COURS
        assert bdc_en_cours.date_realisation is None

    def test_refus_date_future(self, bdc_en_cours, utilisateur_cdt):
        with pytest.raises(BDCIncomplet, match="futur"):
            valider_realisation(bdc_en_cours, utilisateur_cdt, date.today() + timedelta(days=1))
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.EN_COURS

    def test_refus_si_pas_en_cours(self, bdc_a_facturer, utilisateur_cdt):
        with pytest.raises(TransitionInvalide, match="En cours"):
            valider_realisation(bdc_a_facturer, utilisateur_cdt, DATE_INTERVENTION)

    def test_refus_si_a_traiter(self, bdc_a_traiter, utilisateur_cdt):
        with pytest.raises(TransitionInvalide):
            valider_realisation(bdc_a_traiter, utilisateur_cdt, DATE_INTERVENTION)


# ─── 6.2 Tests valider_facturation ──────────────────────────────────────────


class TestValiderFacturation:
    def test_transition_ok(self, bdc_a_facturer, utilisateur_cdt):
        bdc = valider_facturation(bdc_a_facturer, utilisateur_cdt, "FA-2026-001", DATE_FACTURE)
        bdc.refresh_from_db()
        assert bdc.statut == StatutChoices.FACTURE
        assert bdc.numero_facture == "FA-2026-001"
        assert bdc.date_facturation == DATE_FACTURE

    def test_numero_normalise(self, bdc_a_facturer, utilisateur_cdt):
        bdc = valider_facturation(bdc_a_facturer, utilisateur_cdt, "  FA-7  ", DATE_FACTURE)
        assert bdc.numero_facture == "FA-7"

    def test_historique_facturation_cree(self, bdc_a_facturer, utilisateur_cdt):
        valider_facturation(bdc_a_facturer, utilisateur_cdt, "FA-2026-001", DATE_FACTURE)
        action = HistoriqueAction.objects.filter(bdc=bdc_a_facturer, action="FACTURATION").first()
        assert action is not None
        assert action.details == {"numero_facture": "FA-2026-001", "date_facturation": str(DATE_FACTURE)}

    @pytest.mark.parametrize(
        ("numero", "date_facture", "message"),
        [
            ("", DATE_FACTURE, "n° de facture est obligatoire"),
            ("   ", DATE_FACTURE, "n° de facture est obligatoire"),
            ("FA-1", None, "date de facturation est obligatoire"),
            ("FA-1", date.today() + timedelta(days=1), "futur"),
            ("FA-1", date(2026, 2, 19), "précéder la date d'intervention"),
        ],
    )
    def test_refus_saisie_invalide(self, bdc_a_facturer, utilisateur_cdt, numero, date_facture, message):
        with pytest.raises(BDCIncomplet, match=message):
            valider_facturation(bdc_a_facturer, utilisateur_cdt, numero, date_facture)
        bdc_a_facturer.refresh_from_db()
        assert bdc_a_facturer.statut == StatutChoices.A_FACTURER
        assert bdc_a_facturer.numero_facture == ""

    def test_date_facture_egale_intervention_acceptee(self, bdc_a_facturer, utilisateur_cdt):
        bdc = valider_facturation(bdc_a_facturer, utilisateur_cdt, "FA-1", bdc_a_facturer.date_realisation)
        assert bdc.statut == StatutChoices.FACTURE

    def test_refus_numero_deja_utilise(self, bdc_a_facturer, utilisateur_cdt):
        BonDeCommande.objects.create(
            numero_bdc="VAL-DEJA",
            bailleur=bdc_a_facturer.bailleur,
            adresse="1 Rue Doublon",
            statut=StatutChoices.FACTURE,
            numero_facture="FA-2026-001",
            cree_par=utilisateur_cdt,
        )
        with pytest.raises(BDCIncomplet, match="VAL-DEJA"):
            valider_facturation(bdc_a_facturer, utilisateur_cdt, "FA-2026-001", DATE_FACTURE)
        bdc_a_facturer.refresh_from_db()
        assert bdc_a_facturer.statut == StatutChoices.A_FACTURER

    def test_refus_si_pas_a_facturer(self, bdc_en_cours, utilisateur_cdt):
        with pytest.raises(TransitionInvalide, match="À facturer"):
            valider_facturation(bdc_en_cours, utilisateur_cdt, "FA-1", DATE_FACTURE)


class TestContrainteNumeroFacture:
    def test_plusieurs_bdc_sans_numero_autorises(self, bdc_en_cours, bdc_a_facturer):
        assert bdc_en_cours.numero_facture == bdc_a_facturer.numero_facture == ""

    def test_doublon_refuse_en_base(self, bdc_en_cours, bdc_a_facturer):
        from django.db import IntegrityError, transaction

        bdc_en_cours.numero_facture = "FA-X"
        bdc_en_cours.save()
        bdc_a_facturer.numero_facture = "FA-X"
        with pytest.raises(IntegrityError), transaction.atomic():
            bdc_a_facturer.save()

    def test_saisie_simultanee_meme_numero(self, bdc_en_cours, bdc_a_facturer, utilisateur_cdt):
        """Un autre utilisateur enregistre le même n° entre le contrôle et l'écriture : la base tranche."""
        from unittest import mock

        bdc_en_cours.numero_facture = "FA-COURSE"
        bdc_en_cours.save()
        aucun_doublon = BonDeCommande.objects.none()
        # Le contrôle préalable ne voit pas encore le doublon (fenêtre de course)
        with (
            mock.patch.object(BonDeCommande.objects, "filter", return_value=aucun_doublon),
            pytest.raises(BDCIncomplet, match="déjà utilisé par un autre BDC"),
        ):
            valider_facturation(bdc_a_facturer, utilisateur_cdt, "FA-COURSE", DATE_FACTURE)

        bdc_a_facturer.refresh_from_db()
        assert bdc_a_facturer.statut == StatutChoices.A_FACTURER
        assert bdc_a_facturer.numero_facture == ""
        assert not HistoriqueAction.objects.filter(bdc=bdc_a_facturer, action="FACTURATION").exists()


class TestChangerStatutGeneriqueBloque:
    def test_en_cours_vers_a_facturer_refuse(self, bdc_en_cours, utilisateur_cdt):
        with pytest.raises(BDCIncomplet, match="date d'intervention"):
            changer_statut(bdc_en_cours, StatutChoices.A_FACTURER, utilisateur_cdt)
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.EN_COURS

    def test_a_facturer_vers_facture_refuse(self, bdc_a_facturer, utilisateur_cdt):
        with pytest.raises(BDCIncomplet, match="facture"):
            changer_statut(bdc_a_facturer, StatutChoices.FACTURE, utilisateur_cdt)
        bdc_a_facturer.refresh_from_db()
        assert bdc_a_facturer.statut == StatutChoices.A_FACTURER


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
        response = client.post(reverse("bdc:valider_realisation", kwargs={"pk": bdc_en_cours.pk}), SAISIE_REALISATION)
        assert response.status_code == 302
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.A_FACTURER

    def test_get_redirige(self, client, utilisateur_cdt, bdc_en_cours):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:valider_realisation", kwargs={"pk": bdc_en_cours.pk}))
        assert response.status_code == 302

    def test_secretaire_can_access(self, client, utilisateur_secretaire, bdc_en_cours):
        client.force_login(utilisateur_secretaire)
        response = client.post(reverse("bdc:valider_realisation", kwargs={"pk": bdc_en_cours.pk}), SAISIE_REALISATION)
        assert response.status_code == 302
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.A_FACTURER


class TestVueValiderFacturation:
    def test_post_cdt_ok(self, client, utilisateur_cdt, bdc_a_facturer):
        client.force_login(utilisateur_cdt)
        response = client.post(
            reverse("bdc:valider_facturation", kwargs={"pk": bdc_a_facturer.pk}), SAISIE_FACTURATION
        )
        assert response.status_code == 302
        bdc_a_facturer.refresh_from_db()
        assert bdc_a_facturer.statut == StatutChoices.FACTURE

    def test_get_redirige(self, client, utilisateur_cdt, bdc_a_facturer):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:valider_facturation", kwargs={"pk": bdc_a_facturer.pk}))
        assert response.status_code == 302

    def test_secretaire_can_access(self, client, utilisateur_secretaire, bdc_a_facturer):
        client.force_login(utilisateur_secretaire)
        response = client.post(
            reverse("bdc:valider_facturation", kwargs={"pk": bdc_a_facturer.pk}), SAISIE_FACTURATION
        )
        assert response.status_code == 302
        bdc_a_facturer.refresh_from_db()
        assert bdc_a_facturer.statut == StatutChoices.FACTURE


class TestVueSaisieInvalide:
    def test_realisation_sans_date_reste_en_cours(self, client, utilisateur_cdt, bdc_en_cours):
        client.force_login(utilisateur_cdt)
        response = client.post(reverse("bdc:valider_realisation", kwargs={"pk": bdc_en_cours.pk}), follow=True)
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.EN_COURS
        assert "intervention est obligatoire" in response.content.decode()

    def test_realisation_date_illisible_refusee(self, client, utilisateur_cdt, bdc_en_cours):
        client.force_login(utilisateur_cdt)
        client.post(
            reverse("bdc:valider_realisation", kwargs={"pk": bdc_en_cours.pk}), {"date_intervention": "pas-une-date"}
        )
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.EN_COURS

    def test_facturation_htmx_erreur_reaffiche_panneau(self, client, utilisateur_cdt, bdc_a_facturer):
        client.force_login(utilisateur_cdt)
        response = client.post(
            reverse("bdc:valider_facturation", kwargs={"pk": bdc_a_facturer.pk}),
            {"numero_facture": "FA-9", "date_facturation": "2026-01-01"},
            HTTP_HX_REQUEST="true",
        )
        content = response.content.decode()
        bdc_a_facturer.refresh_from_db()
        assert bdc_a_facturer.statut == StatutChoices.A_FACTURER
        assert "précéder la date" in content
        assert 'value="FA-9"' in content
        assert 'value="2026-01-01"' in content


# ─── 6.5 Tests template detail — boutons conditionnels ─────────────────────


class TestFicheDetailSaisie:
    def test_formulaire_realisation_demande_la_date(self, client, utilisateur_cdt, bdc_en_cours):
        client.force_login(utilisateur_cdt)
        content = client.get(reverse("bdc:detail", kwargs={"pk": bdc_en_cours.pk})).content.decode()
        assert f'action="{reverse("bdc:valider_realisation", kwargs={"pk": bdc_en_cours.pk})}"' in content
        assert 'name="date_intervention"' in content
        assert f'max="{date.today().isoformat()}"' in content

    def test_formulaire_facturation_demande_numero_et_date(self, client, utilisateur_cdt, bdc_a_facturer):
        client.force_login(utilisateur_cdt)
        content = client.get(reverse("bdc:detail", kwargs={"pk": bdc_a_facturer.pk})).content.decode()
        assert f'action="{reverse("bdc:valider_facturation", kwargs={"pk": bdc_a_facturer.pk})}"' in content
        assert 'name="numero_facture"' in content
        assert 'name="date_facturation"' in content
        assert 'min="2026-02-20"' in content

    def test_soumission_depuis_la_fiche(self, client, utilisateur_cdt, bdc_en_cours):
        client.force_login(utilisateur_cdt)
        response = client.post(
            reverse("bdc:valider_realisation", kwargs={"pk": bdc_en_cours.pk}), SAISIE_REALISATION, follow=True
        )
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.A_FACTURER
        assert bdc_en_cours.date_realisation == DATE_INTERVENTION
        assert "réalisation validée" in response.content.decode()


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
    """Verify RBAC: Secretaire can perform final workflow transitions, CDT-only actions remain blocked."""

    def test_secretaire_peut_valider_realisation(self, client, utilisateur_secretaire, bdc_en_cours):
        client.force_login(utilisateur_secretaire)
        resp = client.post(reverse("bdc:valider_realisation", kwargs={"pk": bdc_en_cours.pk}), SAISIE_REALISATION)
        assert resp.status_code == 302
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.A_FACTURER

    def test_secretaire_peut_valider_facturation(self, client, utilisateur_secretaire, bdc_a_facturer):
        client.force_login(utilisateur_secretaire)
        resp = client.post(reverse("bdc:valider_facturation", kwargs={"pk": bdc_a_facturer.pk}), SAISIE_FACTURATION)
        assert resp.status_code == 302
        bdc_a_facturer.refresh_from_db()
        assert bdc_a_facturer.statut == StatutChoices.FACTURE

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
        resp = client.post(reverse("bdc:valider_realisation", kwargs={"pk": bdc_en_cours.pk}), SAISIE_REALISATION)
        assert resp.status_code == 302

    def test_cdt_can_access_valider_facturation(self, client, utilisateur_cdt, bdc_a_facturer):
        client.force_login(utilisateur_cdt)
        resp = client.post(reverse("bdc:valider_facturation", kwargs={"pk": bdc_a_facturer.pk}), SAISIE_FACTURATION)
        assert resp.status_code == 302


# ─── Panneau de saisie (sidebar) et colonnes du tableau de bord ─────────────


class TestPanneauSaisieSidebar:
    def test_panneau_realisation_prerempli_aujourdhui(self, client, utilisateur_cdt, bdc_en_cours):
        client.force_login(utilisateur_cdt)
        url = reverse("bdc:sidebar_checklist", kwargs={"pk": bdc_en_cours.pk})
        content = client.get(url + "?transition=EN_COURS__A_FACTURER").content.decode()
        assert 'name="date_intervention"' in content
        assert f'value="{date.today().isoformat()}"' in content

    def test_panneau_facturation_demande_numero_et_date(self, client, utilisateur_cdt, bdc_a_facturer):
        client.force_login(utilisateur_cdt)
        url = reverse("bdc:sidebar_checklist", kwargs={"pk": bdc_a_facturer.pk})
        content = client.get(url + "?transition=A_FACTURER__FACTURE").content.decode()
        assert 'name="numero_facture"' in content
        assert 'name="date_facturation"' in content
        assert 'min="2026-02-20"' in content

    def test_post_panneau_sans_date_bloque(self, client, utilisateur_cdt, bdc_en_cours):
        client.force_login(utilisateur_cdt)
        url = reverse("bdc:sidebar_checklist", kwargs={"pk": bdc_en_cours.pk})
        response = client.post(url, {"transition": "EN_COURS__A_FACTURER"}, HTTP_HX_REQUEST="true")
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.EN_COURS
        assert "intervention est obligatoire" in response.content.decode()


class TestColonnesTableauDeBord:
    def test_affiche_intervention_et_facture(self, client, utilisateur_cdt, bdc_a_facturer):
        valider_facturation(bdc_a_facturer, utilisateur_cdt, "FA-2026-042", DATE_FACTURE)
        client.force_login(utilisateur_cdt)
        content = client.get(reverse("bdc:index")).content.decode()
        assert "Intervention" in content
        assert "20/02/2026" in content
        assert "FA-2026-042" in content
        assert "02/03/2026" in content

    def test_tiret_si_pas_encore_realise(self, client, utilisateur_cdt, bdc_en_cours):
        client.force_login(utilisateur_cdt)
        content = client.get(reverse("bdc:index")).content.decode()
        assert bdc_en_cours.numero_bdc in content
        assert "FA-" not in content
