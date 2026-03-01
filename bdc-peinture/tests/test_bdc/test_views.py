"""
Tests des vues BDC : upload_pdf, creer_bdc, detail_bdc.
Tests unitaires (parsers mockés) et tests d'intégration (flux complet).
"""
import io
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.messages import get_messages
from django.urls import reverse

from apps.bdc.models import ActionChoices, BonDeCommande, HistoriqueAction, LignePrestation, StatutChoices

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _fake_pdf_file(content: bytes = b"%PDF-1.4 fake content") -> io.BytesIO:
    """Crée un faux fichier PDF en mémoire."""
    buf = io.BytesIO(content)
    buf.name = "test.pdf"
    return buf


def _mock_donnees_gdh(**overrides) -> dict:
    """Données extraites GDH simulées."""
    base = {
        "bailleur_code": "GDH",
        "numero_bdc": "450099",
        "numero_marche": "MRC-2024-001",
        "date_emission": None,
        "programme_residence": "Résidence Test",
        "adresse": "1 Rue du Test",
        "code_postal": "84000",
        "ville": "AVIGNON",
        "logement_numero": "A01",
        "logement_type": "T3",
        "logement_etage": "2",
        "logement_porte": "A",
        "objet_travaux": "Peinture complète",
        "delai_execution": None,
        "occupant_nom": "",
        "occupant_telephone": "",
        "occupant_email": "",
        "emetteur_nom": "Jean Test",
        "emetteur_telephone": "0490123456",
        "montant_ht": Decimal("1000.00"),
        "montant_tva": Decimal("100.00"),
        "montant_ttc": Decimal("1100.00"),
        "lignes_prestation": [
            {"designation": "Peinture murs", "quantite": Decimal("20.00"), "unite": "m²", "prix_unitaire": Decimal("10.00"), "montant": Decimal("200.00")},
        ],
    }
    base.update(overrides)
    return base


# ─── Tests upload_pdf ─────────────────────────────────────────────────────────

class TestUploadPDF:

    def test_get_affiche_formulaire(self, client, utilisateur_secretaire):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:upload"))
        assert response.status_code == 200
        assert b"pdf_file" in response.content

    def test_acces_non_authentifie_redirige(self, client):
        response = client.get(reverse("bdc:upload"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_acces_cdt_interdit(self, client, utilisateur_cdt):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:upload"))
        assert response.status_code == 403

    def test_post_sans_fichier_affiche_erreur(self, client, utilisateur_secretaire):
        client.force_login(utilisateur_secretaire)
        response = client.post(reverse("bdc:upload"), {})
        assert response.status_code == 200
        msgs = list(get_messages(response.wsgi_request))
        assert any("sélectionner" in str(m) for m in msgs)

    def test_post_fichier_non_pdf_affiche_erreur(self, client, utilisateur_secretaire):
        client.force_login(utilisateur_secretaire)
        fake_word = io.BytesIO(b"PK\x03\x04 fake docx")
        fake_word.name = "document.docx"
        response = client.post(reverse("bdc:upload"), {"pdf_file": fake_word})
        assert response.status_code == 200
        msgs = list(get_messages(response.wsgi_request))
        assert any("PDF" in str(m) for m in msgs)

    @patch("apps.bdc.views.detecter_parser")
    @patch("apps.bdc.views.default_storage")
    def test_post_pdf_inconnu_affiche_erreur(self, mock_storage, mock_detect, client, utilisateur_secretaire):
        from apps.pdf_extraction.detector import PDFTypeInconnu
        mock_detect.side_effect = PDFTypeInconnu("inconnu")
        client.force_login(utilisateur_secretaire)
        pdf = _fake_pdf_file()
        response = client.post(reverse("bdc:upload"), {"pdf_file": pdf})
        assert response.status_code == 200
        msgs = list(get_messages(response.wsgi_request))
        assert any("non reconnu" in str(m) for m in msgs)

    @patch("apps.bdc.views.detecter_parser")
    @patch("apps.bdc.views.default_storage")
    def test_post_pdf_valide_gdh_redirige(self, mock_storage, mock_detect, client, utilisateur_secretaire, bailleur_gdh):
        mock_parser = MagicMock()
        mock_parser.extraire.return_value = _mock_donnees_gdh()
        mock_detect.return_value = mock_parser
        mock_storage.save.return_value = "tmp/fake-uuid.pdf"

        client.force_login(utilisateur_secretaire)
        pdf = _fake_pdf_file()
        response = client.post(reverse("bdc:upload"), {"pdf_file": pdf})

        assert response.status_code == 302
        assert response.url == reverse("bdc:nouveau")
        # La session contient les données extraites
        session = client.session
        assert "bdc_extrait" in session
        assert session["bdc_extrait"]["numero_bdc"] == "450099"

    @patch("apps.bdc.views.detecter_parser")
    @patch("apps.bdc.views.default_storage")
    def test_post_exception_generique_affiche_erreur(self, mock_storage, mock_detect, client, utilisateur_secretaire):
        mock_detect.side_effect = Exception("pdfplumber crash")
        client.force_login(utilisateur_secretaire)
        pdf = _fake_pdf_file()
        response = client.post(reverse("bdc:upload"), {"pdf_file": pdf})
        assert response.status_code == 200
        msgs = list(get_messages(response.wsgi_request))
        assert any("corrompu" in str(m) for m in msgs)


# ─── Tests creer_bdc ──────────────────────────────────────────────────────────

class TestCreerBDC:

    def _post_data_minimal(self, bailleur_gdh) -> dict:
        return {
            "numero_bdc": "NOUVEAU-001",
            "bailleur": bailleur_gdh.pk,
            "adresse": "2 Rue des Tests",
        }

    def test_get_affiche_formulaire_vide_sans_session(self, client, utilisateur_secretaire):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:nouveau"))
        assert response.status_code == 200
        assert b"Enregistrer" in response.content

    def test_get_prefill_depuis_session(self, client, utilisateur_secretaire, bailleur_gdh):
        client.force_login(utilisateur_secretaire)
        session = client.session
        session["bdc_extrait"] = {
            "bailleur_code": "GDH",
            "numero_bdc": "450099",
            "adresse": "1 Rue du Test",
            "lignes_prestation": [],
        }
        session.save()

        response = client.get(reverse("bdc:nouveau"))
        assert response.status_code == 200

    def test_acces_cdt_interdit(self, client, utilisateur_cdt):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:nouveau"))
        assert response.status_code == 403

    def test_post_doublon_affiche_erreur(self, client, utilisateur_secretaire, bdc_a_traiter, bailleur_gdh):
        client.force_login(utilisateur_secretaire)
        response = client.post(reverse("bdc:nouveau"), {
            "numero_bdc": bdc_a_traiter.numero_bdc,  # doublon
            "bailleur": bailleur_gdh.pk,
            "adresse": "2 Rue Doublon",
        })
        assert response.status_code == 200
        assert BonDeCommande.objects.filter(numero_bdc=bdc_a_traiter.numero_bdc).count() == 1
        assert "existe déjà" in response.content.decode()

    def test_post_cree_bdc_a_traiter_sans_occupation(self, client, utilisateur_secretaire, bailleur_gdh):
        client.force_login(utilisateur_secretaire)
        response = client.post(reverse("bdc:nouveau"), {
            "numero_bdc": "NOUVEAU-001",
            "bailleur": bailleur_gdh.pk,
            "adresse": "2 Rue des Tests",
        })
        assert response.status_code == 302
        bdc = BonDeCommande.objects.get(numero_bdc="NOUVEAU-001")
        assert bdc.statut == StatutChoices.A_TRAITER
        assert bdc.cree_par == utilisateur_secretaire

    def test_post_cree_bdc_a_faire_avec_occupation(self, client, utilisateur_secretaire, bailleur_gdh):
        client.force_login(utilisateur_secretaire)
        response = client.post(reverse("bdc:nouveau"), {
            "numero_bdc": "NOUVEAU-002",
            "bailleur": bailleur_gdh.pk,
            "adresse": "3 Rue des Tests",
            "occupation": "VACANT",
            "type_acces": "BADGE_CODE",
            "modalite_acces": "Badge gardien",
        })
        assert response.status_code == 302
        bdc = BonDeCommande.objects.get(numero_bdc="NOUVEAU-002")
        assert bdc.statut == StatutChoices.A_FAIRE

    def test_post_cree_historique_creation(self, client, utilisateur_secretaire, bailleur_gdh):
        client.force_login(utilisateur_secretaire)
        client.post(reverse("bdc:nouveau"), {
            "numero_bdc": "NOUVEAU-003",
            "bailleur": bailleur_gdh.pk,
            "adresse": "4 Rue des Tests",
        })
        bdc = BonDeCommande.objects.get(numero_bdc="NOUVEAU-003")
        assert HistoriqueAction.objects.filter(
            bdc=bdc,
            action=ActionChoices.CREATION,
            utilisateur=utilisateur_secretaire,
        ).exists()

    @patch("apps.bdc.views.default_storage")
    def test_post_cree_lignes_prestation_depuis_session(self, mock_storage, client, utilisateur_secretaire, bailleur_gdh):
        mock_storage.exists.return_value = False  # Pas de PDF temp

        client.force_login(utilisateur_secretaire)
        session = client.session
        session["bdc_extrait"] = {
            "bailleur_code": "GDH",
            "lignes_prestation": [
                {"designation": "Peinture murs", "quantite": "20.00", "unite": "m²", "prix_unitaire": "10.00", "montant": "200.00"},
            ],
        }
        session.save()

        client.post(reverse("bdc:nouveau"), {
            "numero_bdc": "NOUVEAU-004",
            "bailleur": bailleur_gdh.pk,
            "adresse": "5 Rue des Tests",
        })
        bdc = BonDeCommande.objects.get(numero_bdc="NOUVEAU-004")
        lignes = LignePrestation.objects.filter(bdc=bdc)
        assert lignes.count() == 1
        assert lignes.first().designation == "Peinture murs"

    def test_post_redirige_vers_detail(self, client, utilisateur_secretaire, bailleur_gdh):
        client.force_login(utilisateur_secretaire)
        response = client.post(reverse("bdc:nouveau"), {
            "numero_bdc": "NOUVEAU-005",
            "bailleur": bailleur_gdh.pk,
            "adresse": "6 Rue des Tests",
        })
        assert response.status_code == 302
        bdc = BonDeCommande.objects.get(numero_bdc="NOUVEAU-005")
        assert response.url == reverse("bdc:detail", kwargs={"pk": bdc.pk})


# ─── Tests detail_bdc ─────────────────────────────────────────────────────────

class TestDetailBDC:

    def test_detail_accessible_aux_authentifies(self, client, utilisateur_cdt, bdc_a_traiter):
        client.force_login(utilisateur_cdt)
        response = client.get(reverse("bdc:detail", kwargs={"pk": bdc_a_traiter.pk}))
        assert response.status_code == 200
        assert bdc_a_traiter.numero_bdc.encode() in response.content

    def test_detail_non_authentifie_redirige(self, client, bdc_a_traiter):
        response = client.get(reverse("bdc:detail", kwargs={"pk": bdc_a_traiter.pk}))
        assert response.status_code == 302

    def test_detail_bdc_inexistant_retourne_404(self, client, utilisateur_secretaire):
        client.force_login(utilisateur_secretaire)
        response = client.get(reverse("bdc:detail", kwargs={"pk": 99999}))
        assert response.status_code == 404
