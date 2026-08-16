"""
Tests — fiabilisation de l'attribution : montant obligatoire, annulation d'attribution
et suppression de BDC.

Contexte : un audit de production a montré qu'un BDC pouvait être attribué sans montant
via le mode forfait, ce qui creusait un écart silencieux entre attribution et relevés
(Sum ignore les NULL alors que Count compte la ligne).
"""

from decimal import Decimal

import pytest
from django.core import mail
from django.urls import reverse

from apps.bdc.models import (
    ActionChoices,
    BonDeCommande,
    HistoriqueAction,
    PrixForfaitaire,
    ReleveFacturation,
    StatutChoices,
)
from apps.bdc.services import (
    BDCIncomplet,
    TransitionInvalide,
    annuler_attribution,
    attribuer_st,
    supprimer_bdc,
)
from apps.sous_traitants.models import SousTraitant


@pytest.fixture
def prix_forfait(db):
    return PrixForfaitaire.objects.create(
        reference="PEINT-T2", designation="Peinture T2", unite="u", prix_unitaire="800.00"
    )


@pytest.fixture
def bdc_en_cours(bdc_a_faire, sous_traitant, utilisateur_cdt):
    """BDC attribué à 65 %, montant HT renseigné pour que montant_st soit calculé."""
    bdc_a_faire.montant_ht = Decimal("1000.00")
    bdc_a_faire.save(update_fields=["montant_ht"])
    return attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)


# ─── Montant obligatoire à l'attribution ──────────────────────────────────────


class TestMontantObligatoire:
    """Un BDC ne doit jamais pouvoir être attribué sans montant."""

    def test_forfait_sans_aucune_ligne_refuse(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        """Le trou constaté en production : mode forfait sans ligne valide."""
        with pytest.raises(BDCIncomplet, match="aucune ligne de prestation valide"):
            attribuer_st(
                bdc_a_faire,
                sous_traitant,
                None,
                utilisateur_cdt,
                mode="forfait",
                lignes_forfait=[],
            )

    def test_forfait_lignes_none_refuse(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        with pytest.raises(BDCIncomplet, match="aucune ligne de prestation valide"):
            attribuer_st(
                bdc_a_faire,
                sous_traitant,
                None,
                utilisateur_cdt,
                mode="forfait",
                lignes_forfait=None,
            )

    def test_bdc_reste_a_faire_apres_refus(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        """Le refus ne doit laisser aucune trace d'attribution."""
        with pytest.raises(BDCIncomplet):
            attribuer_st(bdc_a_faire, sous_traitant, None, utilisateur_cdt, mode="forfait", lignes_forfait=[])

        bdc_a_faire.refresh_from_db()
        assert bdc_a_faire.statut == StatutChoices.A_FAIRE
        assert bdc_a_faire.sous_traitant is None
        assert bdc_a_faire.montant_st is None

    def test_pourcentage_absent_refuse(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        with pytest.raises(BDCIncomplet, match="pourcentage ST est obligatoire"):
            attribuer_st(bdc_a_faire, sous_traitant, None, utilisateur_cdt)

    def test_forfait_avec_ligne_valide_passe(self, bdc_a_faire, sous_traitant, utilisateur_cdt, prix_forfait):
        bdc = attribuer_st(
            bdc_a_faire,
            sous_traitant,
            None,
            utilisateur_cdt,
            mode="forfait",
            lignes_forfait=[
                {"prix_id": prix_forfait.pk, "quantite": Decimal("2"), "prix_unitaire": Decimal("800.00")}
            ],
        )

        assert bdc.montant_st == Decimal("1600.00")
        assert bdc.statut == StatutChoices.EN_COURS


# ─── Annulation d'attribution ─────────────────────────────────────────────────


class TestAnnulerAttribution:
    def test_annulation_vide_tous_les_champs(self, bdc_en_cours, utilisateur_cdt):
        """Un simple changement de statut laisserait des résidus d'attribution."""
        assert bdc_en_cours.sous_traitant is not None
        assert bdc_en_cours.montant_st is not None

        bdc = annuler_attribution(bdc_en_cours, utilisateur_cdt)

        assert bdc.statut == StatutChoices.A_FAIRE
        assert bdc.sous_traitant is None
        assert bdc.montant_st is None
        assert bdc.pourcentage_st is None
        assert bdc.mode_attribution == ""

    def test_annulation_persiste_en_base(self, bdc_en_cours, utilisateur_cdt):
        annuler_attribution(bdc_en_cours, utilisateur_cdt)

        bdc = BonDeCommande.objects.get(pk=bdc_en_cours.pk)
        assert bdc.sous_traitant is None
        assert bdc.montant_st is None

    def test_annulation_supprime_lignes_forfait(self, bdc_a_faire, sous_traitant, utilisateur_cdt, prix_forfait):
        bdc = attribuer_st(
            bdc_a_faire,
            sous_traitant,
            None,
            utilisateur_cdt,
            mode="forfait",
            lignes_forfait=[
                {"prix_id": prix_forfait.pk, "quantite": Decimal("1"), "prix_unitaire": Decimal("800.00")}
            ],
        )
        assert bdc.lignes_forfait.count() == 1

        annuler_attribution(bdc, utilisateur_cdt)

        assert bdc.lignes_forfait.count() == 0

    def test_annulation_tracee_dans_historique(self, bdc_en_cours, sous_traitant, utilisateur_cdt):
        annuler_attribution(bdc_en_cours, utilisateur_cdt)

        action = HistoriqueAction.objects.filter(bdc=bdc_en_cours, action=ActionChoices.ANNULATION).first()
        assert action is not None
        assert action.details["ancien_st"] == str(sous_traitant)
        assert action.details["ancien_montant_st"] == "650.00"

    def test_annulation_refusee_si_pas_en_cours(self, bdc_a_faire, utilisateur_cdt):
        with pytest.raises(TransitionInvalide, match="doit être en 'En cours'"):
            annuler_attribution(bdc_a_faire, utilisateur_cdt)

    def test_annulation_refusee_si_dans_un_releve(self, bdc_en_cours, sous_traitant, utilisateur_cdt):
        releve = ReleveFacturation.objects.create(numero=1, sous_traitant=sous_traitant, cree_par=utilisateur_cdt)
        releve.bdc.add(bdc_en_cours)

        with pytest.raises(TransitionInvalide, match="figure dans un relevé"):
            annuler_attribution(bdc_en_cours, utilisateur_cdt)

    def test_bdc_annule_est_reattribuable(self, bdc_en_cours, sous_traitant, utilisateur_cdt):
        """L'annulation rend le bon de nouveau attribuable."""
        annuler_attribution(bdc_en_cours, utilisateur_cdt)

        bdc = attribuer_st(bdc_en_cours, sous_traitant, Decimal("50"), utilisateur_cdt)

        assert bdc.statut == StatutChoices.EN_COURS
        assert bdc.montant_st == Decimal("500.00")


# ─── Suppression de BDC ───────────────────────────────────────────────────────


class TestSupprimerBDC:
    def test_suppression_a_traiter_ok(self, bdc_a_traiter, utilisateur_secretaire):
        numero = supprimer_bdc(bdc_a_traiter, utilisateur_secretaire)

        assert numero == "450056"
        assert not BonDeCommande.objects.filter(numero_bdc="450056").exists()

    def test_suppression_a_faire_ok(self, bdc_a_faire, utilisateur_secretaire):
        supprimer_bdc(bdc_a_faire, utilisateur_secretaire)

        assert not BonDeCommande.objects.filter(numero_bdc="450057").exists()

    def test_suppression_libere_le_numero(self, bdc_a_traiter, bailleur_gdh, utilisateur_secretaire):
        """C'est tout l'intérêt : pouvoir réimporter le bon corrigé du bailleur."""
        supprimer_bdc(bdc_a_traiter, utilisateur_secretaire)

        recree = BonDeCommande.objects.create(
            numero_bdc="450056",
            bailleur=bailleur_gdh,
            adresse="3 Rue François 1er corrigée",
            cree_par=utilisateur_secretaire,
        )
        assert recree.pk is not None

    def test_suppression_refusee_si_en_cours(self, bdc_en_cours, utilisateur_cdt):
        with pytest.raises(TransitionInvalide, match="Annulez d'abord l'attribution"):
            supprimer_bdc(bdc_en_cours, utilisateur_cdt)

        assert BonDeCommande.objects.filter(pk=bdc_en_cours.pk).exists()

    @pytest.mark.parametrize("statut", [StatutChoices.A_FACTURER, StatutChoices.FACTURE])
    def test_suppression_refusee_apres_en_cours(self, bdc_en_cours, utilisateur_cdt, statut):
        bdc_en_cours.statut = statut
        bdc_en_cours.save(update_fields=["statut"])

        with pytest.raises(TransitionInvalide):
            supprimer_bdc(bdc_en_cours, utilisateur_cdt)

    def test_annulation_puis_suppression(self, bdc_en_cours, utilisateur_cdt):
        """Le parcours complet : un bon attribué redevient supprimable après annulation."""
        annuler_attribution(bdc_en_cours, utilisateur_cdt)
        supprimer_bdc(bdc_en_cours, utilisateur_cdt)

        assert not BonDeCommande.objects.filter(pk=bdc_en_cours.pk).exists()


# ─── Vues et permissions ──────────────────────────────────────────────────────


class TestVuesAnnulationSuppression:
    def test_secretaire_peut_supprimer(self, client_secretaire, bdc_a_traiter):
        response = client_secretaire.post(reverse("bdc:supprimer", args=[bdc_a_traiter.pk]))

        assert response.status_code == 302
        assert not BonDeCommande.objects.filter(pk=bdc_a_traiter.pk).exists()

    def test_cdt_peut_supprimer(self, client_cdt, bdc_a_traiter):
        response = client_cdt.post(reverse("bdc:supprimer", args=[bdc_a_traiter.pk]))

        assert response.status_code == 302
        assert not BonDeCommande.objects.filter(pk=bdc_a_traiter.pk).exists()

    def test_get_ne_supprime_pas(self, client_cdt, bdc_a_traiter):
        client_cdt.get(reverse("bdc:supprimer", args=[bdc_a_traiter.pk]))

        assert BonDeCommande.objects.filter(pk=bdc_a_traiter.pk).exists()

    def test_secretaire_ne_peut_pas_annuler(self, client_secretaire, bdc_en_cours):
        response = client_secretaire.post(reverse("bdc:annuler_attribution", args=[bdc_en_cours.pk]))

        assert response.status_code == 403

    def test_cdt_peut_annuler(self, client_cdt, bdc_en_cours):
        response = client_cdt.post(reverse("bdc:annuler_attribution", args=[bdc_en_cours.pk]))

        assert response.status_code == 302
        bdc_en_cours.refresh_from_db()
        assert bdc_en_cours.statut == StatutChoices.A_FAIRE
        assert bdc_en_cours.sous_traitant is None


class TestNotificationAnnulation:
    """Le ST doit être prévenu qu'on lui retire le chantier, comme il l'est de l'attribution."""

    def test_email_envoye_au_sous_traitant(self, bdc_en_cours, sous_traitant, utilisateur_cdt):
        mail.outbox.clear()

        annuler_attribution(bdc_en_cours, utilisateur_cdt)

        envoyes = [m for m in mail.outbox if sous_traitant.email in m.to]
        assert len(envoyes) == 1
        assert bdc_en_cours.numero_bdc in envoyes[0].subject
        assert "annulée" in envoyes[0].subject

    def test_message_precise_de_ne_pas_intervenir(self, bdc_en_cours, sous_traitant, utilisateur_cdt):
        """Sans réattribution, le ST doit comprendre qu'il ne doit pas se déplacer."""
        mail.outbox.clear()

        annuler_attribution(bdc_en_cours, utilisateur_cdt)

        corps = mail.outbox[0].body
        assert "ne vous est plus attribué" in corps
        assert "réattribué" not in corps

    def test_coordonnees_capturees_avant_detachement(self, bdc_en_cours, sous_traitant, utilisateur_cdt):
        """
        Le service vide bdc.sous_traitant : si les coordonnées étaient lues après,
        plus aucune notification ne partirait.
        """
        mail.outbox.clear()

        annuler_attribution(bdc_en_cours, utilisateur_cdt)

        assert bdc_en_cours.sous_traitant is None
        assert mail.outbox, "aucun email envoyé : coordonnées perdues au détachement"
        assert sous_traitant.email in mail.outbox[0].to

    def test_sans_email_ne_casse_pas_l_annulation(self, bdc_a_faire, utilisateur_cdt, db):
        st_sans_contact = SousTraitant.objects.create(nom="Sans Contact", telephone="")
        bdc_a_faire.montant_ht = Decimal("1000.00")
        bdc_a_faire.save(update_fields=["montant_ht"])
        bdc = attribuer_st(bdc_a_faire, st_sans_contact, Decimal("50"), utilisateur_cdt)

        annuler_attribution(bdc, utilisateur_cdt)

        assert bdc.statut == StatutChoices.A_FAIRE
        assert bdc.sous_traitant is None


class TestRetourApresSuppression:
    """L'utilisateur doit rester sur son onglet filtré, pas être ramené sur « Tous »."""

    def test_retour_sur_onglet_filtre(self, client_cdt, bdc_a_traiter):
        response = client_cdt.post(
            reverse("bdc:supprimer", args=[bdc_a_traiter.pk]),
            {"next": "/?statut=A_TRAITER"},
        )

        assert response.status_code == 302
        assert response.url == "/?statut=A_TRAITER"

    def test_sans_next_retour_tableau_de_bord(self, client_cdt, bdc_a_traiter):
        response = client_cdt.post(reverse("bdc:supprimer", args=[bdc_a_traiter.pk]))

        assert response.url == reverse("bdc:index")

    def test_next_externe_ignore(self, client_cdt, bdc_a_traiter):
        """Protection contre la redirection ouverte."""
        response = client_cdt.post(
            reverse("bdc:supprimer", args=[bdc_a_traiter.pk]),
            {"next": "https://exemple-malveillant.test/phishing"},
        )

        assert response.url == reverse("bdc:index")

    def test_next_vers_la_fiche_supprimee_ignore(self, client_cdt, bdc_a_traiter):
        """Rediriger vers la fiche qu'on vient de supprimer donnerait un 404."""
        response = client_cdt.post(
            reverse("bdc:supprimer", args=[bdc_a_traiter.pk]),
            {"next": reverse("bdc:detail", args=[bdc_a_traiter.pk])},
        )

        assert response.url == reverse("bdc:index")


class TestRetourApresAnnulation:
    """Depuis le panneau lateral, l'annulation doit ramener sur l'onglet d'origine."""

    def test_retour_sur_onglet_filtre(self, client_cdt, bdc_en_cours):
        response = client_cdt.post(
            reverse("bdc:annuler_attribution", args=[bdc_en_cours.pk]),
            {"next": "/?statut=EN_COURS"},
        )

        assert response.url == "/?statut=EN_COURS"

    def test_sans_next_retour_sur_la_fiche(self, client_cdt, bdc_en_cours):
        """Depuis la fiche complete, on reste sur la fiche : elle existe toujours."""
        response = client_cdt.post(reverse("bdc:annuler_attribution", args=[bdc_en_cours.pk]))

        assert response.url == reverse("bdc:detail", args=[bdc_en_cours.pk])

    def test_next_externe_ignore(self, client_cdt, bdc_en_cours):
        response = client_cdt.post(
            reverse("bdc:annuler_attribution", args=[bdc_en_cours.pk]),
            {"next": "https://exemple-malveillant.test/phishing"},
        )

        assert response.url == reverse("bdc:detail", args=[bdc_en_cours.pk])
