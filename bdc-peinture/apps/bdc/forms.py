from django import forms

from apps.sous_traitants.models import SousTraitant

from .models import BonDeCommande


class BonDeCommandeForm(forms.ModelForm):
    """
    Formulaire de création / modification d'un BDC.
    Pré-rempli depuis les données extraites du PDF bailleur.

    Champs exclus (gérés automatiquement) :
    - statut : déterminé par la logique métier (services.py)
    - cree_par : l'utilisateur connecté
    - pdf_original : géré séparément via la session
    - created_at / updated_at : auto_now
    """

    class Meta:
        model = BonDeCommande
        fields = [
            "numero_bdc",
            "numero_marche",
            "bailleur",
            "date_emission",
            "programme_residence",
            "adresse",
            "code_postal",
            "ville",
            "logement_numero",
            "logement_type",
            "logement_etage",
            "logement_porte",
            "objet_travaux",
            "delai_execution",
            "occupant_nom",
            "occupant_telephone",
            "occupant_email",
            "emetteur_nom",
            "emetteur_telephone",
            "montant_ht",
            "montant_tva",
            "montant_ttc",
            "occupation",
            "type_acces",
            "acces_complement",
            "rdv_date",
            "notes",
            "sous_traitant",
            "montant_st",
            "pourcentage_st",
        ]
        widgets = {
            "date_emission": forms.DateInput(attrs={"type": "date"}),
            "delai_execution": forms.DateInput(attrs={"type": "date"}),
            "rdv_date": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "objet_travaux": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_numero_bdc(self) -> str:
        """Bloque la création si le numéro BDC existe déjà en base."""
        numero = self.cleaned_data.get("numero_bdc", "").strip()
        if not numero:
            raise forms.ValidationError("Le numéro BDC est obligatoire.")

        qs = BonDeCommande.objects.filter(numero_bdc=numero)
        # Exclure l'instance courante en cas de modification
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(f"Le BDC n°{numero} existe déjà dans le système.")
        return numero


class AttributionForm(forms.Form):
    """Formulaire d'attribution d'un BDC à un sous-traitant."""

    sous_traitant = forms.ModelChoiceField(
        queryset=SousTraitant.objects.filter(actif=True),
        label="Sous-traitant",
        empty_label="— Choisir un sous-traitant —",
    )
    mode_attribution = forms.ChoiceField(
        choices=[("pourcentage", "Pourcentage"), ("forfait", "Forfait")],
        initial="pourcentage",
        required=False,
        widget=forms.HiddenInput(),
    )
    pourcentage_st = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        label="Pourcentage ST (%)",
        min_value=0,
        max_value=100,
        required=False,
    )
    commentaire = forms.CharField(
        required=False,
        label="Commentaire pour le sous-traitant",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Commentaire ajouté dans l'email au ST…"}),
    )

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get("mode_attribution") or "pourcentage"
        cleaned["mode_attribution"] = mode
        if mode == "pourcentage" and not cleaned.get("pourcentage_st"):
            self.add_error("pourcentage_st", "Le pourcentage est obligatoire en mode pourcentage.")
        return cleaned


STATUT_EXPORT_CHOICES = [
    ("", "Tous (à facturer + facturé)"),
    ("A_FACTURER", "À facturer"),
    ("FACTURE", "Facturé"),
]


class ExportFacturationForm(forms.Form):
    """Formulaire de filtres pour l'export facturation."""

    statut = forms.ChoiceField(
        choices=STATUT_EXPORT_CHOICES,
        required=False,
        label="Statut",
    )
    sous_traitant = forms.ModelChoiceField(
        queryset=SousTraitant.objects.filter(actif=True),
        required=False,
        label="Sous-traitant",
        empty_label="Tous les sous-traitants",
    )
    date_du = forms.DateField(
        required=False,
        label="Date réalisation du",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    date_au = forms.DateField(
        required=False,
        label="Date réalisation au",
        widget=forms.DateInput(attrs={"type": "date"}),
    )


class BDCEditionForm(forms.ModelForm):
    """
    Formulaire d'édition des champs manuels depuis la fiche détail / sidebar.
    Seuls les champs saisissables par la secrétaire sont inclus.
    Inclut un champ hidden pour déclencher une transition de statut en même temps.
    """

    nouveau_statut = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = BonDeCommande
        fields = [
            "type_bon",
            "occupation",
            "type_acces",
            "acces_complement",
            "rdv_date",
            "notes",
        ]
        widgets = {
            "rdv_date": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "notes": "Commentaires",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["notes"].required = False
        self.fields["type_bon"].required = False

    def clean(self):
        cleaned = super().clean()
        nouveau_statut = cleaned.get("nouveau_statut")

        # Validations obligatoires seulement lors d'une transition
        if nouveau_statut:
            occupation = cleaned.get("occupation")
            if not occupation:
                self.add_error("occupation", "Ce champ est obligatoire pour valider le contrôle.")
            elif occupation == "VACANT":
                type_acces = cleaned.get("type_acces")
                if not type_acces:
                    self.add_error("type_acces", "Ce champ est obligatoire pour un logement vacant.")
                elif type_acces != "PASS_CHANTIER" and not cleaned.get("acces_complement"):
                    self.add_error("acces_complement", "Ce champ est obligatoire pour un logement vacant.")
            elif occupation == "OCCUPE":
                if not cleaned.get("rdv_date"):
                    self.add_error("rdv_date", "La date de RDV est obligatoire pour un logement occupé.")

        return cleaned
