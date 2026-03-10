from django.urls import path

from . import views, views_bibliotheque

app_name = "bdc"

urlpatterns = [
    path("", views.liste_bdc, name="index"),
    path("upload/", views.upload_pdf, name="upload"),
    path("nouveau/", views.creer_bdc, name="nouveau"),
    path("<int:pk>/sidebar/", views.detail_sidebar, name="detail_sidebar"),
    path("<int:pk>/", views.detail_bdc, name="detail"),
    path("<int:pk>/modifier/", views.modifier_bdc, name="modifier"),
    path("<int:pk>/sidebar-action/", views.sidebar_save_and_transition, name="sidebar_action"),
    path("<int:pk>/controle/", views.controle_bdc, name="controle"),
    path("<int:pk>/statut/", views.changer_statut_bdc, name="changer_statut"),
    path("<int:pk>/attribuer/", views.attribuer_bdc, name="attribuer"),
    path("<int:pk>/reattribuer/", views.reattribuer_bdc, name="reattribuer"),
    path("<int:pk>/attribution-form/", views.attribution_partial, name="attribution_partial"),
    path("<int:pk>/attribution/", views.attribution_split, name="attribution_split"),
    path("<int:pk>/valider/", views.valider_realisation_bdc, name="valider_realisation"),
    path("<int:pk>/facturer/", views.valider_facturation_bdc, name="valider_facturation"),
    path("<int:pk>/sidebar-checklist/", views.sidebar_checklist, name="sidebar_checklist"),
    path("<int:pk>/renvoyer/", views.renvoyer_controle_bdc, name="renvoyer_controle"),
    path("<int:pk>/pdf-st/", views.pdf_masque_preview, name="pdf_masque_preview"),
    path("export/", views.export_facturation, name="export_facturation"),
    path("recoupement/", views.recoupement_st_liste, name="recoupement_liste"),
    path("recoupement/<int:st_pk>/", views.recoupement_st_detail, name="recoupement_detail"),
    # ─── Relevés de facturation ─────────────────────────────────────────────
    path("releves/<int:st_pk>/creer/", views.releve_creer, name="releve_creer"),
    path("releves/<int:pk>/", views.releve_detail, name="releve_detail"),
    path("releves/<int:pk>/valider/", views.releve_valider, name="releve_valider"),
    path("releves/<int:pk>/retirer/<int:bdc_pk>/", views.releve_retirer_bdc, name="releve_retirer_bdc"),
    path("releves/<int:pk>/pdf/", views.releve_pdf, name="releve_pdf"),
    path("releves/<int:pk>/excel/", views.releve_excel, name="releve_excel"),
    path("releves/st/<int:st_pk>/", views.releve_historique, name="releve_historique"),
    # ─── Bibliothèque de prix ──────────────────────────────────────────────
    path("bibliotheque/", views_bibliotheque.bibliotheque_liste, name="bibliotheque"),
    path("bibliotheque/ajouter/", views_bibliotheque.bibliotheque_ajouter, name="bibliotheque_ajouter"),
    path(
        "bibliotheque/<int:pk>/modifier/",
        views_bibliotheque.bibliotheque_modifier,
        name="bibliotheque_modifier",
    ),
    path(
        "bibliotheque/<int:pk>/supprimer/",
        views_bibliotheque.bibliotheque_supprimer,
        name="bibliotheque_supprimer",
    ),
]
