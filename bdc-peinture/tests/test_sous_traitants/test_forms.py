import pytest

from apps.sous_traitants.forms import SousTraitantForm
from apps.sous_traitants.models import SousTraitant


@pytest.mark.django_db
class TestSousTraitantForm:
    def test_valid_form_minimal(self):
        form = SousTraitantForm(data={"nom": "Dupont Peinture", "telephone": "0612345678"})
        assert form.is_valid(), form.errors

    def test_valid_form_all_fields(self):
        form = SousTraitantForm(
            data={
                "nom": "Martin Déco",
                "siret": "12345678901234",
                "telephone": "0698765432",
                "email": "martin@test.fr",
                "adresse": "10 rue du Test",
                "code_postal": "84000",
                "ville": "Avignon",
            }
        )
        assert form.is_valid(), form.errors

    def test_siret_invalid_not_14_digits(self):
        form = SousTraitantForm(data={"nom": "Test", "telephone": "0600000000", "siret": "12345"})
        assert not form.is_valid()
        assert "siret" in form.errors

    def test_siret_invalid_letters(self):
        form = SousTraitantForm(data={"nom": "Test", "telephone": "0600000000", "siret": "ABCDEFGHIJKLMN"})
        assert not form.is_valid()
        assert "siret" in form.errors

    def test_siret_duplicate(self):
        SousTraitant.objects.create(nom="Existing", telephone="0611111111", siret="12345678901234")
        form = SousTraitantForm(data={"nom": "New", "telephone": "0622222222", "siret": "12345678901234"})
        assert not form.is_valid()
        assert "siret" in form.errors

    def test_siret_empty_is_valid(self):
        form = SousTraitantForm(data={"nom": "Sans SIRET", "telephone": "0633333333", "siret": ""})
        assert form.is_valid(), form.errors

    def test_nom_duplicate(self):
        SousTraitant.objects.create(nom="Dupont", telephone="0611111111")
        form = SousTraitantForm(data={"nom": "Dupont", "telephone": "0622222222"})
        assert not form.is_valid()
        assert "nom" in form.errors

    def test_siret_unique_on_edit_excludes_self(self):
        st = SousTraitant.objects.create(nom="Self", telephone="0600000000", siret="12345678901234")
        form = SousTraitantForm(
            data={"nom": "Self", "telephone": "0600000000", "siret": "12345678901234"}, instance=st
        )
        assert form.is_valid(), form.errors
