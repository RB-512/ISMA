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
    path("gestion/", include(("apps.accounts.urls_gestion", "gestion"))),
    path("sous-traitants/", include("apps.sous_traitants.urls")),
    path("", include("apps.bdc.urls")),
]

# Servir les fichiers media via Django (dev + LAN sans nginx)
if settings.DEBUG or not getattr(settings, "USE_NGINX_MEDIA", True):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
