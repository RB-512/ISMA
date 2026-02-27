from django.urls import path

from . import views

app_name = "sous_traitants"

urlpatterns = [
    path("", views.SousTraitantListView.as_view(), name="list"),
]
