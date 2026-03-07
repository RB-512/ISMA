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
    path("<int:pk>/supprimer/", views.supprimer_utilisateur, name="supprimer"),
    # Checklist de contrôle
    path("checklist/", views.checklist_liste, name="checklist_liste"),
    path("checklist/<int:pk>/modifier/", views.checklist_modifier, name="checklist_modifier"),
    path("checklist/<int:pk>/supprimer/", views.checklist_supprimer, name="checklist_supprimer"),
    # Config masquage PDF par bailleur
    path("config-bailleurs/", views.config_bailleurs, name="config_bailleurs"),
    path("config-bailleurs/<int:pk>/form/", views.config_bailleur_form, name="config_bailleur_form"),
]
