"""
Tests complets pour la gestion des utilisateurs (forms + views).
Couvre : creation avec email/allauth, modification, reset password,
desactivation, reactivation, controle d'acces RBAC.
"""

import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from apps.accounts.forms import CreerUtilisateurForm, ModifierUtilisateurForm
from apps.bdc.models import Bailleur, BonDeCommande

User = get_user_model()


# ─── Fixtures locales ────────────────────────────────────────────────────────


@pytest.fixture
def groupe_secretaire_accent(db):
    """Le groupe 'Secrétaire' (avec accent) utilisé par les forms ROLE_CHOICES."""
    group, _ = Group.objects.get_or_create(name="Secretaire")
    return group


@pytest.fixture
def client_cdt(client, utilisateur_cdt):
    client.force_login(utilisateur_cdt)
    return client


@pytest.fixture
def client_secretaire(client, utilisateur_secretaire):
    client.force_login(utilisateur_secretaire)
    return client


# ── Form Tests : CreerUtilisateurForm ────────────────────────────────────────


@pytest.mark.django_db
class TestCreerUtilisateurForm:
    def test_valid_form_creates_user_and_email_address(self, groupe_secretaire_accent):
        form = CreerUtilisateurForm(
            data={
                "username": "jean.dupont",
                "first_name": "Jean",
                "last_name": "Dupont",
                "email": "jean@example.com",
                "password1": "motdepasse123!",
                "password2": "motdepasse123!",
                "role": "Secretaire",
            }
        )
        assert form.is_valid(), form.errors
        user = form.save()

        assert user.pk is not None
        assert user.email == "jean@example.com"
        assert user.first_name == "Jean"
        assert user.groups.filter(name="Secretaire").exists()

        email_addr = EmailAddress.objects.get(user=user)
        assert email_addr.email == "jean@example.com"
        assert email_addr.verified is True
        assert email_addr.primary is True

    def test_duplicate_email_rejected(self, groupe_secretaire_accent):
        User.objects.create_user(username="existing", email="taken@example.com", password="pass123!")
        form = CreerUtilisateurForm(
            data={
                "username": "nouveau",
                "first_name": "Nouveau",
                "last_name": "User",
                "email": "taken@example.com",
                "password1": "motdepasse123!",
                "password2": "motdepasse123!",
                "role": "Secretaire",
            }
        )
        assert not form.is_valid()
        assert "email" in form.errors

    def test_email_required(self, groupe_secretaire_accent):
        form = CreerUtilisateurForm(
            data={
                "username": "sans.email",
                "first_name": "Sans",
                "last_name": "Email",
                "email": "",
                "password1": "motdepasse123!",
                "password2": "motdepasse123!",
                "role": "Secretaire",
            }
        )
        assert not form.is_valid()
        assert "email" in form.errors


# ── Form Tests : ModifierUtilisateurForm ─────────────────────────────────────


@pytest.mark.django_db
class TestModifierUtilisateurForm:
    def test_valid_modification_updates_user(self, utilisateur_secretaire, groupe_secretaire_accent):
        EmailAddress.objects.create(
            user=utilisateur_secretaire, email=utilisateur_secretaire.email, verified=True, primary=True
        )
        form = ModifierUtilisateurForm(
            data={
                "username": utilisateur_secretaire.username,
                "first_name": "Sophie Modifiee",
                "last_name": "Martin Modifiee",
                "email": "sophie.new@example.com",
                "role": "Secretaire",
            },
            instance=utilisateur_secretaire,
        )
        assert form.is_valid(), form.errors
        user = form.save()

        user.refresh_from_db()
        assert user.first_name == "Sophie Modifiee"
        assert user.last_name == "Martin Modifiee"
        assert user.email == "sophie.new@example.com"

    def test_email_sync_allauth(self, utilisateur_secretaire, groupe_secretaire_accent):
        EmailAddress.objects.create(
            user=utilisateur_secretaire, email=utilisateur_secretaire.email, verified=True, primary=True
        )
        form = ModifierUtilisateurForm(
            data={
                "username": utilisateur_secretaire.username,
                "first_name": "Sophie",
                "last_name": "Martin",
                "email": "sophie.updated@example.com",
                "role": "Secretaire",
            },
            instance=utilisateur_secretaire,
        )
        assert form.is_valid()
        form.save()

        allauth_email = EmailAddress.objects.get(user=utilisateur_secretaire, primary=True)
        assert allauth_email.email == "sophie.updated@example.com"

    def test_email_sync_allauth_creates_if_missing(self, utilisateur_secretaire, groupe_secretaire_accent):
        """If no EmailAddress exists yet, save() creates one."""
        form = ModifierUtilisateurForm(
            data={
                "username": utilisateur_secretaire.username,
                "first_name": "Sophie",
                "last_name": "Martin",
                "email": "new@example.com",
                "role": "Secretaire",
            },
            instance=utilisateur_secretaire,
        )
        assert form.is_valid()
        form.save()

        assert EmailAddress.objects.filter(user=utilisateur_secretaire, email="new@example.com", primary=True).exists()

    def test_duplicate_email_rejected(self, utilisateur_secretaire, utilisateur_cdt, groupe_secretaire_accent):
        form = ModifierUtilisateurForm(
            data={
                "username": utilisateur_secretaire.username,
                "first_name": "Sophie",
                "last_name": "Martin",
                "email": utilisateur_cdt.email,
                "role": "Secretaire",
            },
            instance=utilisateur_secretaire,
        )
        assert not form.is_valid()
        assert "email" in form.errors

    def test_role_prepopulated_from_group(self, utilisateur_secretaire):
        """Le champ role est pre-rempli avec le groupe actuel de l'utilisateur."""
        form = ModifierUtilisateurForm(instance=utilisateur_secretaire)
        assert form.fields["role"].initial == "Secretaire"


# ── View Tests ───────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestVuesGestion:
    def test_secretaire_cannot_access_gestion(self, client_secretaire):
        resp = client_secretaire.get(reverse("gestion:liste"))
        assert resp.status_code == 403

    def test_cdt_can_access_liste(self, client_cdt):
        resp = client_cdt.get(reverse("gestion:liste"))
        assert resp.status_code == 302  # redirects to config_bailleurs

    def test_creer_utilisateur_with_email(self, client_cdt, groupe_secretaire_accent):
        resp = client_cdt.post(
            reverse("gestion:creer"),
            {
                "username": "new.user",
                "first_name": "Nouveau",
                "last_name": "Utilisateur",
                "email": "nouveau@example.com",
                "password1": "motdepasse123!",
                "password2": "motdepasse123!",
                "role": "Secretaire",
            },
        )
        assert resp.status_code == 302
        user = User.objects.get(username="new.user")
        assert user.email == "nouveau@example.com"
        assert EmailAddress.objects.filter(user=user, email="nouveau@example.com", verified=True).exists()

    def test_modifier_utilisateur_get_returns_form(self, client_cdt, utilisateur_secretaire):
        resp = client_cdt.get(reverse("gestion:modifier", kwargs={"pk": utilisateur_secretaire.pk}))
        assert resp.status_code == 200
        assert "form" in resp.context

    def test_modifier_utilisateur_post_updates(self, client_cdt, utilisateur_secretaire, groupe_secretaire_accent):
        EmailAddress.objects.create(
            user=utilisateur_secretaire, email=utilisateur_secretaire.email, verified=True, primary=True
        )
        resp = client_cdt.post(
            reverse("gestion:modifier", kwargs={"pk": utilisateur_secretaire.pk}),
            {
                "username": utilisateur_secretaire.username,
                "first_name": "SophieModif",
                "last_name": "MartinModif",
                "email": "sophie.modif@example.com",
                "role": "Secretaire",
            },
        )
        assert resp.status_code == 200  # HTMX response with HX-Redirect header
        assert "HX-Redirect" in resp.headers
        utilisateur_secretaire.refresh_from_db()
        assert utilisateur_secretaire.first_name == "SophieModif"
        assert utilisateur_secretaire.email == "sophie.modif@example.com"

    def test_reset_password_generates_new_password(self, client_cdt, utilisateur_secretaire):
        old_password_hash = utilisateur_secretaire.password
        resp = client_cdt.post(reverse("gestion:reset_password", kwargs={"pk": utilisateur_secretaire.pk}))
        assert resp.status_code == 200
        assert "new_password" in resp.context
        utilisateur_secretaire.refresh_from_db()
        assert utilisateur_secretaire.password != old_password_hash

    def test_reset_password_self_protection(self, client_cdt, utilisateur_cdt):
        resp = client_cdt.post(reverse("gestion:reset_password", kwargs={"pk": utilisateur_cdt.pk}))
        assert resp.status_code == 302  # redirect with error message

    def test_reactiver_utilisateur(self, client_cdt, utilisateur_secretaire):
        utilisateur_secretaire.is_active = False
        utilisateur_secretaire.save()

        resp = client_cdt.post(reverse("gestion:reactiver", kwargs={"pk": utilisateur_secretaire.pk}))
        assert resp.status_code == 302
        utilisateur_secretaire.refresh_from_db()
        assert utilisateur_secretaire.is_active is True

    def test_desactiver_self_protection(self, client_cdt, utilisateur_cdt):
        client_cdt.post(reverse("gestion:desactiver", kwargs={"pk": utilisateur_cdt.pk}))
        utilisateur_cdt.refresh_from_db()
        assert utilisateur_cdt.is_active is True

    def test_supprimer_utilisateur(self, client_cdt, utilisateur_secretaire):
        pk = utilisateur_secretaire.pk
        resp = client_cdt.post(reverse("gestion:supprimer", kwargs={"pk": pk}))
        assert resp.status_code == 302
        assert not User.objects.filter(pk=pk).exists()

    def test_supprimer_self_protection(self, client_cdt, utilisateur_cdt):
        resp = client_cdt.post(reverse("gestion:supprimer", kwargs={"pk": utilisateur_cdt.pk}))
        assert resp.status_code == 302
        assert User.objects.filter(pk=utilisateur_cdt.pk).exists()

    def test_supprimer_protected_user_shows_error(self, client_cdt, utilisateur_secretaire):
        """Un utilisateur lié à des BDC ne peut pas être supprimé (ProtectedError)."""
        bailleur = Bailleur.objects.create(nom="Test Bailleur", code="TST")
        BonDeCommande.objects.create(
            numero_bdc="DEL-TEST-001",
            bailleur=bailleur,
            adresse="1 Rue Test",
            cree_par=utilisateur_secretaire,
        )
        pk = utilisateur_secretaire.pk
        resp = client_cdt.post(
            reverse("gestion:supprimer", kwargs={"pk": pk}),
            follow=True,
        )
        assert resp.status_code == 200
        assert User.objects.filter(pk=pk).exists()
        assert "Impossible de supprimer" in resp.content.decode()
