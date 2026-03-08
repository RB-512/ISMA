"""
Settings de développement avec SQLite (pour makemigrations sans Docker).
"""

from decouple import config

from .base import *  # noqa: F401, F403

DEBUG = True

INTERNAL_IPS = ["127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
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
