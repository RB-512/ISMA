from django.contrib import admin

from .models import SousTraitant


@admin.register(SousTraitant)
class SousTraitantAdmin(admin.ModelAdmin):
    list_display = ("nom", "telephone", "email", "actif")
    list_filter = ("actif",)
    search_fields = ("nom", "telephone", "email")
