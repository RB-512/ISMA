"""
Settings pour les tests (pytest).
"""

from .base import *  # noqa: F401, F403

DEBUG = False

# Base de données SQLite en mémoire pour les tests unitaires (rapide, sans Docker)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Accélère les tests (pas de hachage sécurisé)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Emails silencieux en test
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Media vers un dossier temporaire
import tempfile  # noqa: E402

MEDIA_ROOT = tempfile.mkdtemp()
