from django.urls import path

from . import views

app_name = "bdc"

urlpatterns = [
    path("", views.liste_bdc, name="index"),
    path("upload/", views.upload_pdf, name="upload"),
    path("nouveau/", views.creer_bdc, name="nouveau"),
    path("<int:pk>/", views.detail_bdc, name="detail"),
    path("<int:pk>/modifier/", views.modifier_bdc, name="modifier"),
    path("<int:pk>/statut/", views.changer_statut_bdc, name="changer_statut"),
    path("<int:pk>/attribuer/", views.attribuer_bdc, name="attribuer"),
    path("<int:pk>/reattribuer/", views.reattribuer_bdc, name="reattribuer"),
]
