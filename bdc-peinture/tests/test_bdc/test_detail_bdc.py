"""
Tests des vues fiche détail BDC : detail_bdc, modifier_bdc, changer_statut_bdc.
"""
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.bdc.models import ActionChoices, BonDeCommande, HistoriqueAction, StatutChoices

# ─── Tests modifier_bdc ─────────────────────────────────────────────────────


class TestModifierBDC:

    def test_post_valide_met_a_jour_bdc(self, client, utilisateur_secretaire, bdc_a_traiter):
        client.force_login(utilisateur_secretaire)
        response = client.post(
            reverse("bdc:modifier", kwargs={"pk": bdc_a_traiter.pk}),
            {"occupation": "OCCUPE", "rdv_date": "2026-03-15T10:00", "notes": "Clé chez gardien"},
        )
        assert response.status_code == 302
        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.occupation == "OCCUPE"
        assert bdc_a_traiter.notes == "Clé chez gardien"

    def test_post_valide_trace_historique(self, client, utilisateur_secretaire, bdc_a_traiter):
        client.force_login(utilisateur_secretaire)
        client.post(
            reverse("bdc:modifier", kwargs={"pk": bdc_a_traiter.pk}),
            {"occupation": "VACANT", "type_acces": "BADGE_CODE", "acces_complement": "Code 1234"},
        )
        assert HistoriqueAction.objects.filter(
            bdc=bdc_a_traiter,
            action=ActionChoices.MODIFICATION,
            utilisateur=utilisateur_secretaire,
        ).exists()

    def test_post_valide_message_succes(self, client, utilisateur_secretaire, bdc_a_traiter):
        client.force_login(utilisateur_secretaire)
        response = client.post(
            reverse("bdc:modifier", kwargs={"pk": bdc_a_traiter.pk}),
            {"occupation": "VACANT", "type_acces": "BADGE_CODE", "acces_complement": "Code 1234"},
        )
        msgs = list(get_messages(response.wsgi_request))
        assert any("mis à jour" in str(m) for m in msgs)

    def test_acces_non_secretaire_interdit(self, client, utilisateur_cdt, bdc_a_traiter):
        client.force_login(utilisateur_cdt)
        response = client.post(
            reverse("bdc:modifier", kwargs={"pk": bdc_a_traiter.pk}),
            {"occupation": "VACANT"},
        )
        assert response.status_code == 403

    def test_get_redirige(self, client, utilisateur_secretaire, bdc_a_traiter):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:modifier", kwargs={"pk": bdc_a_traiter.pk}))
        assert response.status_code == 302

    def test_non_authentifie_redirige(self, client, bdc_a_traiter):
        response = client.post(
            reverse("bdc:modifier", kwargs={"pk": bdc_a_traiter.pk}),
            {"occupation": "VACANT"},
        )
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


# ─── Tests changer_statut_bdc ────────────────────────────────────────────────


class TestChangerStatutBDC:

    def test_transition_valide(self, client, utilisateur_secretaire, bdc_a_traiter):
        """A_TRAITER → A_FAIRE avec occupation + type_acces renseignés."""
        bdc_a_traiter.occupation = "OCCUPE"
        bdc_a_traiter.type_acces = "BADGE_CODE"
        bdc_a_traiter.save()
        client.force_login(utilisateur_secretaire)
        response = client.post(
            reverse("bdc:changer_statut", kwargs={"pk": bdc_a_traiter.pk}),
            {"nouveau_statut": StatutChoices.A_FAIRE},
        )
        assert response.status_code == 302
        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.statut == StatutChoices.A_FAIRE

    def test_transition_valide_message_succes(self, client, utilisateur_secretaire, bdc_a_traiter):
        bdc_a_traiter.occupation = "OCCUPE"
        bdc_a_traiter.type_acces = "BADGE_CODE"
        bdc_a_traiter.save()
        client.force_login(utilisateur_secretaire)
        response = client.post(
            reverse("bdc:changer_statut", kwargs={"pk": bdc_a_traiter.pk}),
            {"nouveau_statut": StatutChoices.A_FAIRE},
        )
        msgs = list(get_messages(response.wsgi_request))
        assert any("Statut changé" in str(m) for m in msgs)

    def test_transition_invalide(self, client, utilisateur_secretaire, bdc_a_traiter):
        """A_TRAITER → EN_COURS est interdit."""
        client.force_login(utilisateur_secretaire)
        response = client.post(
            reverse("bdc:changer_statut", kwargs={"pk": bdc_a_traiter.pk}),
            {"nouveau_statut": StatutChoices.EN_COURS},
        )
        assert response.status_code == 302
        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.statut == StatutChoices.A_TRAITER  # inchangé
        msgs = list(get_messages(response.wsgi_request))
        assert any("pas autorisée" in str(m) for m in msgs)

    def test_bdc_incomplet_occupation_manquante(self, client, utilisateur_secretaire, bdc_a_traiter):
        """A_TRAITER → A_FAIRE sans occupation = BDCIncomplet."""
        client.force_login(utilisateur_secretaire)
        response = client.post(
            reverse("bdc:changer_statut", kwargs={"pk": bdc_a_traiter.pk}),
            {"nouveau_statut": StatutChoices.A_FAIRE},
        )
        assert response.status_code == 302
        bdc_a_traiter.refresh_from_db()
        assert bdc_a_traiter.statut == StatutChoices.A_TRAITER  # inchangé
        msgs = list(get_messages(response.wsgi_request))
        assert any("Vacant" in str(m) or "Occupé" in str(m) for m in msgs)

    def test_acces_non_secretaire_interdit(self, client, utilisateur_cdt, bdc_a_traiter):
        client.force_login(utilisateur_cdt)
        response = client.post(
            reverse("bdc:changer_statut", kwargs={"pk": bdc_a_traiter.pk}),
            {"nouveau_statut": StatutChoices.A_FAIRE},
        )
        assert response.status_code == 403

    def test_get_redirige(self, client, utilisateur_secretaire, bdc_a_traiter):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:changer_statut", kwargs={"pk": bdc_a_traiter.pk}))
        assert response.status_code == 302


# ─── Tests detail_bdc enrichi ────────────────────────────────────────────────


class TestDetailBDCEnrichi:

    def test_contacts_occupant_affiches(self, client, utilisateur_secretaire, bdc_a_traiter):
        bdc_a_traiter.occupant_nom = "Mme Dupont"
        bdc_a_traiter.occupant_telephone = "0612345678"
        bdc_a_traiter.save()
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:detail", kwargs={"pk": bdc_a_traiter.pk}))
        assert response.status_code == 200
        content = response.content.decode()
        assert "Mme Dupont" in content
        assert "0612345678" in content

    def test_contacts_emetteur_affiches(self, client, utilisateur_secretaire, bdc_a_traiter):
        bdc_a_traiter.emetteur_nom = "Jean Martin"
        bdc_a_traiter.emetteur_telephone = "0490112233"
        bdc_a_traiter.save()
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:detail", kwargs={"pk": bdc_a_traiter.pk}))
        content = response.content.decode()
        assert "Jean Martin" in content
        assert "0490112233" in content

    def test_section_contacts_masquee_si_vide(self, client, utilisateur_secretaire, bdc_a_traiter):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:detail", kwargs={"pk": bdc_a_traiter.pk}))
        content = response.content.decode()
        assert "Contacts" not in content

    def test_formulaire_edition_absent_de_la_page_detail(self, client, utilisateur_secretaire, bdc_a_traiter):
        """Le formulaire d'édition terrain est dans la page contrôle, pas dans le détail."""
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:detail", kwargs={"pk": bdc_a_traiter.pk}))
        content = response.content.decode()
        assert "Compléter le BDC" not in content
        assert "id_occupation" not in content

    def test_bouton_controler_affiche_pour_secretaire_a_traiter(self, client, utilisateur_secretaire, bdc_a_traiter):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:detail", kwargs={"pk": bdc_a_traiter.pk}))
        content = response.content.decode()
        assert "ler" in content  # Contrôler
        assert "Nouveau BDC" in content

    def test_bouton_controler_masque_pour_cdt(self, client, utilisateur_cdt, bdc_a_traiter):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:detail", kwargs={"pk": bdc_a_traiter.pk}))
        content = response.content.decode()
        assert "Nouveau BDC" not in content

    def test_sous_traitant_affiche(self, client, utilisateur_secretaire, bdc_a_faire, sous_traitant):
        bdc_a_faire.sous_traitant = sous_traitant
        bdc_a_faire.save()
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:detail", kwargs={"pk": bdc_a_faire.pk}))
        content = response.content.decode()
        assert "Dupont Peinture" in content

    def test_statut_terminal_pas_de_boutons(self, client, utilisateur_secretaire, bailleur_gdh):
        bdc = BonDeCommande.objects.create(
            numero_bdc="FACTURE-001",
            bailleur=bailleur_gdh,
            adresse="1 Rue Finale",
            cree_par=utilisateur_secretaire,
            statut=StatutChoices.FACTURE,
        )
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:detail", kwargs={"pk": bdc.pk}))
        content = response.content.decode()
        assert "nouveau_statut" not in content
