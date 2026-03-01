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

# Emails dans la console en dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Django Debug Toolbar (optionnel)
INTERNAL_IPS = ["127.0.0.1"]
