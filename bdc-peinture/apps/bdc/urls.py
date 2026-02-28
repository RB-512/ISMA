from django.urls import path

from . import views

app_name = "bdc"

urlpatterns = [
    path("", views.liste_bdc, name="index"),
    path("upload/", views.upload_pdf, name="upload"),
    path("nouveau/", views.creer_bdc, name="nouveau"),
    path("<int:pk>/sidebar/", views.detail_sidebar, name="detail_sidebar"),
    path("<int:pk>/", views.detail_bdc, name="detail"),
    path("<int:pk>/modifier/", views.modifier_bdc, name="modifier"),
    path("<int:pk>/statut/", views.changer_statut_bdc, name="changer_statut"),
    path("<int:pk>/attribuer/", views.attribuer_bdc, name="attribuer"),
    path("<int:pk>/reattribuer/", views.reattribuer_bdc, name="reattribuer"),
    path("<int:pk>/terrain/", views.telecharger_terrain, name="terrain"),
    path("<int:pk>/valider/", views.valider_realisation_bdc, name="valider_realisation"),
    path("<int:pk>/facturer/", views.valider_facturation_bdc, name="valider_facturation"),
    path("export/", views.export_facturation, name="export_facturation"),
    path("recoupement/", views.recoupement_st_liste, name="recoupement_liste"),
    path("recoupement/<int:st_pk>/", views.recoupement_st_detail, name="recoupement_detail"),
]
