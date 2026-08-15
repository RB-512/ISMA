from django.urls import path

from . import views

app_name = "changelog"

urlpatterns = [
    path("nouveautes/", views.version_list, name="version_list"),
]
