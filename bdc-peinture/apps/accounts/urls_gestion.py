from django.urls import path

from apps.accounts import views

app_name = "gestion"

urlpatterns = [
    path("", views.liste_utilisateurs, name="liste"),
    path("creer/", views.creer_utilisateur, name="creer"),
    path("<int:pk>/role/", views.modifier_role, name="modifier_role"),
    path("<int:pk>/desactiver/", views.desactiver_utilisateur, name="desactiver"),
]
