"""
Tests : un utilisateur Secretaire peut gerer les items checklist
dans la page Configuration (plus de 403 Forbidden).
"""

import pytest
from django.urls import reverse

from apps.bdc.models import ChecklistItem, TransitionChoices


@pytest.fixture
def client_secretaire(client, utilisateur_secretaire):
    client.force_login(utilisateur_secretaire)
    return client


@pytest.fixture
def client_cdt(client, utilisateur_cdt):
    client.force_login(utilisateur_cdt)
    return client


@pytest.fixture
def checklist_item(db):
    return ChecklistItem.objects.create(
        libelle="Test item",
        ordre=1,
        transition=TransitionChoices.CONTROLE,
    )


class TestChecklistSecretaire:
    """Un Secretaire peut creer, modifier et supprimer des items checklist."""

    def test_secretaire_peut_creer_item(self, client_secretaire):
        resp = client_secretaire.post(
            reverse("gestion:checklist_liste"),
            {"libelle": "Nouveau point", "transition": TransitionChoices.CONTROLE},
        )
        assert resp.status_code == 302
        assert ChecklistItem.objects.filter(libelle="Nouveau point").exists()

    def test_secretaire_peut_modifier_item(self, client_secretaire, checklist_item):
        resp = client_secretaire.post(
            reverse("gestion:checklist_modifier", kwargs={"pk": checklist_item.pk}),
            {"libelle": "Item modifie", "ordre": "1"},
        )
        assert resp.status_code == 302
        checklist_item.refresh_from_db()
        assert checklist_item.libelle == "Item modifie"

    def test_secretaire_peut_toggle_item(self, client_secretaire, checklist_item):
        resp = client_secretaire.post(
            reverse("gestion:checklist_modifier", kwargs={"pk": checklist_item.pk}),
            {"action": "toggle"},
        )
        assert resp.status_code == 302
        checklist_item.refresh_from_db()
        assert checklist_item.actif is False

    def test_secretaire_peut_supprimer_item(self, client_secretaire, checklist_item):
        pk = checklist_item.pk
        resp = client_secretaire.post(
            reverse("gestion:checklist_supprimer", kwargs={"pk": pk}),
        )
        assert resp.status_code == 302
        assert not ChecklistItem.objects.filter(pk=pk).exists()

    def test_cdt_peut_toujours_supprimer_item(self, client_cdt, checklist_item):
        pk = checklist_item.pk
        resp = client_cdt.post(
            reverse("gestion:checklist_supprimer", kwargs={"pk": pk}),
        )
        assert resp.status_code == 302
        assert not ChecklistItem.objects.filter(pk=pk).exists()

    def test_utilisateur_sans_groupe_403(self, client, db, utilisateur_secretaire, checklist_item):
        """Un utilisateur sans groupe CDT/Secretaire recoit 403."""
        from django.contrib.auth.models import User

        user = User.objects.create_user(username="nobody", password="pass123")
        client.force_login(user)
        resp = client.post(
            reverse("gestion:checklist_supprimer", kwargs={"pk": checklist_item.pk}),
        )
        assert resp.status_code == 403
