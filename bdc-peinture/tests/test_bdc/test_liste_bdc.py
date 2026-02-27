"""Tests de la vue liste_bdc : accès, filtres, recherche, pagination, compteurs."""
import pytest
from django.urls import reverse

from apps.bdc.models import BonDeCommande, StatutChoices

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

    def test_combinaison_statut_et_recherche(self, client, utilisateur_secretaire, bdc_a_traiter, bdc_a_faire, bdc_erilia_marseille):
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
