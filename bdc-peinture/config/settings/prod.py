"""
Settings de production.
"""

from decouple import config

from .base import *  # noqa: F401, F403

DEBUG = False

# Sécurité HTTPS
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Cookies sécurisés
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

# Base de données
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

# Email via SMTP
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)

# Fichiers statiques servis par Nginx
STATIC_ROOT = "/data/static/"
MEDIA_ROOT = "/data/media/"

# Notifications d'erreurs aux administrateurs
ADMINS = [("Admin ISMA", "bybondecommande@gmail.com")]
SERVER_EMAIL = config("EMAIL_HOST_USER")

# Logging : fichier rotatif + email sur erreur 500
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/data/logs/django.log",
            "maxBytes": 10 * 1024 * 1024,  # 10 Mo
            "backupCount": 5,
            "formatter": "verbose",
        },
        "mail_admins": {
            "class": "django.utils.log.AdminEmailHandler",
            "level": "ERROR",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "apps": {
            "handlers": ["file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
