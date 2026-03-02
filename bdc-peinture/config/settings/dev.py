"""
Settings de développement local.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

# Base de données PostgreSQL (Docker Compose)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "bdc_peinture",
        "USER": "bdc_user",
        "PASSWORD": "bdc_password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

# Emails : SMTP si configuré dans .env, sinon console
if config("EMAIL_HOST", default=""):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = config("EMAIL_HOST")
    EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
    EMAIL_HOST_USER = config("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
    EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
    DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Django Debug Toolbar (optionnel)
INTERNAL_IPS = ["127.0.0.1"]
