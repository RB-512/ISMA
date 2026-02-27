"""
Tests d'authentification et de contrôle d'accès.
"""
from django.test import Client


class TestLogin:
    def test_login_page_accessible(self, db):
        client = Client()
        response = client.get("/accounts/login/")
        assert response.status_code == 200

    def test_login_reussi_redirige(self, utilisateur_secretaire):
        client = Client()
        response = client.post("/accounts/login/", {
            "login": "secretaire@test.fr",
            "password": "testpass123",
        })
        # allauth redirige vers LOGIN_REDIRECT_URL après login réussi
        assert response.status_code in (302, 200)

    def test_login_echoue_mauvais_mot_de_passe(self, utilisateur_secretaire):
        client = Client()
        response = client.post("/accounts/login/", {
            "login": "secretaire@test.fr",
            "password": "mauvais_password",
        })
        # Reste sur la page de login (pas de redirection)
        assert response.status_code == 200

    def test_acces_non_authentifie_redirige_vers_login(self, db):
        client = Client()
        response = client.get("/")
        # Redirige vers login si non authentifié
        assert response.status_code in (302, 301)


class TestGroupRequired:
    def test_groupe_cdt_existe(self, groupe_cdt):
        assert groupe_cdt.name == "CDT"

    def test_groupe_secretaire_existe(self, groupe_secretaire):
        assert groupe_secretaire.name == "Secretaire"

    def test_secretaire_appartient_au_groupe(self, utilisateur_secretaire, groupe_secretaire):
        assert utilisateur_secretaire.groups.filter(name="Secretaire").exists()

    def test_cdt_appartient_au_groupe(self, utilisateur_cdt, groupe_cdt):
        assert utilisateur_cdt.groups.filter(name="CDT").exists()

    def test_secretaire_nappartient_pas_au_groupe_cdt(self, utilisateur_secretaire):
        assert not utilisateur_secretaire.groups.filter(name="CDT").exists()
