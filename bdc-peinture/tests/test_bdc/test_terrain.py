"""
Tests -- generation du PDF terrain (sans prix) pour les sous-traitants.

Generateur unifie PyMuPDF : un seul processus pour tous les bailleurs,
generation depuis les donnees en base (plus de dispatch GDH/ERILIA).
"""

from decimal import Decimal

import fitz  # PyMuPDF
import pytest
from django.core.files.base import ContentFile
from django.test import Client
from django.urls import reverse

from apps.bdc.models import LignePrestation, StatutChoices
from apps.bdc.services import attribuer_st, reattribuer_st
from apps.bdc.terrain import generer_pdf_terrain
from apps.sous_traitants.models import SousTraitant


# --- Helper ------------------------------------------------------------------


def _extraire_texte_terrain(bdc) -> str:
    """Helper : genere le terrain et retourne le texte du PDF."""
    bdc = generer_pdf_terrain(bdc)
    doc = fitz.open(stream=bdc.pdf_terrain.read(), filetype="pdf")
    texte = doc[0].get_text()
    doc.close()
    return texte


# --- Tests generateur unifie PyMuPDF -----------------------------------------


class TestGenererPdfTerrainUnifie:
    """Tests du generateur unifie PyMuPDF (remplace GDH + ERILIA)."""

    def test_pdf_genere_et_stocke(self, bdc_a_faire):
        """Le PDF terrain est genere et stocke sur le BDC."""
        bdc = generer_pdf_terrain(bdc_a_faire)
        assert bdc.pdf_terrain
        assert bdc.pdf_terrain.name

    def test_pdf_une_seule_page(self, bdc_a_faire):
        """Le PDF terrain fait une seule page."""
        bdc = generer_pdf_terrain(bdc_a_faire)
        doc = fitz.open(stream=bdc.pdf_terrain.read(), filetype="pdf")
        assert len(doc) == 1
        doc.close()

    def test_nom_bailleur_en_entete(self, bdc_a_faire):
        """Le nom du bailleur apparait en en-tete."""
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert "Grand Delta Habitat" in texte or "GRAND DELTA HABITAT" in texte

    def test_numero_bdc_present(self, bdc_a_faire):
        """Le numero BDC apparait dans le PDF."""
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert bdc_a_faire.numero_bdc in texte

    def test_adresse_presente(self, bdc_a_faire):
        """L'adresse du chantier apparait."""
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert bdc_a_faire.adresse in texte
        assert bdc_a_faire.ville in texte

    def test_objet_travaux_present(self, bdc_a_faire):
        """L'objet des travaux apparait."""
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert bdc_a_faire.objet_travaux in texte

    def test_occupant_present(self, bdc_a_faire):
        """Le contact occupant (nom + tel) apparait."""
        bdc_a_faire.occupant_nom = "MUSELLA CHRISTIANE"
        bdc_a_faire.occupant_telephone = "0612345678"
        bdc_a_faire.save(update_fields=["occupant_nom", "occupant_telephone"])
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert "MUSELLA" in texte
        assert "0612345678" in texte

    def test_prestations_sans_prix(self, bdc_a_faire):
        """Les prestations apparaissent (designation, quantite, unite) SANS prix."""
        LignePrestation.objects.create(
            bdc=bdc_a_faire,
            designation="Peinture SDB",
            quantite=Decimal("15"),
            unite="m2",
            prix_unitaire=Decimal("11.19"),
            montant=Decimal("167.85"),
            ordre=0,
        )
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert "Peinture SDB" in texte
        assert "15" in texte
        assert "11.19" not in texte
        assert "167.85" not in texte

    def test_montants_bdc_absents(self, bdc_a_faire):
        """Les montants globaux du BDC n'apparaissent pas."""
        bdc_a_faire.montant_ht = Decimal("1071.40")
        bdc_a_faire.montant_tva = Decimal("107.14")
        bdc_a_faire.montant_ttc = Decimal("1178.54")
        bdc_a_faire.save(update_fields=["montant_ht", "montant_tva", "montant_ttc"])
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert "1071" not in texte
        assert "1178" not in texte

    def test_contact_emetteur_absent(self, bdc_a_faire):
        """Le telephone et email de l'emetteur n'apparaissent pas."""
        bdc_a_faire.emetteur_nom = "Joseph LONEGRO"
        bdc_a_faire.emetteur_telephone = "0490272800"
        bdc_a_faire.save(update_fields=["emetteur_nom", "emetteur_telephone"])
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert "0490272800" not in texte

    def test_mention_sans_prix(self, bdc_a_faire):
        """La mention DOCUMENT TERRAIN SANS PRIX apparait."""
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert "SANS PRIX" in texte

    def test_fonctionne_bailleur_gdh(self, bdc_a_faire):
        """Fonctionne pour un BDC GDH (plus besoin de pdf_original)."""
        assert bdc_a_faire.bailleur.code == "GDH"
        assert not bdc_a_faire.pdf_original  # pas de PDF original necessaire
        bdc = generer_pdf_terrain(bdc_a_faire)
        assert bdc.pdf_terrain

    def test_fonctionne_bailleur_erilia(self, bdc_a_faire, bailleur_erilia):
        """Fonctionne pour un BDC ERILIA."""
        bdc_a_faire.bailleur = bailleur_erilia
        bdc_a_faire.save(update_fields=["bailleur"])
        bdc = generer_pdf_terrain(bdc_a_faire)
        assert bdc.pdf_terrain

    def test_fonctionne_bailleur_inconnu(self, bdc_a_faire):
        """Fonctionne pour n'importe quel bailleur."""
        from apps.bdc.models import Bailleur

        autre = Bailleur.objects.create(nom="Nouveau Bailleur", code="NB")
        bdc_a_faire.bailleur = autre
        bdc_a_faire.save(update_fields=["bailleur"])
        bdc = generer_pdf_terrain(bdc_a_faire)
        assert bdc.pdf_terrain
        texte = _extraire_texte_terrain(bdc_a_faire)
        assert "NOUVEAU BAILLEUR" in texte


# --- Tests generer_pdf_terrain (dispatch unifie) -----------------------------


class TestGenererPdfTerrain:
    def test_genere_gdh(self, bdc_a_faire):
        assert bdc_a_faire.bailleur.code == "GDH"
        bdc = generer_pdf_terrain(bdc_a_faire)
        assert bdc.pdf_terrain
        assert bdc.pdf_terrain.name

    def test_genere_erilia(self, bdc_a_faire, bailleur_erilia):
        bdc_a_faire.bailleur = bailleur_erilia
        bdc_a_faire.save(update_fields=["bailleur"])
        bdc = generer_pdf_terrain(bdc_a_faire)
        assert bdc.pdf_terrain
        assert bdc.pdf_terrain.name

    def test_bailleur_inconnu(self, bdc_a_faire):
        from apps.bdc.models import Bailleur

        autre = Bailleur.objects.create(nom="Autre Bailleur", code="AUTRE")
        bdc_a_faire.bailleur = autre
        bdc_a_faire.save(update_fields=["bailleur"])
        bdc = generer_pdf_terrain(bdc_a_faire)
        assert bdc.pdf_terrain
        assert bdc.pdf_terrain.name


# --- Tests integration : attribution genere le PDF terrain -------------------


class TestAttributionGenereTerrainIntegration:
    def test_attribution_genere_pdf_terrain(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        bdc.refresh_from_db()
        assert bdc.pdf_terrain

    def test_reattribution_regenere_pdf_terrain(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        autre_st = SousTraitant.objects.create(nom="Martin", telephone="0600000000", actif=True)
        bdc = reattribuer_st(bdc, autre_st, Decimal("70"), utilisateur_cdt)
        bdc.refresh_from_db()
        assert bdc.pdf_terrain

    def test_attribution_reussit_meme_si_terrain_echoue(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)
        assert bdc.statut == StatutChoices.EN_COURS
        assert bdc.sous_traitant == sous_traitant


# --- Tests vue telecharger_terrain -------------------------------------------


@pytest.fixture
def client_logged(utilisateur_secretaire) -> Client:
    client = Client()
    client.login(username="secretaire_test", password="testpass123")
    return client


class TestTelechargerTerrain:
    def test_telechargement_ok(self, client_logged, bdc_a_faire):
        bdc_a_faire.pdf_terrain.save("terrain.pdf", ContentFile(b"%PDF-1.4 fake pdf"), save=True)

        url = reverse("bdc:terrain", args=[bdc_a_faire.pk])
        resp = client_logged.get(url)

        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"

    def test_404_si_pas_de_terrain(self, client_logged, bdc_a_faire):
        assert not bdc_a_faire.pdf_terrain

        url = reverse("bdc:terrain", args=[bdc_a_faire.pk])
        resp = client_logged.get(url)

        assert resp.status_code == 404


# --- Tests template detail : bouton BDC terrain ------------------------------


class TestDetailBoutonTerrain:
    def test_bouton_terrain_visible(self, client_logged, bdc_a_faire):
        bdc_a_faire.pdf_terrain.save("terrain.pdf", ContentFile(b"%PDF-1.4 fake pdf"), save=True)

        url = reverse("bdc:detail", args=[bdc_a_faire.pk])
        resp = client_logged.get(url)

        assert "BDC terrain" in resp.content.decode()

    def test_bouton_terrain_absent(self, client_logged, bdc_a_faire):
        assert not bdc_a_faire.pdf_terrain

        url = reverse("bdc:detail", args=[bdc_a_faire.pk])
        resp = client_logged.get(url)

        assert "BDC terrain" not in resp.content.decode()
