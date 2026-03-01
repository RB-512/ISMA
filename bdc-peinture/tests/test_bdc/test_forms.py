"""Tests des formulaires BDC."""

import pytest

from apps.bdc.forms import BDCEditionForm

pytestmark = pytest.mark.django_db


class TestBDCEditionForm:
    def test_fields_include_type_acces_and_acces_complement(self):
        form = BDCEditionForm()
        assert "type_acces" in form.fields
        assert "acces_complement" in form.fields

    def test_fields_exclude_rdv_pris(self):
        form = BDCEditionForm()
        assert "rdv_pris" not in form.fields

    def test_nouveau_statut_hidden_field(self):
        form = BDCEditionForm()
        assert "nouveau_statut" in form.fields
        assert form.fields["nouveau_statut"].required is False
        assert form.fields["nouveau_statut"].widget.input_type == "hidden"
