from django import forms

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
            "numero_bdc", "numero_marche", "bailleur", "date_emission",
            "programme_residence", "adresse", "code_postal", "ville",
            "logement_numero", "logement_type", "logement_etage", "logement_porte",
            "objet_travaux", "delai_execution",
            "occupant_nom", "occupant_telephone", "occupant_email",
            "emetteur_nom", "emetteur_telephone",
            "montant_ht", "montant_tva", "montant_ttc",
            "occupation", "modalite_acces", "rdv_pris", "rdv_date", "notes",
            "sous_traitant", "montant_st", "pourcentage_st",
        ]
        widgets = {
            "date_emission": forms.DateInput(attrs={"type": "date"}),
            "delai_execution": forms.DateInput(attrs={"type": "date"}),
            "rdv_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "objet_travaux": forms.Textarea(attrs={"rows": 3}),
            "modalite_acces": forms.Textarea(attrs={"rows": 2}),
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
            raise forms.ValidationError(
                f"Le BDC n°{numero} existe déjà dans le système."
            )
        return numero


class BDCEditionForm(forms.ModelForm):
    """
    Formulaire d'édition des champs manuels depuis la fiche détail.
    Seuls les champs saisissables par la secrétaire sont inclus.
    """

    class Meta:
        model = BonDeCommande
        fields = ["occupation", "modalite_acces", "rdv_pris", "rdv_date", "notes"]
        widgets = {
            "rdv_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "modalite_acces": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
