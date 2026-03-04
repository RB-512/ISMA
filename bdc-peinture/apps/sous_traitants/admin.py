from django.contrib import admin

from .models import SousTraitant


@admin.register(SousTraitant)
class SousTraitantAdmin(admin.ModelAdmin):
    list_display = ("nom", "siret", "telephone", "email", "ville", "actif")
    list_filter = ("actif", "ville")
    search_fields = ("nom", "siret", "telephone", "email", "ville")
