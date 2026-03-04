from django.urls import path

from apps.sous_traitants import views

app_name = "sous_traitants"

urlpatterns = [
    path("", views.liste_sous_traitants, name="list"),
    path("creer/", views.creer_sous_traitant, name="creer"),
    path("<int:pk>/modifier/", views.modifier_sous_traitant, name="modifier"),
    path("<int:pk>/desactiver/", views.desactiver_sous_traitant, name="desactiver"),
    path("<int:pk>/reactiver/", views.reactiver_sous_traitant, name="reactiver"),
    path("<int:pk>/supprimer/", views.supprimer_sous_traitant, name="supprimer"),
]
