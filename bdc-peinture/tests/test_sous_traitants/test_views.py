import pytest
from django.urls import reverse

from apps.sous_traitants.models import SousTraitant


@pytest.fixture
def sous_traitant_actif(db):
    return SousTraitant.objects.create(
        nom="Dupont Peinture",
        telephone="0612345678",
        email="dupont@test.fr",
        siret="12345678901234",
        adresse="10 rue Test",
        code_postal="84000",
        ville="Avignon",
    )


@pytest.fixture
def sous_traitant_inactif(db):
    return SousTraitant.objects.create(
        nom="Martin Inactif",
        telephone="0698765432",
        actif=False,
    )


# ─── Liste ──────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestListeSousTraitants:
    def test_cdt_can_access(self, client_cdt):
        resp = client_cdt.get(reverse("sous_traitants:list"))
        assert resp.status_code == 200

    def test_secretaire_can_access(self, client_secretaire):
        resp = client_secretaire.get(reverse("sous_traitants:list"))
        assert resp.status_code == 200

    def test_anonymous_redirected(self, client):
        resp = client.get(reverse("sous_traitants:list"))
        assert resp.status_code == 302

    def test_list_shows_active_and_inactive(self, client_cdt, sous_traitant_actif, sous_traitant_inactif):
        resp = client_cdt.get(reverse("sous_traitants:list"))
        content = resp.content.decode()
        assert "Dupont Peinture" in content
        assert "Martin Inactif" in content

    def test_search_by_nom(self, client_cdt, sous_traitant_actif, sous_traitant_inactif):
        resp = client_cdt.get(reverse("sous_traitants:list") + "?q=Dupont")
        content = resp.content.decode()
        assert "Dupont Peinture" in content
        assert "Martin Inactif" not in content

    def test_search_by_siret(self, client_cdt, sous_traitant_actif):
        resp = client_cdt.get(reverse("sous_traitants:list") + "?q=12345678")
        content = resp.content.decode()
        assert "Dupont Peinture" in content

    def test_search_by_ville(self, client_cdt, sous_traitant_actif):
        resp = client_cdt.get(reverse("sous_traitants:list") + "?q=Avignon")
        content = resp.content.decode()
        assert "Dupont Peinture" in content

    def test_search_empty_returns_all(self, client_cdt, sous_traitant_actif, sous_traitant_inactif):
        resp = client_cdt.get(reverse("sous_traitants:list") + "?q=")
        content = resp.content.decode()
        assert "Dupont Peinture" in content
        assert "Martin Inactif" in content

    def test_search_no_match(self, client_cdt, sous_traitant_actif):
        resp = client_cdt.get(reverse("sous_traitants:list") + "?q=ZZZZZ")
        content = resp.content.decode()
        assert "Dupont Peinture" not in content


# ─── Creer ──────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestCreerSousTraitant:
    def test_cdt_can_create(self, client_cdt):
        resp = client_cdt.post(
            reverse("sous_traitants:creer"),
            {"nom": "Nouveau ST", "telephone": "0611111111"},
        )
        assert resp.status_code == 302
        assert SousTraitant.objects.filter(nom="Nouveau ST").exists()

    def test_secretaire_cannot_create(self, client_secretaire):
        resp = client_secretaire.post(
            reverse("sous_traitants:creer"),
            {"nom": "Blocked ST", "telephone": "0622222222"},
        )
        assert resp.status_code == 403
        assert not SousTraitant.objects.filter(nom="Blocked ST").exists()

    def test_create_with_full_fields(self, client_cdt):
        resp = client_cdt.post(
            reverse("sous_traitants:creer"),
            {
                "nom": "ST Complet",
                "telephone": "0633333333",
                "email": "complet@test.fr",
                "siret": "98765432109876",
                "adresse": "5 av Test",
                "code_postal": "13001",
                "ville": "Marseille",
            },
        )
        assert resp.status_code == 302
        st = SousTraitant.objects.get(nom="ST Complet")
        assert st.siret == "98765432109876"
        assert st.ville == "Marseille"

    def test_create_invalid_form_rerenders(self, client_cdt):
        resp = client_cdt.post(
            reverse("sous_traitants:creer"),
            {"nom": "", "telephone": ""},  # nom is required
        )
        assert resp.status_code == 200  # re-renders the list page with errors

    def test_get_redirects_to_list(self, client_cdt):
        resp = client_cdt.get(reverse("sous_traitants:creer"))
        assert resp.status_code == 302


# ─── Modifier ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestModifierSousTraitant:
    def test_cdt_can_get_form(self, client_cdt, sous_traitant_actif):
        resp = client_cdt.get(reverse("sous_traitants:modifier", kwargs={"pk": sous_traitant_actif.pk}))
        assert resp.status_code == 200
        assert "form" in resp.context

    def test_cdt_can_modify(self, client_cdt, sous_traitant_actif):
        resp = client_cdt.post(
            reverse("sous_traitants:modifier", kwargs={"pk": sous_traitant_actif.pk}),
            {"nom": "Dupont Renove", "telephone": "0699999999"},
        )
        assert resp.status_code == 302
        sous_traitant_actif.refresh_from_db()
        assert sous_traitant_actif.nom == "Dupont Renove"

    def test_secretaire_cannot_modify(self, client_secretaire, sous_traitant_actif):
        resp = client_secretaire.post(
            reverse("sous_traitants:modifier", kwargs={"pk": sous_traitant_actif.pk}),
            {"nom": "Hacked", "telephone": "0600000000"},
        )
        assert resp.status_code == 403
        sous_traitant_actif.refresh_from_db()
        assert sous_traitant_actif.nom == "Dupont Peinture"  # unchanged

    def test_modify_nonexistent_returns_404(self, client_cdt):
        resp = client_cdt.get(reverse("sous_traitants:modifier", kwargs={"pk": 99999}))
        assert resp.status_code == 404


# ─── Desactiver / Reactiver ─────────────────────────────────────────────────────


@pytest.mark.django_db
class TestDesactiverReactiver:
    def test_cdt_can_deactivate(self, client_cdt, sous_traitant_actif):
        resp = client_cdt.post(reverse("sous_traitants:desactiver", kwargs={"pk": sous_traitant_actif.pk}))
        assert resp.status_code == 302
        sous_traitant_actif.refresh_from_db()
        assert sous_traitant_actif.actif is False

    def test_cdt_can_reactivate(self, client_cdt, sous_traitant_inactif):
        resp = client_cdt.post(reverse("sous_traitants:reactiver", kwargs={"pk": sous_traitant_inactif.pk}))
        assert resp.status_code == 302
        sous_traitant_inactif.refresh_from_db()
        assert sous_traitant_inactif.actif is True

    def test_secretaire_cannot_deactivate(self, client_secretaire, sous_traitant_actif):
        resp = client_secretaire.post(reverse("sous_traitants:desactiver", kwargs={"pk": sous_traitant_actif.pk}))
        assert resp.status_code == 403
        sous_traitant_actif.refresh_from_db()
        assert sous_traitant_actif.actif is True  # unchanged

    def test_secretaire_cannot_reactivate(self, client_secretaire, sous_traitant_inactif):
        resp = client_secretaire.post(reverse("sous_traitants:reactiver", kwargs={"pk": sous_traitant_inactif.pk}))
        assert resp.status_code == 403
        sous_traitant_inactif.refresh_from_db()
        assert sous_traitant_inactif.actif is False  # unchanged

    def test_get_desactiver_redirects_without_change(self, client_cdt, sous_traitant_actif):
        resp = client_cdt.get(reverse("sous_traitants:desactiver", kwargs={"pk": sous_traitant_actif.pk}))
        assert resp.status_code == 302
        sous_traitant_actif.refresh_from_db()
        assert sous_traitant_actif.actif is True  # GET does not deactivate
