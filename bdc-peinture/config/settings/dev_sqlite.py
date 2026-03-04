"""
Settings de développement avec SQLite (pour makemigrations sans Docker).
"""

from .base import *  # noqa: F401, F403

DEBUG = True

INTERNAL_IPS = ["127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}
