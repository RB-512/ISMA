import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

User = get_user_model()


@pytest.fixture
def client_cdt(client, utilisateur_cdt):
    client.force_login(utilisateur_cdt)
    return client


@pytest.fixture
def client_secretaire(client, utilisateur_secretaire):
    client.force_login(utilisateur_secretaire)
    return client


class TestListeUtilisateurs:
    def test_acces_cdt(self, client_cdt):
        resp = client_cdt.get(reverse("gestion:liste"))
        assert resp.status_code == 200

    def test_secretaire_can_access(self, client_secretaire):
        resp = client_secretaire.get(reverse("gestion:liste"))
        assert resp.status_code == 200

    def test_liste_affiche_utilisateurs(self, client_cdt, utilisateur_secretaire):
        resp = client_cdt.get(reverse("gestion:liste"))
        content = resp.content.decode()
        assert utilisateur_secretaire.get_full_name() in content or utilisateur_secretaire.email in content


class TestCreerUtilisateur:
    def test_creer_compte_valide(self, client_cdt):
        Group.objects.get_or_create(name="Secretaire")
        resp = client_cdt.post(
            reverse("gestion:creer"),
            {
                "username": "nouveau.user",
                "first_name": "Nouveau",
                "last_name": "User",
                "email": "nouveau@test.fr",
                "password1": "motdepasse123!",
                "password2": "motdepasse123!",
                "role": "Secretaire",
            },
        )
        assert resp.status_code == 302
        assert User.objects.filter(username="nouveau.user").exists()

    def test_creer_compte_groupe_assigne(self, client_cdt):
        Group.objects.get_or_create(name="CDT")
        client_cdt.post(
            reverse("gestion:creer"),
            {
                "username": "cdt.user",
                "first_name": "Chef",
                "last_name": "Travaux",
                "email": "chef@test.fr",
                "password1": "motdepasse123!",
                "password2": "motdepasse123!",
                "role": "CDT",
            },
        )
        user = User.objects.get(username="cdt.user")
        assert user.groups.filter(name="CDT").exists()

    def test_creer_formulaire_invalide_reaffiche(self, client_cdt):
        resp = client_cdt.post(reverse("gestion:creer"), {})
        assert resp.status_code == 200
        assert "form_creer" in resp.context


class TestModifierRole:
    def test_modifier_role_valide(self, client_cdt, utilisateur_secretaire):
        Group.objects.get_or_create(name="CDT")
        client_cdt.post(
            reverse("gestion:modifier_role", kwargs={"pk": utilisateur_secretaire.pk}),
            {"role": "CDT"},
        )
        utilisateur_secretaire.refresh_from_db()
        assert utilisateur_secretaire.groups.filter(name="CDT").exists()


class TestDesactiverUtilisateur:
    def test_desactiver_autre_utilisateur(self, client_cdt, utilisateur_secretaire):
        client_cdt.post(reverse("gestion:desactiver", kwargs={"pk": utilisateur_secretaire.pk}))
        utilisateur_secretaire.refresh_from_db()
        assert not utilisateur_secretaire.is_active

    def test_ne_peut_pas_se_desactiver_soi_meme(self, client_cdt, utilisateur_cdt):
        client_cdt.post(reverse("gestion:desactiver", kwargs={"pk": utilisateur_cdt.pk}))
        utilisateur_cdt.refresh_from_db()
        assert utilisateur_cdt.is_active  # inchangé
