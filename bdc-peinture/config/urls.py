"""
Routes principales de l'application BDC Peinture.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("gestion/", include(("apps.accounts.urls_gestion", "gestion"))),
    path("sous-traitants/", include("apps.sous_traitants.urls")),
    path("", include("apps.bdc.urls")),
]

# Servir les fichiers media via Django
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif not getattr(settings, "USE_NGINX_MEDIA", True):
    # LAN sans nginx : forcer le serving des media (static() refuse si DEBUG=False)
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
