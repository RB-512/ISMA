from django.contrib import admin

from .models import Bailleur, BonDeCommande, ChecklistItem, HistoriqueAction, LignePrestation, ReleveFacturation


@admin.register(Bailleur)
class BailleurAdmin(admin.ModelAdmin):
    list_display = ("nom", "code")
    search_fields = ("nom", "code")


@admin.register(BonDeCommande)
class BonDeCommandeAdmin(admin.ModelAdmin):
    list_display = ("numero_bdc", "bailleur", "statut", "delai_execution", "created_at")
    list_filter = ("statut", "bailleur", "sous_traitant")
    search_fields = ("numero_bdc", "adresse", "occupant_nom")
    readonly_fields = ("created_at", "updated_at")


@admin.register(LignePrestation)
class LignePrestationAdmin(admin.ModelAdmin):
    list_display = ("bdc", "designation", "quantite", "unite", "prix_unitaire", "montant")


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ("libelle", "ordre", "actif")
    list_editable = ("ordre", "actif")


@admin.register(HistoriqueAction)
class HistoriqueActionAdmin(admin.ModelAdmin):
    list_display = ("bdc", "utilisateur", "action", "created_at")
    list_filter = ("action",)
    readonly_fields = ("created_at",)


@admin.register(ReleveFacturation)
class ReleveFacturationAdmin(admin.ModelAdmin):
    list_display = ("numero", "sous_traitant", "statut", "date_creation", "date_validation")
    list_filter = ("statut", "sous_traitant")
    readonly_fields = ("date_creation",)
