from django.contrib import admin

from .models import Version


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ["numero", "date_mise_en_ligne", "created_by", "created_at"]
    ordering = ["-date_mise_en_ligne", "-created_at"]
    exclude = ["created_by"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
