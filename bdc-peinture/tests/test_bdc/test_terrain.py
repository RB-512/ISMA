"""
Tests — génération du PDF terrain (sans prix) pour les sous-traitants.
Couvre les tâches 7.1 à 7.6.

Note : WeasyPrint nécessite des bibliothèques C natives (GTK/Pango).
Les tests ERILIA mockent WeasyPrint et vérifient le HTML généré.
"""

import sys
from decimal import Decimal
from unittest.mock import MagicMock, patch

import fitz  # PyMuPDF
import pytest
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.test import Client
from django.urls import reverse

from apps.bdc.models import LignePrestation, StatutChoices
from apps.bdc.services import attribuer_st, reattribuer_st
from apps.bdc.terrain import (
    GenerationTerrainError,
    _generer_terrain_gdh,
    generer_pdf_terrain,
)
from apps.sous_traitants.models import SousTraitant

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _creer_pdf_2_pages() -> bytes:
    """Crée un PDF de 2 pages en mémoire via PyMuPDF."""
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((72, 72), "Page 1 — Bon de commande avec prix")
    page2 = doc.new_page()
    page2.insert_text((72, 72), "Page 2 — Bon d'intervention sans prix")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def _creer_pdf_2_pages_avec_emetteur() -> bytes:
    """Crée un PDF de 2 pages avec infos émetteur (tél + email) sur page 2."""
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((72, 72), "Page 1 — Bon de commande avec prix")
    page2 = doc.new_page()
    y = 72
    page2.insert_text((72, y), "Bon d'intervention sans prix")
    y += 30
    page2.insert_text((72, y), "Adresse : 3 Rue Francois 1er 84000 AVIGNON")
    y += 20
    page2.insert_text((72, y), "Emetteur : Joseph LONEGRO")
    y += 20
    page2.insert_text((72, y), "Mail : joseph.lonegro@gdhabitat.fr")
    y += 20
    page2.insert_text((72, y), "Tel : 0490272800")
    y += 20
    page2.insert_text((72, y), "Portable : 0612345678")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def _creer_pdf_1_page() -> bytes:
    """Crée un PDF d'une seule page."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Page unique")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def _fake_pdf() -> bytes:
    """Crée un faux PDF minimal pour les mocks WeasyPrint."""
    return _creer_pdf_1_page()


@pytest.fixture()
def _mock_weasyprint():
    """Injecte un module weasyprint factice dans sys.modules."""
    mock_module = MagicMock()
    mock_module.HTML.return_value.write_pdf.return_value = _fake_pdf()
    with patch.dict(sys.modules, {"weasyprint": mock_module}):
        yield mock_module


# ─── 7.1 Tests _generer_terrain_gdh ──────────────────────────────────────────


class TestGenererTerrainGDH:
    def test_extraction_page_2_reussie(self, bdc_a_faire):
        pdf_2pages = _creer_pdf_2_pages()
        bdc_a_faire.pdf_original.save("test.pdf", ContentFile(pdf_2pages), save=True)

        result = _generer_terrain_gdh(bdc_a_faire)

        assert isinstance(result, bytes)
        assert len(result) > 0
        # Vérifier que c'est un PDF valide avec 1 page
        doc = fitz.open(stream=result, filetype="pdf")
        assert len(doc) == 1
        text = doc[0].get_text()
        assert "Page 2" in text
        doc.close()

    def test_pdf_1_page_leve_erreur(self, bdc_a_faire):
        pdf_1page = _creer_pdf_1_page()
        bdc_a_faire.pdf_original.save("test.pdf", ContentFile(pdf_1page), save=True)

        with pytest.raises(GenerationTerrainError, match="1 page"):
            _generer_terrain_gdh(bdc_a_faire)

    def test_pas_de_pdf_original_leve_erreur(self, bdc_a_faire):
        assert not bdc_a_faire.pdf_original

        with pytest.raises(GenerationTerrainError, match="pas de PDF original"):
            _generer_terrain_gdh(bdc_a_faire)


# ─── 7.1b Tests anonymisation PDF terrain GDH ─────────────────────────────────


class TestAnonymisationTerrainGDH:
    def test_telephone_emetteur_masque(self, bdc_a_faire):
        """Le téléphone de l'émetteur doit être remplacé par *** dans le PDF terrain."""
        pdf_avec_emetteur = _creer_pdf_2_pages_avec_emetteur()
        bdc_a_faire.pdf_original.save("test.pdf", ContentFile(pdf_avec_emetteur), save=True)

        result = _generer_terrain_gdh(bdc_a_faire)

        doc = fitz.open(stream=result, filetype="pdf")
        texte = doc[0].get_text()
        doc.close()
        assert "0490272800" not in texte
        assert "0612345678" not in texte

    def test_email_emetteur_masque(self, bdc_a_faire):
        """L'email de l'émetteur doit être remplacé par *** dans le PDF terrain."""
        pdf_avec_emetteur = _creer_pdf_2_pages_avec_emetteur()
        bdc_a_faire.pdf_original.save("test.pdf", ContentFile(pdf_avec_emetteur), save=True)

        result = _generer_terrain_gdh(bdc_a_faire)

        doc = fitz.open(stream=result, filetype="pdf")
        texte = doc[0].get_text()
        doc.close()
        assert "joseph.lonegro@gdhabitat.fr" not in texte

    def test_nom_emetteur_preserve(self, bdc_a_faire):
        """Le nom de l'émetteur doit rester visible (seuls tél et email masqués)."""
        pdf_avec_emetteur = _creer_pdf_2_pages_avec_emetteur()
        bdc_a_faire.pdf_original.save("test.pdf", ContentFile(pdf_avec_emetteur), save=True)

        result = _generer_terrain_gdh(bdc_a_faire)

        doc = fitz.open(stream=result, filetype="pdf")
        texte = doc[0].get_text()
        doc.close()
        assert "Emetteur" in texte

    def test_adresse_preservee(self, bdc_a_faire):
        """L'adresse du chantier ne doit pas être masquée."""
        pdf_avec_emetteur = _creer_pdf_2_pages_avec_emetteur()
        bdc_a_faire.pdf_original.save("test.pdf", ContentFile(pdf_avec_emetteur), save=True)

        result = _generer_terrain_gdh(bdc_a_faire)

        doc = fitz.open(stream=result, filetype="pdf")
        texte = doc[0].get_text()
        doc.close()
        assert "AVIGNON" in texte

    def test_remplacement_par_etoiles(self, bdc_a_faire):
        """Les valeurs masquées doivent être remplacées par ***."""
        pdf_avec_emetteur = _creer_pdf_2_pages_avec_emetteur()
        bdc_a_faire.pdf_original.save("test.pdf", ContentFile(pdf_avec_emetteur), save=True)

        result = _generer_terrain_gdh(bdc_a_faire)

        doc = fitz.open(stream=result, filetype="pdf")
        texte = doc[0].get_text()
        doc.close()
        assert "***" in texte


# ─── 7.2 Tests _generer_terrain_erilia ────────────────────────────────────────


@pytest.mark.usefixtures("_mock_weasyprint")
class TestGenererTerrainERILIA:
    def test_pdf_genere(self, bdc_a_faire):
        from apps.bdc.terrain import _generer_terrain_erilia

        result = _generer_terrain_erilia(bdc_a_faire)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_pas_de_prix_dans_html(self, bdc_a_faire):
        """Vérifie que le template HTML ne contient aucun prix."""
        bdc_a_faire.montant_ht = Decimal("1071.40")
        bdc_a_faire.montant_tva = Decimal("107.14")
        bdc_a_faire.montant_ttc = Decimal("1178.54")
        bdc_a_faire.save(update_fields=["montant_ht", "montant_tva", "montant_ttc"])

        LignePrestation.objects.create(
            bdc=bdc_a_faire,
            designation="Peinture WC",
            quantite=Decimal("15"),
            unite="m²",
            prix_unitaire=Decimal("11.19"),
            montant=Decimal("167.85"),
            ordre=0,
        )

        lignes = bdc_a_faire.lignes_prestation.all()
        html = render_to_string(
            "bdc/terrain_erilia.html",
            {
                "bdc": bdc_a_faire,
                "lignes": lignes,
            },
        )

        assert "1071" not in html
        assert "107.14" not in html
        assert "1178" not in html
        assert "11.19" not in html
        assert "167.85" not in html
        # Mais la désignation et quantité sont présentes
        assert "Peinture WC" in html
        assert "15" in html


# ─── 7.3 Tests generer_pdf_terrain (dispatch) ────────────────────────────────


@pytest.mark.usefixtures("_mock_weasyprint")
class TestGenererPdfTerrain:
    def test_dispatch_gdh(self, bdc_a_faire):
        assert bdc_a_faire.bailleur.code == "GDH"
        pdf_2pages = _creer_pdf_2_pages()
        bdc_a_faire.pdf_original.save("test.pdf", ContentFile(pdf_2pages), save=True)

        bdc = generer_pdf_terrain(bdc_a_faire)

        assert bdc.pdf_terrain
        assert bdc.pdf_terrain.name

    def test_dispatch_erilia(self, bdc_a_faire, bailleur_erilia):
        bdc_a_faire.bailleur = bailleur_erilia
        bdc_a_faire.save(update_fields=["bailleur"])

        bdc = generer_pdf_terrain(bdc_a_faire)

        assert bdc.pdf_terrain
        assert bdc.pdf_terrain.name

    def test_bailleur_inconnu_fallback_erilia(self, bdc_a_faire):
        from apps.bdc.models import Bailleur

        autre = Bailleur.objects.create(nom="Autre Bailleur", code="AUTRE")
        bdc_a_faire.bailleur = autre
        bdc_a_faire.save(update_fields=["bailleur"])

        bdc = generer_pdf_terrain(bdc_a_faire)

        assert bdc.pdf_terrain
        assert bdc.pdf_terrain.name


# ─── 7.4 Tests intégration : attribution génère le PDF terrain ───────────────


@pytest.mark.usefixtures("_mock_weasyprint")
class TestAttributionGenereTerrainIntegration:
    def test_attribution_genere_pdf_terrain(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        pdf_2pages = _creer_pdf_2_pages()
        bdc_a_faire.pdf_original.save("test.pdf", ContentFile(pdf_2pages), save=True)

        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

        bdc.refresh_from_db()
        assert bdc.pdf_terrain

    def test_reattribution_regenere_pdf_terrain(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        pdf_2pages = _creer_pdf_2_pages()
        bdc_a_faire.pdf_original.save("test.pdf", ContentFile(pdf_2pages), save=True)

        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

        autre_st = SousTraitant.objects.create(nom="Martin", telephone="0600000000", actif=True)
        bdc = reattribuer_st(bdc, autre_st, Decimal("70"), utilisateur_cdt)

        bdc.refresh_from_db()
        assert bdc.pdf_terrain

    def test_attribution_reussit_meme_si_terrain_echoue(self, bdc_a_faire, sous_traitant, utilisateur_cdt):
        """L'attribution ne doit pas échouer si la génération terrain échoue."""
        # Pas de pdf_original → la génération GDH échouera
        bdc = attribuer_st(bdc_a_faire, sous_traitant, Decimal("65"), utilisateur_cdt)

        assert bdc.statut == StatutChoices.EN_COURS
        assert bdc.sous_traitant == sous_traitant


# ─── 7.5 Tests vue telecharger_terrain ────────────────────────────────────────


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


# ─── 7.6 Tests template detail : bouton BDC terrain ──────────────────────────


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
