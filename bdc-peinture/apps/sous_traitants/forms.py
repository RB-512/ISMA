from django import forms

from .models import SousTraitant

_INPUT_CSS = (
    "w-full px-3 py-2 rounded-lg border border-[var(--color-border)] "
    "bg-[var(--color-surface)] text-[var(--color-text)] text-sm "
    "focus:ring-2 focus:ring-accent focus:border-accent"
)


class SousTraitantForm(forms.ModelForm):
    class Meta:
        model = SousTraitant
        fields = ["nom", "siret", "telephone", "email", "adresse", "code_postal", "ville"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": _INPUT_CSS}),
            "siret": forms.TextInput(attrs={"class": _INPUT_CSS, "placeholder": "14 chiffres", "maxlength": "14"}),
            "telephone": forms.TextInput(attrs={"class": _INPUT_CSS}),
            "email": forms.EmailInput(attrs={"class": _INPUT_CSS}),
            "adresse": forms.TextInput(attrs={"class": _INPUT_CSS}),
            "code_postal": forms.TextInput(attrs={"class": _INPUT_CSS, "maxlength": "5"}),
            "ville": forms.TextInput(attrs={"class": _INPUT_CSS}),
        }

    def clean_siret(self):
        siret = self.cleaned_data.get("siret", "").strip()
        if not siret:
            return siret
        if not siret.isdigit() or len(siret) != 14:
            raise forms.ValidationError("Le SIRET doit contenir exactement 14 chiffres.")
        qs = SousTraitant.objects.filter(siret=siret)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ce SIRET est déjà utilisé par un autre sous-traitant.")
        return siret
