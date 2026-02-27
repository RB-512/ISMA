from django.urls import path

from . import views

app_name = "bdc"

urlpatterns = [
    path("", views.liste_bdc, name="index"),
    path("upload/", views.upload_pdf, name="upload"),
    path("nouveau/", views.creer_bdc, name="nouveau"),
    path("<int:pk>/", views.detail_bdc, name="detail"),
]
