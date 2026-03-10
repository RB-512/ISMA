"""
Tests unitaires — attribution et réattribution de BDC à un sous-traitant.
Couvre les tâches 7.1 (services), 7.2 (notifications), 7.3 (vues), 7.4 (template detail).
"""

import logging
from decimal import Decimal

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.bdc.models import HistoriqueAction, LigneForfaitAttribution, PrixForfaitaire, StatutChoices
from apps.bdc.notifications import notifier_st_attribution
from apps.bdc.services import TransitionInvalide, attribuer_st, reattribuer_st
from apps.sous_traitants.models import SousTraitant

@pytest.fixture
def prix_t2(db):
    return PrixForfaitaire.objects.create(
        reference="PEINT-T2", designation="Peinture T2", unite="u", prix_unitaire="800.00"
    )


@pytest.fixture
def prix_t3(db):
    return PrixForfaitaire.objects.create(
        reference="PEINT-T3", designation="Peinture T3", unite="u", prix_unitaire="1200.00"
    )


# ─── 7.1 Tests services attribuer_st / reattribuer_st ─────────────────────────


class TestAttribuerST:
    """Tests unitaires de attribuer_st()."""

    def test_attribution_ok(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

        assert bdc.sous_traitant == sous_traitant
        assert bdc.pourcentage_st == Decimal("65")
        assert bdc.statut == StatutChoices.EN_COURS

    def test_montant_st_calcule(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        bdc_a_faire.montant_ht = Decimal("1000.00")
        bdc_a_faire.save(update_fields=["montant_ht"])

        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

        assert bdc.montant_st == Decimal("650.00")

    def test_montant_st_none_si_pas_montant_ht(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        assert bdc_a_faire.montant_ht is None
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

        assert bdc.montant_st is None

    def test_historique_attribution_cree(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

        action = HistoriqueAction.objects.filter(bdc=bdc_a_faire, action="ATTRIBUTION").first()
        assert action is not None
        assert action.details["sous_traitant"] == str(sous_traitant)
        assert action.details["pourcentage"] == "65"

    def test_attribution_refuse_si_pas_a_faire(self, bdc_a_traiter, sous_traitant, utilisateur_cdt):
        with pytest.raises(TransitionInvalide, match="À contrôler"):
            attribuer_st(bdc_a_traiter, sous_traitant, Decimal("65"), utilisateur_cdt)


class TestReattribuerST:
    """Tests unitaires de reattribuer_st()."""

    @pytest.fixture
    def bdc_en_cours(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        """BDC attribué puis en cours."""
        return attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

    @pytest.fixture
    def autre_st(self, db):
        return SousTraitant.objects.create(
            nom="Martin Peinture",
            telephone="0698765432",
            actif=True,
        )

    def test_reattribution_ok(self, bdc_en_cours, autre_st, utilisateur_cdt):
        bdc = reattribuer_st(bdc_en_cours, autre_st, Decimal("70"), utilisateur_cdt)

        assert bdc.sous_traitant == autre_st
        assert bdc.pourcentage_st == Decimal("70")
        assert bdc.statut == StatutChoices.EN_COURS  # statut inchangé

    def test_historique_reattribution_trace_ancien_st(self, bdc_en_cours, autre_st, utilisateur_cdt, sous_traitant):
        reattribuer_st(bdc_en_cours, autre_st, Decimal("70"), utilisateur_cdt)

        action = HistoriqueAction.objects.filter(bdc=bdc_en_cours, action="REATTRIBUTION").first()
        assert action is not None
        assert action.details["ancien_st"] == str(sous_traitant)
        assert action.details["nouveau_st"] == str(autre_st)

    def test_reattribution_refuse_si_pas_en_cours(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        with pytest.raises(TransitionInvalide, match="À attribuer"):
            reattribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

    def test_montant_st_recalcule(self, bdc_en_cours, autre_st, utilisateur_cdt):
        bdc_en_cours.montant_ht = Decimal("2000.00")
        bdc_en_cours.save(update_fields=["montant_ht"])

        bdc = reattribuer_st(bdc_en_cours, autre_st, Decimal("50"), utilisateur_cdt)

        assert bdc.montant_st == Decimal("1000.00")


# ─── 7.2 Tests notifications ─────────────────────────────────────────────────


class TestNotifierSTAttribution:
    """Tests unitaires de notifier_st_attribution()."""

    def test_message_contient_adresse(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        message = notifier_st_attribution(bdc)

        assert bdc.adresse_complete in message

    def test_message_ne_contient_pas_prix(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        bdc_a_faire.montant_ht = Decimal("1500.00")
        bdc_a_faire.save(update_fields=["montant_ht"])
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        message = notifier_st_attribution(bdc)

        assert "1500" not in message
        assert "975" not in message  # montant_st
        assert "65" not in message  # pourcentage

    def test_message_vide_si_pas_st(self, bdc_a_faire):
        message = notifier_st_attribution(bdc_a_faire)

        assert message == ""

    def test_logging(self, bdc_a_faire, sous_traitant, utilisateur_cdt, caplog):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

        with caplog.at_level(logging.INFO, logger="apps.bdc.notifications"):
            notifier_st_attribution(bdc)

        assert "SMS ST" in caplog.text
        assert sous_traitant.nom in caplog.text

    def test_message_contient_travaux(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        message = notifier_st_attribution(bdc)

        assert bdc.objet_travaux in message


# ─── 7.3 Tests vues attribuer_bdc / reattribuer_bdc ──────────────────────────


class TestAttribuerBDCView:
    """Tests vue attribuer_bdc."""

    def test_acces_cdt_ok(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:attribuer", args=[bdc_a_faire.pk])
        resp = client_cdt.get(url)
        assert resp.status_code == 200

    def test_secretaire_can_access_attribuer(self, client_secretaire, bdc_a_faire):
        url = reverse("bdc:attribuer", args=[bdc_a_faire.pk])
        resp = client_secretaire.get(url)
        assert resp.status_code == 200

    def test_statut_incorrect_redirige(self, client_cdt, bdc_a_traiter):
        url = reverse("bdc:attribuer", args=[bdc_a_traiter.pk])
        resp = client_cdt.get(url)
        assert resp.status_code == 302

    def test_post_valide_attribue(self, client_cdt, bdc_a_faire, sous_traitant):
        url = reverse("bdc:attribuer", args=[bdc_a_faire.pk])
        resp = client_cdt.post(
            url,
            {
                "sous_traitant": sous_traitant.pk,
                "pourcentage_st": "65",
            },
        )
        assert resp.status_code == 302

        bdc_a_faire.refresh_from_db()
        assert bdc_a_faire.sous_traitant == sous_traitant
        assert bdc_a_faire.statut == StatutChoices.EN_COURS

    def test_post_valide_message_contient_lien_retour(self, client_cdt, bdc_a_faire, sous_traitant):
        url = reverse("bdc:attribuer", args=[bdc_a_faire.pk])
        resp = client_cdt.post(url, {"sous_traitant": sous_traitant.pk, "pourcentage_st": "65"})
        msgs = [str(m) for m in get_messages(resp.wsgi_request)]
        msg = msgs[0]
        assert "attribué à" in msg
        assert "Continuer les attributions" in msg
        assert "statut=A_FAIRE" in msg

    def test_post_invalide_renvoie_formulaire(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:attribuer", args=[bdc_a_faire.pk])
        resp = client_cdt.post(
            url,
            {
                "sous_traitant": "",
                "pourcentage_st": "",
            },
        )
        assert resp.status_code == 200  # formulaire ré-affiché


class TestReattribuerBDCView:
    """Tests vue reattribuer_bdc."""

    @pytest.fixture
    def bdc_en_cours(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        return attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

    @pytest.fixture
    def autre_st(self, db):
        return SousTraitant.objects.create(
            nom="Martin Peinture",
            telephone="0698765432",
            actif=True,
        )

    def test_acces_cdt_ok(self, client_cdt, bdc_en_cours):
        url = reverse("bdc:reattribuer", args=[bdc_en_cours.pk])
        resp = client_cdt.get(url)
        assert resp.status_code == 200

    def test_statut_incorrect_redirige(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:reattribuer", args=[bdc_a_faire.pk])
        resp = client_cdt.get(url)
        assert resp.status_code == 302

    def test_post_valide_reattribue(self, client_cdt, bdc_en_cours, autre_st):
        url = reverse("bdc:reattribuer", args=[bdc_en_cours.pk])
        resp = client_cdt.post(
            url,
            {
                "sous_traitant": autre_st.pk,
                "pourcentage_st": "70",
            },
        )
        assert resp.status_code == 302

        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.sous_traitant == autre_st
        assert bdc_en_cours.pourcentage_st == Decimal("70")

    def test_post_valide_message_contient_lien_retour(self, client_cdt, bdc_en_cours, autre_st):
        url = reverse("bdc:reattribuer", args=[bdc_en_cours.pk])
        resp = client_cdt.post(url, {"sous_traitant": autre_st.pk, "pourcentage_st": "70"})
        msgs = [str(m) for m in get_messages(resp.wsgi_request)]
        msg = msgs[0]
        assert "réattribué à" in msg
        assert "Continuer les attributions" in msg

    def test_message_email_si_st_a_email(self, client_cdt, bdc_en_cours, autre_st):
        autre_st.email = "martin@example.com"
        autre_st.save(update_fields=["email"])
        url = reverse("bdc:reattribuer", args=[bdc_en_cours.pk])
        resp = client_cdt.post(url, {"sous_traitant": autre_st.pk, "pourcentage_st": "70"})
        msgs = [str(m) for m in get_messages(resp.wsgi_request)]
        assert "email" in msgs[0].lower()

    def test_message_sans_email_si_st_sans_email(self, client_cdt, bdc_en_cours, autre_st):
        autre_st.email = ""
        autre_st.save(update_fields=["email"])
        url = reverse("bdc:reattribuer", args=[bdc_en_cours.pk])
        resp = client_cdt.post(url, {"sous_traitant": autre_st.pk, "pourcentage_st": "70"})
        msgs = [str(m) for m in get_messages(resp.wsgi_request)]
        assert "email" not in msgs[0].lower()


# ─── 7.4 Tests template detail : boutons Attribuer / Réattribuer ─────────────


class TestDetailBDCBoutonsAttribution:
    """Tests conditionnels des boutons Attribuer / Réattribuer sur la fiche détail."""

    def test_bouton_attribuer_visible_cdt_a_faire(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:detail", args=[bdc_a_faire.pk])
        resp = client_cdt.get(url)
        assert "Attribuer" in resp.content.decode()

    def test_bouton_attribuer_visible_secretaire(self, client_secretaire, bdc_a_faire):
        url = reverse("bdc:detail", args=[bdc_a_faire.pk])
        resp = client_secretaire.get(url)
        content = resp.content.decode()
        assert "Attribuer" in content

    def test_bouton_reattribuer_visible_cdt_en_cours(self, client_cdt, bdc_a_faire, sous_traitant, utilisateur_cdt):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        url = reverse("bdc:detail", args=[bdc.pk])
        resp = client_cdt.get(url)
        assert "attribuer" in resp.content.decode().lower()

    def test_transition_en_cours_visible_pour_secretaire(self, client_secretaire, bdc_a_faire):
        """La transition A_FAIRE → EN_COURS est visible pour tous les utilisateurs authentifiés."""
        url = reverse("bdc:detail", args=[bdc_a_faire.pk])
        resp = client_secretaire.get(url)
        content = resp.content.decode()
        # Le bouton d'attribution (qui déclenche EN_COURS) doit être visible
        assert "Attribuer" in content


# ─── Tests vue attribution_partial (HTMX inline) ────────────────────────────


class TestAttributionPartial:
    """Tests de la vue attribution_partial (HTMX inline)."""

    @pytest.fixture
    def bdc_en_cours(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        return attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

    def test_get_retourne_formulaire(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:attribution_partial", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.get(url)
        assert resp.status_code == 200
        assert "id_sous_traitant" in resp.content.decode()

    def test_get_contient_tableau_repartition(self, client_cdt, bdc_a_faire, sous_traitant):
        url = reverse("bdc:attribution_partial", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.get(url)
        assert sous_traitant.nom in resp.content.decode()

    def test_post_valide_attribue_et_redirige(self, client_cdt, bdc_a_faire, sous_traitant):
        url = reverse("bdc:attribution_partial", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.post(url, {"sous_traitant": sous_traitant.pk, "pourcentage_st": "65.00"})
        assert resp.status_code == 204
        assert "HX-Redirect" in resp.headers
        bdc_a_faire.refresh_from_db()
        assert bdc_a_faire.statut == StatutChoices.EN_COURS

    def test_post_valide_message_contient_lien_retour(self, client_cdt, bdc_a_faire, sous_traitant):
        url = reverse("bdc:attribution_partial", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.post(url, {"sous_traitant": sous_traitant.pk, "pourcentage_st": "65.00"})
        msgs = [str(m) for m in get_messages(resp.wsgi_request)]
        msg = msgs[0]
        assert "attribué à" in msg
        assert "Continuer les attributions" in msg

    def test_post_invalide_reaffiche_formulaire(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:attribution_partial", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.post(url, {})
        assert resp.status_code == 200
        assert "id_sous_traitant" in resp.content.decode()

    def test_reattribution_pre_rempli(self, client_cdt, bdc_en_cours):
        url = reverse("bdc:attribution_partial", kwargs={"pk": bdc_en_cours.pk})
        resp = client_cdt.get(url)
        content = resp.content.decode()
        assert "selected" in content  # ST pré-sélectionné

    def test_get_avec_periode_filtre_repartition(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:attribution_partial", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.get(url + "?periode=mois")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Semaine" in content  # period selector present
        assert "Mois" in content

    def test_secretaire_can_access_attribution_partial(self, client_secretaire, bdc_a_faire):
        url = reverse("bdc:attribution_partial", kwargs={"pk": bdc_a_faire.pk})
        resp = client_secretaire.get(url)
        assert resp.status_code == 200


# ─── Tests vue attribution_split (page split-screen) ────────────────────────


class TestAttributionSplit:
    """Tests de la page split-screen d'attribution."""

    @pytest.fixture
    def bdc_en_cours(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        return attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

    def test_get_affiche_split_screen(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:attribution_split", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.get(url)
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "id_sous_traitant" in content
        assert bdc_a_faire.numero_bdc in content

    def test_post_valide_attribue_et_redirige(self, client_cdt, bdc_a_faire, sous_traitant):
        url = reverse("bdc:attribution_split", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.post(url, {"sous_traitant": sous_traitant.pk, "pourcentage_st": "65.00"})
        assert resp.status_code == 302
        bdc_a_faire.refresh_from_db()
        assert bdc_a_faire.statut == StatutChoices.EN_COURS

    def test_post_valide_message_contient_lien_retour(self, client_cdt, bdc_a_faire, sous_traitant):
        url = reverse("bdc:attribution_split", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.post(url, {"sous_traitant": sous_traitant.pk, "pourcentage_st": "65.00"})
        msgs = [str(m) for m in get_messages(resp.wsgi_request)]
        msg = msgs[0]
        assert "attribué à" in msg
        assert "Continuer les attributions" in msg

    def test_post_invalide_reaffiche(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:attribution_split", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.post(url, {})
        assert resp.status_code == 200
        assert "id_sous_traitant" in resp.content.decode()

    def test_reattribution_pre_rempli(self, client_cdt, bdc_en_cours):
        url = reverse("bdc:attribution_split", kwargs={"pk": bdc_en_cours.pk})
        resp = client_cdt.get(url)
        assert "selected" in resp.content.decode()

    def test_htmx_retourne_partial(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:attribution_split", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.get(url, HTTP_HX_REQUEST="true")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "<html" not in content.lower()

    def test_secretaire_can_access_attribution_split(self, client_secretaire, bdc_a_faire):
        url = reverse("bdc:attribution_split", kwargs={"pk": bdc_a_faire.pk})
        resp = client_secretaire.get(url)
        assert resp.status_code == 200

    def test_repartition_st_presente(self, client_cdt, bdc_a_faire, sous_traitant):
        url = reverse("bdc:attribution_split", kwargs={"pk": bdc_a_faire.pk})
        resp = client_cdt.get(url)
        assert sous_traitant.nom in resp.content.decode()

    def test_statut_incorrect_redirige(self, client_cdt, bdc_a_traiter):
        """Un BDC A_TRAITER ne peut pas etre attribue."""
        url = reverse("bdc:attribution_split", kwargs={"pk": bdc_a_traiter.pk})
        resp = client_cdt.get(url)
        assert resp.status_code == 302


# ─── Tests validation HTMX depuis la sidebar ─────────────────────────────


class TestSidebarValidation:
    """Tests du flux de validation rapide via HTMX dans la sidebar du dashboard."""

    @pytest.fixture
    def bdc_en_cours(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        return attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

    def test_valider_realisation_htmx_retourne_sidebar(self, client_cdt, bdc_en_cours):
        url = reverse("bdc:valider_realisation", args=[bdc_en_cours.pk])
        resp = client_cdt.post(url, HTTP_HX_REQUEST="true")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert bdc_en_cours.numero_bdc in content
        assert "bdc-updated" in resp["HX-Trigger"]

    def test_valider_realisation_htmx_change_statut(self, client_cdt, bdc_en_cours):
        url = reverse("bdc:valider_realisation", args=[bdc_en_cours.pk])
        resp = client_cdt.post(url, HTTP_HX_REQUEST="true")
        assert resp.status_code == 200
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.A_FACTURER

    def test_valider_realisation_htmx_affiche_succes(self, client_cdt, bdc_en_cours):
        url = reverse("bdc:valider_realisation", args=[bdc_en_cours.pk])
        resp = client_cdt.post(url, HTTP_HX_REQUEST="true")
        content = resp.content.decode()
        assert "réalisation validée" in content.lower() or "alisation valid" in content

    def test_valider_realisation_htmx_affiche_nouveau_statut(self, client_cdt, bdc_en_cours):
        url = reverse("bdc:valider_realisation", args=[bdc_en_cours.pk])
        resp = client_cdt.post(url, HTTP_HX_REQUEST="true")
        content = resp.content.decode()
        assert "facturer" in content.lower()

    def test_valider_realisation_non_htmx_redirige(self, client_cdt, bdc_en_cours):
        url = reverse("bdc:valider_realisation", args=[bdc_en_cours.pk])
        resp = client_cdt.post(url)
        assert resp.status_code == 302

    def test_valider_facturation_htmx(self, client_cdt, bdc_en_cours, utilisateur_cdt):
        from apps.bdc.services import valider_realisation as _valider

        _valider(bdc_en_cours, utilisateur_cdt)

        url = reverse("bdc:valider_facturation", args=[bdc_en_cours.pk])
        resp = client_cdt.post(url, HTTP_HX_REQUEST="true")
        assert resp.status_code == 200
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.FACTURE
        assert "bdc-updated" in resp["HX-Trigger"]

    def test_valider_realisation_htmx_erreur_si_mauvais_statut(self, client_cdt, bdc_a_faire):
        url = reverse("bdc:valider_realisation", args=[bdc_a_faire.pk])
        resp = client_cdt.post(url, HTTP_HX_REQUEST="true")
        assert resp.status_code == 200
        content = resp.content.decode()
        # Error message should be in the sidebar
        assert "bg-danger" in content


# ─── Tests attribution mode forfait ──────────────────────────────────────


class TestAttribuerForfait:
    """Tests unitaires de attribuer_st() en mode forfait."""

    def test_attribution_forfait_cree_lignes(self, bdc_a_faire, sous_traitant, utilisateur_cdt, prix_t2, prix_t3):
        lignes = [
            {"prix_id": prix_t2.pk, "quantite": Decimal("2"), "prix_unitaire": Decimal("800.00")},
            {"prix_id": prix_t3.pk, "quantite": Decimal("1"), "prix_unitaire": Decimal("1200.00")},
        ]
        bdc = attribuer_st(bdc_a_faire, sous_traitant, None, utilisateur_cdt, mode="forfait", lignes_forfait=lignes)

        assert bdc.mode_attribution == "forfait"
        assert bdc.montant_st == Decimal("2800.00")
        assert bdc.lignes_forfait.count() == 2

    def test_attribution_forfait_pu_modifiable(self, bdc_a_faire, sous_traitant, utilisateur_cdt, prix_t2):
        lignes = [{"prix_id": prix_t2.pk, "quantite": Decimal("1"), "prix_unitaire": Decimal("750.00")}]
        bdc = attribuer_st(bdc_a_faire, sous_traitant, None, utilisateur_cdt, mode="forfait", lignes_forfait=lignes)

        assert bdc.montant_st == Decimal("750.00")
        assert bdc.lignes_forfait.first().prix_unitaire == Decimal("750.00")

    def test_attribution_pourcentage_mode_set(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        bdc_a_faire.montant_ht = Decimal("1000.00")
        bdc_a_faire.save(update_fields=["montant_ht"])
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        assert bdc.mode_attribution == "pourcentage"
        assert bdc.montant_st == Decimal("650.00")
        assert bdc.lignes_forfait.count() == 0

    def test_forfait_calcule_pourcentage_inverse(self, bdc_a_faire, sous_traitant, utilisateur_cdt, prix_t2):
        bdc_a_faire.montant_ht = Decimal("2000.00")
        bdc_a_faire.save(update_fields=["montant_ht"])
        lignes = [{"prix_id": prix_t2.pk, "quantite": Decimal("1"), "prix_unitaire": Decimal("800.00")}]
        bdc = attribuer_st(bdc_a_faire, sous_traitant, None, utilisateur_cdt, mode="forfait", lignes_forfait=lignes)
        assert bdc.pourcentage_st == Decimal("40.00")


class TestAttribuerForfaitVue:
    """Tests vue attribuer_bdc en mode forfait."""

    def test_post_forfait_via_vue(self, client_cdt, bdc_a_faire, sous_traitant, prix_t2):
        url = reverse("bdc:attribuer", args=[bdc_a_faire.pk])
        resp = client_cdt.post(url, {
            "sous_traitant": sous_traitant.pk,
            "mode_attribution": "forfait",
            "ligne_0_prix": prix_t2.pk,
            "ligne_0_qty": "3",
            "ligne_0_pu": "800.00",
        })
        assert resp.status_code == 302
        bdc_a_faire.refresh_from_db()
        assert bdc_a_faire.mode_attribution == "forfait"
        assert bdc_a_faire.montant_st == Decimal("2400.00")

    def test_post_pourcentage_reste_compatible(self, client_cdt, bdc_a_faire, sous_traitant):
        url = reverse("bdc:attribuer", args=[bdc_a_faire.pk])
        resp = client_cdt.post(url, {
            "sous_traitant": sous_traitant.pk,
            "mode_attribution": "pourcentage",
            "pourcentage_st": "65",
        })
        assert resp.status_code == 302
        bdc_a_faire.refresh_from_db()
        assert bdc_a_faire.mode_attribution == "pourcentage"
        assert bdc_a_faire.pourcentage_st == Decimal("65")

    def test_get_contient_prix_forfaitaires(self, client_cdt, bdc_a_faire, prix_t2):
        url = reverse("bdc:attribuer", args=[bdc_a_faire.pk])
        resp = client_cdt.get(url)
        assert resp.status_code == 200
        assert "PEINT-T2" in resp.content.decode()
