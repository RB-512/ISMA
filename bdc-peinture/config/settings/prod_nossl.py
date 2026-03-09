"""Production sans SSL (accès par IP, pas de nom de domaine)."""

from .prod import *  # noqa: F401, F403

SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
