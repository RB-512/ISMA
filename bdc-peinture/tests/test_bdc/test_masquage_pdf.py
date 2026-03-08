import fitz
import pytest

from apps.bdc.masquage_pdf import generer_pdf_masque


def _creer_pdf_simple():
    """Cree un PDF 1 page avec du texte pour les tests."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    page.insert_text((100, 100), "Montant HT : 1234,56 EUR", fontsize=12)
    page.insert_text((100, 200), "Adresse : 12 rue des Tests", fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.mark.django_db
class TestGenererPdfMasqueZones:
    def test_masque_zone_rectangulaire(self, bdc_a_traiter):
        bdc_a_traiter.bailleur.zones_masquage = [{"x": 90, "y": 85, "w": 300, "h": 25, "page": 1, "label": "Montant"}]
        bdc_a_traiter.bailleur.save()
        from django.core.files.base import ContentFile

        bdc_a_traiter.pdf_original.save("test.pdf", ContentFile(_creer_pdf_simple()))
        result = generer_pdf_masque(bdc_a_traiter)
        assert result is not None
        assert isinstance(result, bytes)
        doc = fitz.open(stream=result, filetype="pdf")
        assert len(doc) == 1
        doc.close()

    def test_retourne_none_sans_pdf_original(self, bdc_a_traiter):
        bdc_a_traiter.bailleur.zones_masquage = [{"x": 0, "y": 0, "w": 100, "h": 100, "page": 1, "label": "test"}]
        bdc_a_traiter.bailleur.save()
        result = generer_pdf_masque(bdc_a_traiter)
        assert result is None

    def test_retourne_none_sans_zones(self, bdc_a_traiter):
        from django.core.files.base import ContentFile

        bdc_a_traiter.pdf_original.save("test.pdf", ContentFile(_creer_pdf_simple()))
        result = generer_pdf_masque(bdc_a_traiter)
        assert result is None

    def test_filtrage_pages(self, bdc_a_traiter):
        bdc_a_traiter.bailleur.zones_masquage = [{"x": 90, "y": 85, "w": 300, "h": 25, "page": 1, "label": "test"}]
        bdc_a_traiter.bailleur.save()
        doc = fitz.open()
        doc.new_page(width=595, height=842)
        doc.new_page(width=595, height=842)
        pdf_2pages = doc.tobytes()
        doc.close()
        from django.core.files.base import ContentFile

        bdc_a_traiter.pdf_original.save("test.pdf", ContentFile(pdf_2pages))
        result = generer_pdf_masque(bdc_a_traiter, pages=[1])
        assert result is not None
        doc = fitz.open(stream=result, filetype="pdf")
        assert len(doc) == 1
        doc.close()

    def test_zone_page_inexistante_ignoree(self, bdc_a_traiter):
        bdc_a_traiter.bailleur.zones_masquage = [{"x": 0, "y": 0, "w": 100, "h": 100, "page": 5, "label": "page 5"}]
        bdc_a_traiter.bailleur.save()
        from django.core.files.base import ContentFile

        bdc_a_traiter.pdf_original.save("test.pdf", ContentFile(_creer_pdf_simple()))
        result = generer_pdf_masque(bdc_a_traiter)
        assert result is not None
