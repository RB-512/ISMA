"""Tests de la vue liste_bdc : accès, filtres, recherche, pagination, compteurs."""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.bdc.models import BonDeCommande, LignePrestation, StatutChoices

pytestmark = pytest.mark.django_db


@pytest.fixture
def bdc_erilia_marseille(bailleur_erilia, utilisateur_secretaire):
    return BonDeCommande.objects.create(
        numero_bdc="ERI-100",
        bailleur=bailleur_erilia,
        adresse="10 Boulevard Michelet",
        ville="Marseille",
        occupant_nom="Dupont Jean",
        cree_par=utilisateur_secretaire,
        statut=StatutChoices.EN_COURS,
    )


# ─── Tests accès ─────────────────────────────────────────────────────────────


class TestListeBDCAcces:
    def test_acces_authentifie(self, client, utilisateur_secretaire):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:index"))
        assert response.status_code == 200

    def test_acces_cdt_autorise(self, client, utilisateur_cdt):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:index"))
        assert response.status_code == 200

    def test_non_authentifie_redirige(self, client):
        response = client.get(reverse("bdc:index"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_liste_vide(self, client, utilisateur_secretaire):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:index"))
        assert response.status_code == 200
        assert "Aucun bon de commande" in response.content.decode()

    def test_liste_avec_donnees(self, client, utilisateur_secretaire, bdc_a_traiter):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:index"))
        assert response.status_code == 200
        assert bdc_a_traiter.numero_bdc in response.content.decode()


# ─── Tests pagination ────────────────────────────────────────────────────────


class TestListeBDCPagination:
    def test_pagination_page_2(self, client, utilisateur_secretaire, bailleur_gdh):
        # Créer 30 BDC pour dépasser la pagination de 25
        for i in range(30):
            BonDeCommande.objects.create(
                numero_bdc=f"PAG-{i:03d}",
                bailleur=bailleur_gdh,
                adresse=f"{i} Rue Pagination",
                cree_par=utilisateur_secretaire,
                statut=StatutChoices.A_TRAITER,
            )

        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:index"), {"page": 2})
        assert response.status_code == 200
        # Page 2 should have 5 results (30 - 25)
        page_obj = response.context["page_obj"]
        assert page_obj.number == 2
        assert len(page_obj) == 5


# ─── Tests filtres ───────────────────────────────────────────────────────────


class TestListeBDCFiltres:
    def test_filtre_statut(self, client, utilisateur_secretaire, bdc_a_traiter, bdc_a_faire):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:index"), {"statut": "A_FAIRE"})
        content = response.content.decode()
        assert bdc_a_faire.numero_bdc in content
        assert bdc_a_traiter.numero_bdc not in content

    def test_filtre_bailleur(self, client, utilisateur_secretaire, bdc_a_traiter, bdc_erilia_marseille):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:index"), {"bailleur": bdc_erilia_marseille.bailleur.pk})
        content = response.content.decode()
        assert bdc_erilia_marseille.numero_bdc in content
        assert bdc_a_traiter.numero_bdc not in content

    def test_filtre_ville(self, client, utilisateur_secretaire, bdc_a_traiter, bdc_erilia_marseille):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:index"), {"ville": "Marseille"})
        content = response.content.decode()
        assert bdc_erilia_marseille.numero_bdc in content
        assert bdc_a_traiter.numero_bdc not in content

    def test_filtre_date_du(self, client, utilisateur_secretaire, bdc_a_traiter):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:index"), {"date_du": "2020-01-01"})
        content = response.content.decode()
        assert bdc_a_traiter.numero_bdc in content

    def test_filtre_date_au_exclut(self, client, utilisateur_secretaire, bdc_a_traiter):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:index"), {"date_au": "2020-01-01"})
        content = response.content.decode()
        assert bdc_a_traiter.numero_bdc not in content

    def test_recherche_numero_bdc(self, client, utilisateur_secretaire, bdc_a_traiter, bdc_erilia_marseille):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:index"), {"q": "ERI-100"})
        content = response.content.decode()
        assert bdc_erilia_marseille.numero_bdc in content
        assert bdc_a_traiter.numero_bdc not in content

    def test_recherche_adresse(self, client, utilisateur_secretaire, bdc_a_traiter, bdc_erilia_marseille):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:index"), {"q": "Boulevard Michelet"})
        content = response.content.decode()
        assert bdc_erilia_marseille.numero_bdc in content
        assert bdc_a_traiter.numero_bdc not in content

    def test_recherche_occupant(self, client, utilisateur_secretaire, bdc_a_traiter, bdc_erilia_marseille):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:index"), {"q": "Dupont"})
        content = response.content.decode()
        assert bdc_erilia_marseille.numero_bdc in content

    def test_recherche_sans_resultat(self, client, utilisateur_secretaire, bdc_a_traiter):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:index"), {"q": "XXXXNOTFOUND"})
        content = response.content.decode()
        assert "Aucun bon de commande" in content

    def test_combinaison_statut_et_recherche(
        self, client, utilisateur_secretaire, bdc_a_traiter, bdc_a_faire, bdc_erilia_marseille
    ):
        client.force_login(utilisateur_secretaire)
        # A_TRAITER + recherche "François" (bdc_a_traiter adresse = "3 Rue François 1er")
        response = client.get(reverse("bdc:index"), {"statut": "A_TRAITER", "q": "François"})
        content = response.content.decode()
        assert bdc_a_traiter.numero_bdc in content
        assert bdc_a_faire.numero_bdc not in content
        assert bdc_erilia_marseille.numero_bdc not in content


# ─── Tests compteurs ─────────────────────────────────────────────────────────


class TestListeBDCCompteurs:
    def test_compteurs_dans_context(self, client, utilisateur_secretaire, bdc_a_traiter, bdc_a_faire):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:index"))
        assert response.context["total"] == 2
        compteurs = response.context["compteurs"]
        assert compteurs.get("A_TRAITER") == 1
        assert compteurs.get("A_FAIRE") == 1

    def test_compteurs_base_vide(self, client, utilisateur_secretaire):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:index"))
        assert response.context["total"] == 0


# ─── Tests queryset optimisations ───────────────────────────────────────────


class TestListeBDCQueryset:
    def test_liste_bdc_includes_sous_traitant_and_montant(self, client, bdc_a_traiter, utilisateur_secretaire):
        """Dashboard queryset includes sous_traitant and montant_ht_total annotation."""
        # Create a prestation line so the annotation has data
        LignePrestation.objects.create(
            bdc=bdc_a_traiter,
            designation="Peinture murs",
            quantite=Decimal("10.00"),
            unite="m2",
            prix_unitaire=Decimal("12.50"),
            montant=Decimal("125.00"),
            ordre=0,
        )

        client.force_login(utilisateur_secretaire)
        resp = client.get(reverse("bdc:index"))

        assert resp.status_code == 200
        bdc = resp.context["page_obj"][0]

        # sous_traitant should be accessible without extra query
        assert hasattr(bdc, "sous_traitant")

        # montant_ht_total annotation should be present
        assert hasattr(bdc, "montant_ht_total")
        assert bdc.montant_ht_total == Decimal("125.00")


# ─── Tests sidebar detail ──────────────────────────────────────────────────


class TestDetailSidebar:
    def test_detail_sidebar_returns_partial(self, client, bdc_a_traiter, utilisateur_secretaire):
        """Sidebar endpoint returns partial HTML without base layout."""
        client.force_login(utilisateur_secretaire)
        resp = client.get(reverse("bdc:detail_sidebar", args=[bdc_a_traiter.pk]))
        assert resp.status_code == 200
        content = resp.content.decode()
        assert bdc_a_traiter.numero_bdc in content
        # Should not contain full base template markers
        assert "<html" not in content.lower()

    def test_detail_sidebar_requires_login(self, client, bdc_a_traiter):
        resp = client.get(reverse("bdc:detail_sidebar", args=[bdc_a_traiter.pk]))
        assert resp.status_code == 302


# ─── Tests tab filtering integration ────────────────────────────────────────


class TestTabFiltering:
    def test_tab_filtering_by_statut(self, client, bdc_a_traiter, utilisateur_secretaire):
        """Filtering by statut via query param returns only matching BDCs."""
        client.force_login(utilisateur_secretaire)
        resp = client.get(reverse("bdc:index") + "?statut=A_TRAITER")
        assert resp.status_code == 200
        for bdc in resp.context["page_obj"]:
            assert bdc.statut == "A_TRAITER"


# ─── Tests sidebar save and transition ─────────────────────────────────────


class TestSidebarSaveAndTransition:
    def test_post_saves_fields_returns_partial(self, client, utilisateur_secretaire, bdc_a_traiter):
        """POST sidebar_action saves fields and returns partial HTML."""
        client.force_login(utilisateur_secretaire)
        resp = client.post(
            reverse("bdc:sidebar_action", args=[bdc_a_traiter.pk]),
            {"occupation": "OCCUPE", "type_acces": "BADGE_CODE", "rdv_date": "2026-03-15T10:00", "notes": "Test"},
        )
        assert resp.status_code == 200
        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.occupation == "OCCUPE"
        assert bdc_a_traiter.type_acces == "BADGE_CODE"
        assert bdc_a_traiter.notes == "Test"
        # Should be partial HTML
        content = resp.content.decode()
        assert "<html" not in content.lower()
        assert bdc_a_traiter.numero_bdc in content

    def test_post_with_transition_changes_status(self, client, utilisateur_secretaire, bdc_a_traiter):
        """POST sidebar_action with nouveau_statut triggers transition."""
        client.force_login(utilisateur_secretaire)
        resp = client.post(
            reverse("bdc:sidebar_action", args=[bdc_a_traiter.pk]),
            {
                "occupation": "VACANT",
                "type_acces": "BADGE_CODE",
                "acces_complement": "Code 1234",
                "nouveau_statut": "A_FAIRE",
            },
        )
        assert resp.status_code == 200
        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.statut == StatutChoices.A_FAIRE

    def test_post_with_invalid_transition_returns_error(self, client, utilisateur_secretaire, bdc_a_traiter):
        """POST sidebar_action with invalid transition returns sidebar with error."""
        client.force_login(utilisateur_secretaire)
        resp = client.post(
            reverse("bdc:sidebar_action", args=[bdc_a_traiter.pk]),
            {
                "occupation": "VACANT",
                "type_acces": "BADGE_CODE",
                "acces_complement": "Code 1234",
                "nouveau_statut": "EN_COURS",  # invalid from A_TRAITER
            },
        )
        assert resp.status_code == 200
        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.statut == StatutChoices.A_TRAITER  # unchanged

    def test_response_contains_hx_trigger(self, client, utilisateur_secretaire, bdc_a_traiter):
        """Response contains HX-Trigger: bdc-updated header."""
        client.force_login(utilisateur_secretaire)
        resp = client.post(
            reverse("bdc:sidebar_action", args=[bdc_a_traiter.pk]),
            {"occupation": "VACANT", "notes": "test"},
        )
        assert resp.status_code == 200
        assert resp["HX-Trigger"] == "bdc-updated"

    def test_requires_secretaire(self, client, utilisateur_cdt, bdc_a_traiter):
        """Only Secretaire group can access sidebar_action."""
        client.force_login(utilisateur_cdt)
        resp = client.post(
            reverse("bdc:sidebar_action", args=[bdc_a_traiter.pk]),
            {"occupation": "VACANT"},
        )
        assert resp.status_code == 403

    def test_get_redirects(self, client, utilisateur_secretaire, bdc_a_traiter):
        """GET sidebar_action redirects to detail."""
        client.force_login(utilisateur_secretaire)
        resp = client.get(reverse("bdc:sidebar_action", args=[bdc_a_traiter.pk]))
        assert resp.status_code == 302
