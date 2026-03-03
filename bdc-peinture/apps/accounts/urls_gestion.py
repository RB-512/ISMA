from django.urls import path

from apps.accounts import views

app_name = "gestion"

urlpatterns = [
    path("", views.liste_utilisateurs, name="liste"),
    path("creer/", views.creer_utilisateur, name="creer"),
    path("<int:pk>/role/", views.modifier_role, name="modifier_role"),
    path("<int:pk>/desactiver/", views.desactiver_utilisateur, name="desactiver"),
    path("<int:pk>/modifier/", views.modifier_utilisateur, name="modifier"),
    path("<int:pk>/reset-password/", views.reset_password_utilisateur, name="reset_password"),
    path("<int:pk>/reactiver/", views.reactiver_utilisateur, name="reactiver"),
]
