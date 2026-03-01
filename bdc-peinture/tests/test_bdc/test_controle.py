"""
Tests de la page de contrôle BDC (split-screen PDF + checklist).
"""
import pytest
from django.urls import reverse

from apps.bdc.models import ChecklistItem, ChecklistResultat, StatutChoices
from apps.bdc.services import BDCIncomplet, changer_statut

# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def checklist_items(db):
    """Crée 3 items de checklist actifs."""
    return [
        ChecklistItem.objects.create(libelle="Nature des prestations vérifiée", ordre=1),
        ChecklistItem.objects.create(libelle="Cohérence surface / type de logement", ordre=2),
        ChecklistItem.objects.create(libelle="Montant vérifié", ordre=3),
    ]


@pytest.fixture
def client_secretaire(client, utilisateur_secretaire):
    """Client HTTP authentifié en tant que secrétaire."""
    client.force_login(utilisateur_secretaire)
    return client


@pytest.fixture
def client_cdt(client, utilisateur_cdt):
    """Client HTTP authentifié en tant que CDT."""
    client.force_login(utilisateur_cdt)
    return client


# ─── Tests GET ───────────────────────────────────────────────────────────────


class TestControleGet:
    def test_controle_a_traiter_secretaire(self, client_secretaire, bdc_a_traiter, checklist_items):
        """GET contrôle avec BDC A_TRAITER en tant que secrétaire → 200, formulaire + checklist éditable."""
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        response = client_secretaire.get(url)

        assert response.status_code == 200
        assert response.context["est_editable"] is True
        assert response.context["form_edition"] is not None
        assert len(response.context["checklist_items"]) == 3

    def test_controle_a_faire_lecture_seule(self, client_secretaire, bdc_a_faire, checklist_items):
        """GET contrôle avec BDC A_FAIRE → 200, lecture seule, pas de formulaire."""
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_faire.pk})
        response = client_secretaire.get(url)

        assert response.status_code == 200
        assert response.context["est_editable"] is False
        assert response.context["form_edition"] is None

    def test_controle_non_authentifie_redirige(self, client, bdc_a_traiter):
        """GET contrôle non authentifié → redirect login."""
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        response = client.get(url)

        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_controle_cdt_lecture_seule(self, client_cdt, bdc_a_traiter, checklist_items):
        """GET contrôle en tant que CDT → 200, lecture seule (pas secrétaire)."""
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        response = client_cdt.get(url)

        assert response.status_code == 200
        assert response.context["est_editable"] is False
        assert response.context["form_edition"] is None


# ─── Tests POST ──────────────────────────────────────────────────────────────


class TestControlePost:
    def test_sauvegarder_checklist_et_formulaire(self, client_secretaire, bdc_a_traiter, checklist_items):
        """POST sauvegarder checklist + formulaire → données en base."""
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        data = {
            f"check_{checklist_items[0].pk}": "on",
            f"note_{checklist_items[0].pk}": "OK vérifié",
            f"check_{checklist_items[1].pk}": "on",
            f"note_{checklist_items[1].pk}": "",
            # checklist_items[2] non coché
            "occupation": "VACANT",
            "type_acces": "BADGE_CODE",
            "acces_complement": "Code 1234",
            "modalite_acces": "Badge gardien",
            "rdv_date": "",
            "notes": "RAS",
            "nouveau_statut": "",
        }
        response = client_secretaire.post(url, data)

        assert response.status_code == 200

        # Vérifier les résultats checklist
        r1 = ChecklistResultat.objects.get(bdc=bdc_a_traiter, item=checklist_items[0])
        assert r1.coche is True
        assert r1.note == "OK vérifié"

        r2 = ChecklistResultat.objects.get(bdc=bdc_a_traiter, item=checklist_items[1])
        assert r2.coche is True

        r3 = ChecklistResultat.objects.get(bdc=bdc_a_traiter, item=checklist_items[2])
        assert r3.coche is False

        # Vérifier les champs du BDC
        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.occupation == "VACANT"
        assert bdc_a_traiter.notes == "RAS"

    def test_transition_sans_checklist_complete_echoue(self, client_secretaire, bdc_a_traiter, checklist_items):
        """POST transition sans checklist complète → reste A_TRAITER, message d'erreur."""
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        data = {
            f"check_{checklist_items[0].pk}": "on",
            # items 1 et 2 non cochés
            "occupation": "VACANT",
            "type_acces": "BADGE_CODE",
            "modalite_acces": "Badge gardien",
            "rdv_date": "",
            "notes": "",
            "nouveau_statut": "A_FAIRE",
        }
        response = client_secretaire.post(url, data)

        assert response.status_code == 200
        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.statut == StatutChoices.A_TRAITER

    def test_transition_avec_checklist_complete_et_occupation(
        self, client_secretaire, bdc_a_traiter, checklist_items
    ):
        """POST transition avec checklist complète + occupation → passe en A_FAIRE, redirect."""
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        data = {
            "occupation": "VACANT",
            "type_acces": "BADGE_CODE",
            "acces_complement": "Code 1234",
            "modalite_acces": "Badge gardien",
            "rdv_date": "",
            "notes": "",
            "nouveau_statut": "A_FAIRE",
        }
        # Cocher tous les items
        for item in checklist_items:
            data[f"check_{item.pk}"] = "on"
            data[f"note_{item.pk}"] = ""

        response = client_secretaire.post(url, data)

        # Redirect vers l'index après transition réussie
        assert response.status_code == 302
        assert response.url == reverse("bdc:index")

        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.statut == StatutChoices.A_FAIRE


# ─── Tests service-level checklist validation ────────────────────────────────


class TestChecklistValidation:
    def test_checklist_bloque_transition_a_faire(self, bdc_a_traiter, utilisateur_secretaire, checklist_items):
        """changer_statut refuse A_TRAITER → A_FAIRE si checklist incomplète."""
        bdc_a_traiter.occupation = "VACANT"
        bdc_a_traiter.type_acces = "BADGE_CODE"
        bdc_a_traiter.modalite_acces = "Badge gardien"
        bdc_a_traiter.save()

        with pytest.raises(BDCIncomplet, match="points de contrôle"):
            changer_statut(bdc_a_traiter, StatutChoices.A_FAIRE, utilisateur_secretaire)

    def test_checklist_complete_permet_transition(self, bdc_a_traiter, utilisateur_secretaire, checklist_items):
        """changer_statut accepte A_TRAITER → A_FAIRE si tous items cochés."""
        bdc_a_traiter.occupation = "VACANT"
        bdc_a_traiter.type_acces = "BADGE_CODE"
        bdc_a_traiter.modalite_acces = "Badge gardien"
        bdc_a_traiter.save()

        # Cocher tous les items
        for item in checklist_items:
            ChecklistResultat.objects.create(bdc=bdc_a_traiter, item=item, coche=True)

        bdc = changer_statut(bdc_a_traiter, StatutChoices.A_FAIRE, utilisateur_secretaire)
        assert bdc.statut == StatutChoices.A_FAIRE

    def test_sans_items_actifs_transition_ok(self, bdc_a_traiter, utilisateur_secretaire):
        """Si aucun item de checklist actif, la transition est permise."""
        bdc_a_traiter.occupation = "VACANT"
        bdc_a_traiter.type_acces = "BADGE_CODE"
        bdc_a_traiter.modalite_acces = "Badge gardien"
        bdc_a_traiter.save()

        bdc = changer_statut(bdc_a_traiter, StatutChoices.A_FAIRE, utilisateur_secretaire)
        assert bdc.statut == StatutChoices.A_FAIRE


# ─── Test sidebar button ────────────────────────────────────────────────────


class TestSidebarControle:
    def test_sidebar_a_traiter_affiche_bouton_controler(self, client_secretaire, bdc_a_traiter):
        """Sidebar BDC A_TRAITER affiche bouton 'Contrôler' et pas le formulaire d'édition."""
        url = reverse("bdc:detail_sidebar", kwargs={"pk": bdc_a_traiter.pk})
        response = client_secretaire.get(url)

        content = response.content.decode()
        assert "Contr" in content  # "Contrôler ce BDC" (HTML entity encoded)
        assert reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk}) in content

    def test_sidebar_a_faire_affiche_formulaire(self, client_secretaire, bdc_a_faire):
        """Sidebar BDC A_FAIRE affiche le formulaire d'édition, pas le bouton contrôle."""
        url = reverse("bdc:detail_sidebar", kwargs={"pk": bdc_a_faire.pk})
        response = client_secretaire.get(url)

        content = response.content.decode()
        assert "sidebar-action" in content or "Enregistrer" in content
