"""
Tests de la page de contrôle BDC (split-screen PDF + checklist).
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.bdc.forms import BDCEditionForm
from apps.bdc.models import (
    ActionChoices,
    ChecklistItem,
    ChecklistResultat,
    HistoriqueAction,
    StatutChoices,
    TransitionChoices,
)
from apps.bdc.services import BDCIncomplet, attribuer_st, changer_statut, valider_facturation, valider_realisation

# ─── Tests BDCEditionForm ───────────────────────────────────────────────────


class TestBDCEditionForm:
    """Tests for BDCEditionForm field changes."""

    def test_modalite_acces_not_in_fields(self):
        """modalite_acces field was removed from form."""
        assert "modalite_acces" not in BDCEditionForm.Meta.fields

    def test_notes_label_is_commentaires(self, bdc_a_traiter):
        form = BDCEditionForm(instance=bdc_a_traiter)
        assert form.fields["notes"].label == "Commentaires"

    def test_occupation_required_for_transition(self, bdc_a_traiter):
        """occupation obligatoire seulement lors d'une transition."""
        form = BDCEditionForm(data={"occupation": "", "nouveau_statut": "A_FAIRE"}, instance=bdc_a_traiter)
        assert not form.is_valid()
        assert "occupation" in form.errors

    def test_occupation_not_required_for_save(self, bdc_a_traiter):
        """occupation pas obligatoire pour un simple enregistrement."""
        form = BDCEditionForm(data={"occupation": ""}, instance=bdc_a_traiter)
        assert form.is_valid()

    def test_notes_not_required(self, bdc_a_traiter):
        form = BDCEditionForm(
            data={"occupation": "VACANT", "type_acces": "BADGE_CODE", "acces_complement": "Code 1234", "nouveau_statut": "A_FAIRE"},
            instance=bdc_a_traiter,
        )
        assert form.is_valid()

    def test_vacant_requires_type_acces(self, bdc_a_traiter):
        form = BDCEditionForm(
            data={"occupation": "VACANT", "type_acces": "", "acces_complement": "", "nouveau_statut": "A_FAIRE"},
            instance=bdc_a_traiter,
        )
        assert not form.is_valid()
        assert "type_acces" in form.errors

    def test_vacant_requires_acces_complement(self, bdc_a_traiter):
        form = BDCEditionForm(
            data={"occupation": "VACANT", "type_acces": "BADGE_CODE", "acces_complement": "", "nouveau_statut": "A_FAIRE"},
            instance=bdc_a_traiter,
        )
        assert not form.is_valid()
        assert "acces_complement" in form.errors

    def test_occupe_requires_rdv_date(self, bdc_a_traiter):
        form = BDCEditionForm(
            data={"occupation": "OCCUPE", "rdv_date": "", "nouveau_statut": "A_FAIRE"},
            instance=bdc_a_traiter,
        )
        assert not form.is_valid()
        assert "rdv_date" in form.errors

    def test_occupe_valid_with_rdv(self, bdc_a_traiter):
        form = BDCEditionForm(
            data={"occupation": "OCCUPE", "rdv_date": "2026-03-15T10:00", "nouveau_statut": "A_FAIRE"},
            instance=bdc_a_traiter,
        )
        assert form.is_valid()


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def checklist_items(db):
    """Crée 3 items de checklist actifs pour la transition A_TRAITER → A_FAIRE."""
    return [
        ChecklistItem.objects.create(
            libelle="Nature des prestations vérifiée",
            ordre=1,
            transition=TransitionChoices.CONTROLE,
        ),
        ChecklistItem.objects.create(
            libelle="Cohérence surface / type de logement",
            ordre=2,
            transition=TransitionChoices.CONTROLE,
        ),
        ChecklistItem.objects.create(
            libelle="Montant vérifié",
            ordre=3,
            transition=TransitionChoices.CONTROLE,
        ),
    ]


@pytest.fixture
def checklist_items_attribution(db):
    """Items de checklist pour la transition A_FAIRE -> EN_COURS."""
    return [
        ChecklistItem.objects.create(
            libelle="Sous-traitant contacté",
            ordre=1,
            transition=TransitionChoices.ATTRIBUTION,
        ),
    ]


@pytest.fixture
def checklist_items_realisation(db):
    """Items de checklist pour la transition EN_COURS -> A_FACTURER."""
    return [
        ChecklistItem.objects.create(
            libelle="Photos avant/après prises",
            ordre=1,
            transition=TransitionChoices.REALISATION,
        ),
    ]


@pytest.fixture
def checklist_items_facturation(db):
    """Items de checklist pour la transition A_FACTURER -> FACTURE."""
    return [
        ChecklistItem.objects.create(
            libelle="Facture reçue",
            ordre=1,
            transition=TransitionChoices.FACTURATION,
        ),
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

    def test_controle_cdt_editable(self, client_cdt, bdc_a_traiter, checklist_items):
        """GET contrôle en tant que CDT → 200, éditable (plus de restriction de rôle)."""
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        response = client_cdt.get(url)

        assert response.status_code == 200
        assert response.context["est_editable"] is True
        assert response.context["form_edition"] is not None


class TestControleFiltrageTransition:
    """La page contrôle ne montre que les items A_TRAITER__A_FAIRE."""

    def test_controle_ne_montre_pas_items_autres_transitions(
        self, client_secretaire, bdc_a_traiter, checklist_items, checklist_items_attribution
    ):
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        response = client_secretaire.get(url)
        assert len(response.context["checklist_items"]) == 3


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

    def test_enregistrement_sans_transition_affiche_toast(self, client_secretaire, bdc_a_traiter):
        """POST sans nouveau_statut → toast de succès avec lien dashboard."""
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        data = {
            "occupation": "VACANT",
            "type_acces": "BADGE_CODE",
            "acces_complement": "Code 1234",
            "notes": "Test partiel",
            "nouveau_statut": "",
        }
        resp = client_secretaire.post(url, data)
        assert resp.status_code == 200
        messages_list = list(resp.context["messages"])
        assert any("enregistr" in str(m) for m in messages_list)
        assert any("dashboard" in str(m).lower() for m in messages_list)

    def test_transition_sans_checklist_complete_echoue(self, client_secretaire, bdc_a_traiter, checklist_items):
        """POST transition sans checklist complète → reste A_TRAITER, message d'erreur."""
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        data = {
            f"check_{checklist_items[0].pk}": "on",
            # items 1 et 2 non cochés
            "occupation": "VACANT",
            "type_acces": "BADGE_CODE",
            "rdv_date": "",
            "notes": "",
            "nouveau_statut": "A_FAIRE",
        }
        response = client_secretaire.post(url, data)

        assert response.status_code == 200
        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.statut == StatutChoices.A_TRAITER

    def test_transition_avec_checklist_complete_et_occupation(self, client_secretaire, bdc_a_traiter, checklist_items):
        """POST transition avec checklist complète + occupation → passe en A_FAIRE, redirect."""
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        data = {
            "occupation": "VACANT",
            "type_acces": "BADGE_CODE",
            "acces_complement": "Code 1234",
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

    def test_transition_bloquee_si_occupation_manquante(self, client_secretaire, bdc_a_traiter):
        """POST transition sans occupation → formulaire invalide, transition bloquée, statut inchangé."""
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        data = {"occupation": "", "notes": "", "nouveau_statut": "A_FAIRE"}
        response = client_secretaire.post(url, data)

        assert response.status_code == 200
        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.statut == StatutChoices.A_TRAITER
        assert "occupation" in response.context["form_edition"].errors

    def test_transition_bloquee_si_rdv_date_manquante_occupe(self, client_secretaire, bdc_a_traiter):
        """POST avec occupation=OCCUPE sans rdv_date → formulaire invalide, transition bloquée."""
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        data = {"occupation": "OCCUPE", "rdv_date": "", "notes": "", "nouveau_statut": "A_FAIRE"}
        response = client_secretaire.post(url, data)

        assert response.status_code == 200
        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.statut == StatutChoices.A_TRAITER
        assert "rdv_date" in response.context["form_edition"].errors

    def test_transition_bloquee_si_type_acces_manquant_vacant(self, client_secretaire, bdc_a_traiter):
        """POST avec occupation=VACANT sans type_acces → formulaire invalide, transition bloquée."""
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        data = {
            "occupation": "VACANT",
            "type_acces": "",
            "acces_complement": "",
            "notes": "",
            "nouveau_statut": "A_FAIRE",
        }
        response = client_secretaire.post(url, data)

        assert response.status_code == 200
        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.statut == StatutChoices.A_TRAITER
        assert "type_acces" in response.context["form_edition"].errors


# ─── Tests service-level checklist validation ────────────────────────────────


class TestChecklistValidation:
    def test_checklist_bloque_transition_a_faire(self, bdc_a_traiter, utilisateur_secretaire, checklist_items):
        """changer_statut refuse A_TRAITER → A_FAIRE si checklist incomplète."""
        bdc_a_traiter.occupation = "VACANT"
        bdc_a_traiter.type_acces = "BADGE_CODE"
        bdc_a_traiter.save()

        with pytest.raises(BDCIncomplet, match="points de contrôle"):
            changer_statut(bdc_a_traiter, StatutChoices.A_FAIRE, utilisateur_secretaire)

    def test_checklist_complete_permet_transition(self, bdc_a_traiter, utilisateur_secretaire, checklist_items):
        """changer_statut accepte A_TRAITER → A_FAIRE si tous items cochés."""
        bdc_a_traiter.occupation = "VACANT"
        bdc_a_traiter.type_acces = "BADGE_CODE"
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
        bdc_a_traiter.save()

        bdc = changer_statut(bdc_a_traiter, StatutChoices.A_FAIRE, utilisateur_secretaire)
        assert bdc.statut == StatutChoices.A_FAIRE

    def test_occupe_avec_rdv_transition_ok(self, bdc_a_traiter, utilisateur_secretaire):
        """Logement occupé avec rdv_date : type_acces non requis, transition permise."""
        from datetime import datetime

        bdc_a_traiter.occupation = "OCCUPE"
        bdc_a_traiter.type_acces = ""
        bdc_a_traiter.rdv_date = datetime(2026, 3, 15, 10, 0)
        bdc_a_traiter.save()

        bdc = changer_statut(bdc_a_traiter, StatutChoices.A_FAIRE, utilisateur_secretaire)
        assert bdc.statut == StatutChoices.A_FAIRE

    def test_occupe_sans_rdv_bloque_transition(self, bdc_a_traiter, utilisateur_secretaire):
        """Logement occupé sans rdv_date : transition bloquée."""
        bdc_a_traiter.occupation = "OCCUPE"
        bdc_a_traiter.rdv_date = None
        bdc_a_traiter.save()

        with pytest.raises(BDCIncomplet, match="RDV"):
            changer_statut(bdc_a_traiter, StatutChoices.A_FAIRE, utilisateur_secretaire)


# ─── Test sidebar button ────────────────────────────────────────────────────


class TestSidebarControle:
    def test_sidebar_a_traiter_affiche_bouton_controler(self, client_secretaire, bdc_a_traiter):
        """Sidebar BDC A_TRAITER affiche bouton 'Contrôler' et pas le formulaire d'édition."""
        url = reverse("bdc:detail_sidebar", kwargs={"pk": bdc_a_traiter.pk})
        response = client_secretaire.get(url)

        content = response.content.decode()
        assert "Contr" in content  # "Contrôler ce BDC" (HTML entity encoded)
        assert reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk}) in content

    def test_sidebar_a_faire_read_only(self, client_secretaire, bdc_a_faire):
        """Sidebar BDC A_FAIRE shows read-only info, not the edit form."""
        url = reverse("bdc:detail_sidebar", kwargs={"pk": bdc_a_faire.pk})
        response = client_secretaire.get(url)

        content = response.content.decode()
        assert "Informations" in content  # read-only section header
        assert "id_occupation" not in content  # no dropdown form field


# ─── Tests Renvoi CDT → Secrétaire ──────────────────────────────────────────


class TestRenvoiControle:
    """Tests for CDT renvoi BDC to secrétaire."""

    def test_renvoi_changes_statut_to_a_traiter(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:renvoyer_controle", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.post(url, {"commentaire": "Occupation manquante"})
        bdc_a_faire.refresh_from_db()
        assert bdc_a_faire.statut == StatutChoices.A_TRAITER
        assert resp.status_code == 302

    def test_renvoi_creates_historique_with_comment(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:renvoyer_controle", kwargs={"pk": bdc_a_faire.pk})
        client_cdt.post(url, {"commentaire": "RDV non renseigné"})
        hist = HistoriqueAction.objects.filter(bdc=bdc_a_faire, action=ActionChoices.RENVOI).first()
        assert hist is not None
        assert hist.details["commentaire"] == "RDV non renseigné"

    def test_renvoi_requires_commentaire(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:renvoyer_controle", kwargs={"pk": bdc_a_faire.pk})
        client_cdt.post(url, {"commentaire": ""})
        bdc_a_faire.refresh_from_db()
        assert bdc_a_faire.statut == StatutChoices.A_FAIRE  # unchanged

    def test_renvoi_only_from_a_faire(self, client_cdt, bdc_a_traiter):
        url = reverse("bdc:renvoyer_controle", kwargs={"pk": bdc_a_traiter.pk})
        client_cdt.post(url, {"commentaire": "Test"})
        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.statut == StatutChoices.A_TRAITER  # unchanged (was already A_TRAITER)

    def test_renvoi_accessible_for_secretaire(self, client_secretaire, bdc_a_faire):
        url = reverse("bdc:renvoyer_controle", kwargs={"pk": bdc_a_faire.pk})
        resp = client_secretaire.post(url, {"commentaire": "Test"})
        assert resp.status_code == 302  # redirect after renvoi

    def test_renvoi_get_not_allowed(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:renvoyer_controle", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.get(url)
        assert resp.status_code == 302  # redirects to detail


# ─── Tests Sidebar read-only after contrôle ──────────────────────────────────


class TestSidebarReadOnly:
    """After contrôle (not A_TRAITER), sidebar shows read-only fields."""

    def test_sidebar_a_faire_no_form(self, client_secretaire, bdc_a_faire):
        """Secretaire sees no edit form for A_FAIRE BDC."""
        url = reverse("bdc:detail_sidebar", kwargs={"pk": bdc_a_faire.pk})
        resp = client_secretaire.get(url)
        content = resp.content.decode()
        assert "id_occupation" not in content  # no dropdown

    def test_sidebar_a_traiter_has_controle_button(self, client_secretaire, bdc_a_traiter):
        """A_TRAITER shows 'Contrôler' button, not form."""
        url = reverse("bdc:detail_sidebar", kwargs={"pk": bdc_a_traiter.pk})
        resp = client_secretaire.get(url)
        content = resp.content.decode()
        assert "Contr" in content  # "Contrôler ce BDC"


# ─── Tests Toast après contrôle ──────────────────────────────────────────────


class TestControleToast:
    """Toast message after contrôle validation."""

    def test_validation_shows_success_toast(self, client_secretaire, bdc_a_traiter, checklist_items):
        url = reverse("bdc:controle", kwargs={"pk": bdc_a_traiter.pk})
        data = {
            "occupation": "VACANT",
            "type_acces": "BADGE_CODE",
            "acces_complement": "Code 1234",
            "rdv_date": "",
            "notes": "",
            "nouveau_statut": "A_FAIRE",
        }
        # Cocher tous les items de checklist
        for item in checklist_items:
            data[f"check_{item.pk}"] = "on"
            data[f"note_{item.pk}"] = ""

        resp = client_secretaire.post(url, data, follow=True)
        messages_list = list(resp.context["messages"])
        assert any("valid" in str(m) and "attribuer" in str(m) for m in messages_list)


# ─── Tests garde checklist générique sur toutes les transitions ──────────────


class TestChecklistTransitionGenerique:
    """Tests de la garde checklist générique sur toutes les transitions."""

    def test_attribution_bloquee_si_checklist_incomplete(
        self, bdc_a_faire, sous_traitant, utilisateur_cdt, checklist_items_attribution
    ):
        with pytest.raises(BDCIncomplet, match="points de contrôle"):
            attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

    def test_attribution_ok_si_checklist_complete(
        self, bdc_a_faire, sous_traitant, utilisateur_cdt, checklist_items_attribution
    ):
        for item in checklist_items_attribution:
            ChecklistResultat.objects.create(bdc=bdc_a_faire, item=item, coche=True)
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        assert bdc.statut == StatutChoices.EN_COURS

    def test_attribution_ok_sans_checklist(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        assert bdc.statut == StatutChoices.EN_COURS

    def test_realisation_bloquee_si_checklist_incomplete(
        self, bdc_a_faire, sous_traitant, utilisateur_cdt, checklist_items_realisation
    ):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        with pytest.raises(BDCIncomplet, match="points de contrôle"):
            valider_realisation(bdc, utilisateur_cdt)

    def test_realisation_ok_si_checklist_complete(
        self, bdc_a_faire, sous_traitant, utilisateur_cdt, checklist_items_realisation
    ):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        for item in checklist_items_realisation:
            ChecklistResultat.objects.create(bdc=bdc, item=item, coche=True)
        bdc = valider_realisation(bdc, utilisateur_cdt)
        assert bdc.statut == StatutChoices.A_FACTURER

    def test_facturation_bloquee_si_checklist_incomplete(
        self, bdc_a_faire, sous_traitant, utilisateur_cdt, checklist_items_facturation
    ):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        bdc = valider_realisation(bdc, utilisateur_cdt)
        with pytest.raises(BDCIncomplet, match="points de contrôle"):
            valider_facturation(bdc, utilisateur_cdt)

    def test_facturation_ok_si_checklist_complete(
        self, bdc_a_faire, sous_traitant, utilisateur_cdt, checklist_items_facturation
    ):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        bdc = valider_realisation(bdc, utilisateur_cdt)
        for item in checklist_items_facturation:
            ChecklistResultat.objects.create(bdc=bdc, item=item, coche=True)
        bdc = valider_facturation(bdc, utilisateur_cdt)
        assert bdc.statut == StatutChoices.FACTURE

    def test_checklist_controle_filtre_par_transition(
        self, bdc_a_traiter, utilisateur_secretaire, checklist_items, checklist_items_attribution
    ):
        """Les items d'attribution ne bloquent pas la transition A_TRAITER -> A_FAIRE."""
        bdc_a_traiter.occupation = "VACANT"
        bdc_a_traiter.type_acces = "BADGE_CODE"
        bdc_a_traiter.save()
        for item in checklist_items:
            ChecklistResultat.objects.create(bdc=bdc_a_traiter, item=item, coche=True)
        bdc = changer_statut(bdc_a_traiter, StatutChoices.A_FAIRE, utilisateur_secretaire)
        assert bdc.statut == StatutChoices.A_FAIRE


# ─── Tests sidebar checklist transition ──────────────────────────────────────


class TestSidebarChecklistTransition:
    """Tests du flux checklist inline dans la sidebar."""

    @pytest.fixture
    def bdc_en_cours(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        return attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

    @pytest.fixture
    def bdc_a_facturer(self, bdc_en_cours, utilisateur_cdt):
        return valider_realisation(bdc_en_cours, utilisateur_cdt)

    def test_get_checklist_realisation(self, client_cdt, bdc_en_cours, checklist_items_realisation):
        url = reverse("bdc:sidebar_checklist", kwargs={"pk": bdc_en_cours.pk})
        resp = client_cdt.get(url + "?transition=EN_COURS__A_FACTURER")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Photos avant" in content

    def test_get_sans_items_affiche_confirmation(self, client_cdt, bdc_en_cours):
        """Si pas d'items pour cette transition, affiche un formulaire de confirmation (pas de transition directe)."""
        url = reverse("bdc:sidebar_checklist", kwargs={"pk": bdc_en_cours.pk})
        resp = client_cdt.get(url + "?transition=EN_COURS__A_FACTURER")
        assert resp.status_code == 200
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.EN_COURS  # pas encore transitionné
        assert "confirm_only" in resp.content.decode() or "Confirmer" in resp.content.decode()

    def test_post_checklist_complete_valide_transition(self, client_cdt, bdc_en_cours, checklist_items_realisation):
        url = reverse("bdc:sidebar_checklist", kwargs={"pk": bdc_en_cours.pk})
        data = {"transition": "EN_COURS__A_FACTURER"}
        for item in checklist_items_realisation:
            data[f"check_{item.pk}"] = "on"
        resp = client_cdt.post(url, data, HTTP_HX_REQUEST="true")
        assert resp.status_code == 200
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.A_FACTURER

    def test_post_checklist_incomplete_bloque(self, client_cdt, bdc_en_cours, checklist_items_realisation):
        url = reverse("bdc:sidebar_checklist", kwargs={"pk": bdc_en_cours.pk})
        data = {"transition": "EN_COURS__A_FACTURER"}
        # Ne pas cocher → bloque
        resp = client_cdt.post(url, data, HTTP_HX_REQUEST="true")
        assert resp.status_code == 200
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.EN_COURS
        assert "points de contr" in resp.content.decode().lower()

    def test_post_checklist_facturation(self, client_cdt, bdc_a_facturer, checklist_items_facturation):
        url = reverse("bdc:sidebar_checklist", kwargs={"pk": bdc_a_facturer.pk})
        data = {"transition": "A_FACTURER__FACTURE"}
        for item in checklist_items_facturation:
            data[f"check_{item.pk}"] = "on"
        resp = client_cdt.post(url, data, HTTP_HX_REQUEST="true")
        assert resp.status_code == 200
        bdc_a_facturer.refresh_from_db()
        assert bdc_a_facturer.statut == StatutChoices.FACTURE
