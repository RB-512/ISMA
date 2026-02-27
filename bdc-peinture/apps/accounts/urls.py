from django.urls import include, path

urlpatterns = [
    # django-allauth gère le login, logout, et les URLs d'authentification
    path("", include("allauth.urls")),
]
