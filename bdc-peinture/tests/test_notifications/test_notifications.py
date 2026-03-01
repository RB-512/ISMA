"""
Tests unitaires — notifications SMS, email, branchement workflow et alertes délais.
"""

from datetime import date, timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core import mail
from django.core.management import call_command
from django.urls import reverse

from apps.bdc.models import BonDeCommande, StatutChoices
from apps.bdc.services import attribuer_st, reattribuer_st
from apps.notifications.alertes import get_bdc_delai_proche, get_bdc_en_retard
from apps.notifications.backends import LogSmsBackend, get_sms_backend
from apps.notifications.email import envoyer_email_attribution, envoyer_email_reattribution
from apps.notifications.sms import envoyer_sms_attribution, envoyer_sms_reattribution

# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def bdc_a_faire(db, bailleur_gdh, utilisateur_secretaire, sous_traitant):
    return BonDeCommande.objects.create(
        numero_bdc="NOTIF-001",
        bailleur=bailleur_gdh,
        adresse="10 Rue Notification",
        ville="Avignon",
        occupation="OCCUPE",
        objet_travaux="Peinture SDB",
        modalite_acces="Clé chez gardien",
        delai_execution=date(2026, 3, 15),
        montant_ht=Decimal("1000"),
        statut=StatutChoices.A_FAIRE,
        cree_par=utilisateur_secretaire,
    )


@pytest.fixture
def bdc_en_cours(db, bailleur_gdh, utilisateur_cdt, sous_traitant):
    return BonDeCommande.objects.create(
        numero_bdc="NOTIF-002",
        bailleur=bailleur_gdh,
        adresse="20 Rue Notification",
        ville="Orange",
        occupation="VACANT",
        objet_travaux="Peinture T3 complet",
        delai_execution=date(2026, 3, 10),
        montant_ht=Decimal("2000"),
        statut=StatutChoices.EN_COURS,
        sous_traitant=sous_traitant,
        pourcentage_st=Decimal("65"),
        cree_par=utilisateur_cdt,
    )


@pytest.fixture
def sous_traitant_b(db):
    from apps.sous_traitants.models import SousTraitant

    return SousTraitant.objects.create(
        nom="Martin Peinture",
        telephone="0698765432",
        email="martin@peinture.fr",
    )


@pytest.fixture
def sous_traitant_sans_contact(db):
    from apps.sous_traitants.models import SousTraitant

    return SousTraitant.objects.create(
        nom="ST Sans Contact",
        telephone="",
        email="",
    )


# ─── 7.1 Tests backend SMS ──────────────────────────────────────────────────


class TestLogSmsBackend:
    def test_send_logge_message(self, caplog):
        backend = LogSmsBackend()
        with caplog.at_level("INFO"):
            result = backend.send("0612345678", "Test SMS")
        assert result is True
        assert "0612345678" in caplog.text
        assert "Test SMS" in caplog.text

    def test_get_sms_backend_retourne_log_par_defaut(self):
        backend = get_sms_backend()
        assert isinstance(backend, LogSmsBackend)


class TestOvhSmsBackend:
    @patch("apps.notifications.backends.requests.post")
    def test_send_appelle_api_ovh(self, mock_post, settings):
        settings.OVH_APPLICATION_KEY = "app-key"
        settings.OVH_APPLICATION_SECRET = "app-secret"
        settings.OVH_CONSUMER_KEY = "consumer-key"
        settings.OVH_SMS_SERVICE_NAME = "sms-test-123"
        settings.OVH_SMS_SENDER = "BDCPeinture"

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        from apps.notifications.backends import OvhSmsBackend

        backend = OvhSmsBackend()
        result = backend.send("0612345678", "Test OVH")

        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "sms-test-123" in call_args[0][0]
        assert call_args[1]["json"]["receivers"] == ["0612345678"]
        assert call_args[1]["json"]["message"] == "Test OVH"


# ─── 7.2 Tests service SMS ──────────────────────────────────────────────────


class TestEnvoyerSmsAttribution:
    def test_message_contient_adresse_et_travaux(self, bdc_a_faire, sous_traitant):
        bdc_a_faire.sous_traitant = sous_traitant
        bdc_a_faire.save()

        with patch("apps.notifications.sms.get_sms_backend") as mock_backend:
            mock_instance = MagicMock()
            mock_instance.send.return_value = True
            mock_backend.return_value = mock_instance

            result = envoyer_sms_attribution(bdc_a_faire)

        assert result is True
        message = mock_instance.send.call_args[0][1]
        assert "10 Rue Notification" in message
        assert "Peinture SDB" in message
        assert "Occupé" in message

    def test_message_ne_contient_pas_de_prix(self, bdc_a_faire, sous_traitant):
        bdc_a_faire.sous_traitant = sous_traitant
        bdc_a_faire.montant_ht = Decimal("1000")
        bdc_a_faire.montant_st = Decimal("650")
        bdc_a_faire.pourcentage_st = Decimal("65")
        bdc_a_faire.save()

        with patch("apps.notifications.sms.get_sms_backend") as mock_backend:
            mock_instance = MagicMock()
            mock_instance.send.return_value = True
            mock_backend.return_value = mock_instance

            envoyer_sms_attribution(bdc_a_faire)

        message = mock_instance.send.call_args[0][1]
        assert "1000" not in message
        assert "650" not in message
        assert "65" not in message

    def test_st_sans_telephone_retourne_false(self, bdc_a_faire, sous_traitant_sans_contact):
        bdc_a_faire.sous_traitant = sous_traitant_sans_contact
        bdc_a_faire.save()

        result = envoyer_sms_attribution(bdc_a_faire)
        assert result is False

    def test_pas_de_st_retourne_false(self, bdc_a_faire):
        bdc_a_faire.sous_traitant = None
        bdc_a_faire.save()

        result = envoyer_sms_attribution(bdc_a_faire)
        assert result is False


class TestEnvoyerSmsReattribution:
    def test_sms_envoye_ancien_et_nouveau(self, bdc_en_cours):
        with patch("apps.notifications.sms.get_sms_backend") as mock_backend:
            mock_instance = MagicMock()
            mock_instance.send.return_value = True
            mock_backend.return_value = mock_instance

            result = envoyer_sms_reattribution(bdc_en_cours, "0611111111")

        assert result is True
        assert mock_instance.send.call_count == 2  # annulation + attribution


# ─── 7.3 Tests service email ────────────────────────────────────────────────


class TestEnvoyerEmailAttribution:
    def test_email_envoye_avec_contenu(self, bdc_a_faire, sous_traitant):
        bdc_a_faire.sous_traitant = sous_traitant
        bdc_a_faire.save()

        result = envoyer_email_attribution(bdc_a_faire)

        assert result is True
        assert len(mail.outbox) == 1
        email_sent = mail.outbox[0]
        assert "NOTIF-001" in email_sent.subject
        assert "dupont@peinture.fr" in email_sent.to
        assert "10 Rue Notification" in email_sent.body

    def test_st_sans_email_retourne_false(self, bdc_a_faire, sous_traitant_sans_contact):
        bdc_a_faire.sous_traitant = sous_traitant_sans_contact
        bdc_a_faire.save()

        result = envoyer_email_attribution(bdc_a_faire)
        assert result is False
        assert len(mail.outbox) == 0

    def test_email_sans_pdf_si_terrain_absent(self, bdc_a_faire, sous_traitant):
        bdc_a_faire.sous_traitant = sous_traitant
        bdc_a_faire.save()

        result = envoyer_email_attribution(bdc_a_faire)

        assert result is True
        email_sent = mail.outbox[0]
        assert len(email_sent.attachments) == 0
        assert "document terrain" in email_sent.body


class TestEnvoyerEmailReattribution:
    def test_email_annulation_et_attribution(self, bdc_en_cours):
        result = envoyer_email_reattribution(bdc_en_cours, "ancien@test.fr")

        assert result is True
        assert len(mail.outbox) == 2
        assert "annulée" in mail.outbox[0].body
        assert "attribué" in mail.outbox[1].body

    def test_email_sans_ancien_email(self, bdc_en_cours):
        envoyer_email_reattribution(bdc_en_cours, "")

        assert len(mail.outbox) == 1  # Seulement le nouveau ST


# ─── 7.4 Tests branchement workflow ─────────────────────────────────────────


class TestBranchementAttribution:
    @patch("apps.bdc.services._notifier_st_si_possible")
    @patch("apps.bdc.services._generer_terrain_si_possible")
    def test_attribution_appelle_notifications(
        self, mock_terrain, mock_notif, bdc_a_faire, sous_traitant, utilisateur_cdt
    ):
        attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        mock_notif.assert_called_once_with(bdc_a_faire)

    @patch("apps.notifications.sms.envoyer_sms_attribution", side_effect=Exception("SMS crash"))
    @patch("apps.bdc.services._generer_terrain_si_possible")
    def test_attribution_ok_meme_si_notification_echoue(
        self, mock_terrain, mock_sms, bdc_a_faire, sous_traitant, utilisateur_cdt
    ):
        # Le SMS lève une exception mais l'attribution ne doit pas être annulée
        # car _notifier_st_si_possible a un try/except interne
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        assert bdc.statut == StatutChoices.EN_COURS
        assert bdc.sous_traitant == sous_traitant


class TestBranchementReattribution:
    @patch("apps.bdc.services._notifier_reattribution_si_possible")
    @patch("apps.bdc.services._generer_terrain_si_possible")
    def test_reattribution_appelle_notifications(
        self, mock_terrain, mock_notif, bdc_en_cours, sous_traitant_b, utilisateur_cdt
    ):
        reattribuer_st(bdc_en_cours, sous_traitant_b, Decimal("70"), utilisateur_cdt)
        mock_notif.assert_called_once()
        call_args = mock_notif.call_args[0]
        assert call_args[0] == bdc_en_cours
        assert call_args[1] == "0612345678"  # ancien ST téléphone
        assert call_args[2] == "dupont@peinture.fr"  # ancien ST email


# ─── 7.5 Tests alertes ──────────────────────────────────────────────────────


class TestAlertesService:
    def test_bdc_en_retard(self, db, bailleur_gdh, utilisateur_cdt):
        BonDeCommande.objects.create(
            numero_bdc="RETARD-001",
            bailleur=bailleur_gdh,
            adresse="1 Rue Retard",
            statut=StatutChoices.EN_COURS,
            delai_execution=date.today() - timedelta(days=3),
            cree_par=utilisateur_cdt,
        )
        assert get_bdc_en_retard().count() == 1

    def test_bdc_delai_proche(self, db, bailleur_gdh, utilisateur_cdt):
        BonDeCommande.objects.create(
            numero_bdc="PROCHE-001",
            bailleur=bailleur_gdh,
            adresse="2 Rue Proche",
            statut=StatutChoices.EN_COURS,
            delai_execution=date.today() + timedelta(days=1),
            cree_par=utilisateur_cdt,
        )
        assert get_bdc_delai_proche().count() == 1

    def test_factures_exclus(self, db, bailleur_gdh, utilisateur_cdt):
        BonDeCommande.objects.create(
            numero_bdc="FACT-001",
            bailleur=bailleur_gdh,
            adresse="3 Rue Facturé",
            statut=StatutChoices.FACTURE,
            delai_execution=date.today() - timedelta(days=10),
            cree_par=utilisateur_cdt,
        )
        assert get_bdc_en_retard().count() == 0

    def test_a_facturer_exclus(self, db, bailleur_gdh, utilisateur_cdt):
        BonDeCommande.objects.create(
            numero_bdc="AFACT-001",
            bailleur=bailleur_gdh,
            adresse="4 Rue A Facturer",
            statut=StatutChoices.A_FACTURER,
            delai_execution=date.today() - timedelta(days=5),
            cree_par=utilisateur_cdt,
        )
        assert get_bdc_en_retard().count() == 0

    def test_sans_delai_exclus(self, db, bailleur_gdh, utilisateur_cdt):
        BonDeCommande.objects.create(
            numero_bdc="NODELAI-001",
            bailleur=bailleur_gdh,
            adresse="5 Rue Sans Délai",
            statut=StatutChoices.EN_COURS,
            delai_execution=None,
            cree_par=utilisateur_cdt,
        )
        assert get_bdc_en_retard().count() == 0


class TestManagementCommand:
    def test_check_delais_output(self, db, bailleur_gdh, utilisateur_cdt):
        BonDeCommande.objects.create(
            numero_bdc="CMD-001",
            bailleur=bailleur_gdh,
            adresse="1 Rue Command",
            statut=StatutChoices.EN_COURS,
            delai_execution=date.today() - timedelta(days=1),
            cree_par=utilisateur_cdt,
        )
        out = StringIO()
        call_command("check_delais", stdout=out)
        output = out.getvalue()
        assert "CMD-001" in output
        assert "1 BDC en retard" in output


class TestDashboardAlertes:
    def test_encart_visible_cdt_avec_retard(self, client, utilisateur_cdt, bailleur_gdh):
        BonDeCommande.objects.create(
            numero_bdc="DASH-001",
            bailleur=bailleur_gdh,
            adresse="1 Rue Dashboard",
            statut=StatutChoices.EN_COURS,
            delai_execution=date.today() - timedelta(days=2),
            cree_par=utilisateur_cdt,
        )
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:index"))
        content = response.content.decode()
        assert "DASH-001" in content
        assert "en retard" in content

    def test_encart_absent_secretaire(self, client, utilisateur_secretaire, utilisateur_cdt, bailleur_gdh):
        BonDeCommande.objects.create(
            numero_bdc="DASH-002",
            bailleur=bailleur_gdh,
            adresse="2 Rue Dashboard",
            statut=StatutChoices.EN_COURS,
            delai_execution=date.today() - timedelta(days=2),
            cree_par=utilisateur_cdt,
        )
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:index"))
        content = response.content.decode()
        assert "en retard" not in content

    def test_encart_absent_si_pas_dalerte(self, client, utilisateur_cdt):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:index"))
        content = response.content.decode()
        assert "en retard" not in content
        assert "proches du délai" not in content
