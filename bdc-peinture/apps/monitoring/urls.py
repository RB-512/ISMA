from django.urls import path

from . import views

app_name = "monitoring"

urlpatterns = [
    path("erreurs/", views.error_list, name="error_list"),
    path("erreurs/<int:pk>/", views.error_detail, name="error_detail"),
]
