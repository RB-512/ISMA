"""
Settings pour deploiement LAN (NAS Synology).
Pas de SSL, WhiteNoise pour les fichiers statiques.
"""

from decouple import config

from .base import *  # noqa: F401, F403

DEBUG = False

# WhiteNoise pour servir les fichiers statiques sans Nginx
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Base de donnees PostgreSQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="db"),
        "PORT": config("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
    }
}

# Fichiers statiques et media (volumes Docker)
STATIC_ROOT = "/data/static/"
MEDIA_ROOT = "/data/media/"

# Pas de Nginx en LAN : Django sert les fichiers media
USE_NGINX_MEDIA = False

# Pas de securite HTTPS en LAN
SESSION_COOKIE_HTTPONLY = True

# Email (optionnel, console par defaut)
if config("EMAIL_HOST", default=""):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = config("EMAIL_HOST")
    EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
    EMAIL_HOST_USER = config("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
    EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
    DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)
