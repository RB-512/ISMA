"""
Routes principales de l'application BDC Peinture.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("sous-traitants/", include("apps.sous_traitants.urls")),
    path("", include("apps.bdc.urls")),
]

# En développement : servir les fichiers media via Django
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
