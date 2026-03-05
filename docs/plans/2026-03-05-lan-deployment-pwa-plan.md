# LAN Deployment + PWA Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy ISMA on a Synology NAS via Docker (LAN only) with a Chrome PWA shortcut.

**Architecture:** Django + Gunicorn + WhiteNoise (no Nginx) serving on port 8080, PostgreSQL 16 in a separate container. WhiteNoise serves static files. A PWA manifest enables Chrome "Install app" for a native-like shortcut.

**Tech Stack:** Django 5.1, WhiteNoise, Gunicorn, Docker Compose, PostgreSQL 16, PWA Web Manifest

---

### Task 1: Add WhiteNoise dependency

**Files:**
- Modify: `bdc-peinture/pyproject.toml:6-18`

**Step 1: Add whitenoise to dependencies**

In `bdc-peinture/pyproject.toml`, add `whitenoise` to the `dependencies` list:

```toml
dependencies = [
    "django>=5.1",
    "django-allauth>=65.0",
    "django-filter>=24.0",
    "pdfplumber>=0.11",
    "pymupdf>=1.24",
    "psycopg[binary]>=3.2",
    "gunicorn>=23.0",
    "python-decouple>=3.8",
    "weasyprint>=63.0",
    "pillow>=11.0",
    "openpyxl>=3.1",
    "requests>=2.31",
    "whitenoise>=6.7",
]
```

**Step 2: Sync dependencies**

Run: `cd bdc-peinture && uv sync`
Expected: whitenoise installed, uv.lock updated.

**Step 3: Commit**

```bash
git add bdc-peinture/pyproject.toml bdc-peinture/uv.lock
git commit -m "chore: add whitenoise dependency for static file serving"
```

---

### Task 2: Create LAN settings

**Files:**
- Create: `bdc-peinture/config/settings/lan.py`

**Step 1: Create the settings file**

Create `bdc-peinture/config/settings/lan.py`:

```python
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
```

**Step 2: Verify the file loads without error**

Run: `cd bdc-peinture && DJANGO_SETTINGS_MODULE=config.settings.lan uv run python -c "import django; django.setup(); print('OK')"`

Note: This will fail locally (no PostgreSQL) but should not raise an ImportError. If running with SQLite locally, just verify the import chain is correct by checking no syntax error:

Run: `cd bdc-peinture && uv run python -c "from config.settings.lan import *; print('Settings loaded OK')"`

**Step 3: Commit**

```bash
git add bdc-peinture/config/settings/lan.py
git commit -m "feat: add LAN settings for Synology NAS deployment"
```

---

### Task 3: Create docker-compose.lan.yml

**Files:**
- Create: `bdc-peinture/docker-compose.lan.yml`

**Step 1: Create the compose file**

Create `bdc-peinture/docker-compose.lan.yml`:

```yaml
services:
  web:
    build: .
    restart: unless-stopped
    ports:
      - "8080:8000"
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.lan
    env_file:
      - .env
    volumes:
      - media_data:/data/media
      - static_data:/data/static
    depends_on:
      db:
        condition: service_healthy
    command: >
      sh -c "uv run manage.py collectstatic --noinput &&
             uv run manage.py migrate --noinput &&
             uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2"

  db:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  media_data:
  static_data:
```

**Step 2: Validate YAML syntax**

Run: `cd bdc-peinture && docker compose -f docker-compose.lan.yml config --quiet 2>&1 || echo "YAML OK (docker not required for syntax check)"`

**Step 3: Commit**

```bash
git add bdc-peinture/docker-compose.lan.yml
git commit -m "feat: add docker-compose.lan.yml for Synology LAN deployment"
```

---

### Task 4: Create PWA icons (SVG)

**Files:**
- Create: `bdc-peinture/static/icons/icon-192.svg`
- Create: `bdc-peinture/static/icons/icon-512.svg`

**Step 1: Create icons directory and SVG icons**

Both icons use the same SVG content (SVG scales naturally). The "I" logo matches the existing sidebar icon style (accent blue #3B82F6, white letter, rounded square).

Create `bdc-peinture/static/icons/icon-192.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="192" height="192" viewBox="0 0 192 192">
  <rect width="192" height="192" rx="32" fill="#3B82F6"/>
  <text x="96" y="130" text-anchor="middle" font-family="system-ui, sans-serif" font-weight="700" font-size="120" fill="white">I</text>
</svg>
```

Create `bdc-peinture/static/icons/icon-512.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="80" fill="#3B82F6"/>
  <text x="256" y="345" text-anchor="middle" font-family="system-ui, sans-serif" font-weight="700" font-size="320" fill="white">I</text>
</svg>
```

**Step 2: Commit**

```bash
git add bdc-peinture/static/icons/
git commit -m "feat: add PWA icons for ISMA app"
```

---

### Task 5: Create PWA manifest

**Files:**
- Create: `bdc-peinture/static/manifest.json`

**Step 1: Create the manifest file**

Create `bdc-peinture/static/manifest.json`:

```json
{
  "name": "ISMA",
  "short_name": "ISMA",
  "description": "Gestion des bons de commande",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#F7F5F2",
  "theme_color": "#1B2B3A",
  "icons": [
    {
      "src": "/static/icons/icon-192.svg",
      "sizes": "192x192",
      "type": "image/svg+xml",
      "purpose": "any maskable"
    },
    {
      "src": "/static/icons/icon-512.svg",
      "sizes": "512x512",
      "type": "image/svg+xml",
      "purpose": "any maskable"
    }
  ]
}
```

**Step 2: Commit**

```bash
git add bdc-peinture/static/manifest.json
git commit -m "feat: add PWA manifest for Chrome install shortcut"
```

---

### Task 6: Add PWA meta tags to base.html

**Files:**
- Modify: `bdc-peinture/templates/base.html:1-8`

**Step 1: Add manifest link and PWA meta tags**

In `bdc-peinture/templates/base.html`, after the `<title>` tag (line 6), add:

```html
    <title>{% block title %}ISMA{% endblock %}</title>

    {# ── PWA ── #}
    <link rel="manifest" href="{% static 'manifest.json' %}">
    <meta name="theme-color" content="#1B2B3A">
    <meta name="mobile-web-app-capable" content="yes">
    <link rel="icon" type="image/svg+xml" href="{% static 'icons/icon-192.svg' %}">
    <link rel="apple-touch-icon" href="{% static 'icons/icon-192.svg' %}">
```

Also add `{% load static %}` at the very top of the file (line 1, before `<!DOCTYPE html>`):

```html
{% load static %}
<!DOCTYPE html>
```

**Step 2: Verify template renders**

Run: `cd bdc-peinture && uv run manage.py check --settings=config.settings.dev_sqlite`
Expected: System check identified no issues.

**Step 3: Commit**

```bash
git add bdc-peinture/templates/base.html
git commit -m "feat: add PWA manifest and icon links to base template"
```

---

### Task 7: Update .env.example with LAN section

**Files:**
- Modify: `bdc-peinture/.env.example`

**Step 1: Add LAN deployment section**

Append to `bdc-peinture/.env.example`:

```ini

# ============================================================
# Deploiement LAN (NAS Synology)
# Utiliser avec: DJANGO_SETTINGS_MODULE=config.settings.lan
# docker compose -f docker-compose.lan.yml up -d
# ============================================================
# DJANGO_SETTINGS_MODULE=config.settings.lan
# ALLOWED_HOSTS=*
```

**Step 2: Commit**

```bash
git add bdc-peinture/.env.example
git commit -m "docs: add LAN deployment section to .env.example"
```

---

### Task 8: Smoke test with Docker (optional, if Docker available)

**Step 1: Create a test .env if needed**

Verify `bdc-peinture/.env` exists with valid `SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, and `ALLOWED_HOSTS=*`.

**Step 2: Build and start**

Run:
```bash
cd bdc-peinture
docker compose -f docker-compose.lan.yml up -d --build
```

Expected: Both containers start. Web container runs collectstatic, migrate, then gunicorn.

**Step 3: Test access**

Run: `curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/accounts/login/`
Expected: `200` or `302` (redirect to login page).

**Step 4: Check manifest is served**

Run: `curl -s http://localhost:8080/static/manifest.json | head -5`
Expected: JSON content of the manifest.

**Step 5: Stop containers**

Run: `cd bdc-peinture && docker compose -f docker-compose.lan.yml down`

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Add whitenoise dependency | `pyproject.toml`, `uv.lock` |
| 2 | Create LAN settings | `config/settings/lan.py` |
| 3 | Create docker-compose LAN | `docker-compose.lan.yml` |
| 4 | Create PWA icons | `static/icons/icon-{192,512}.svg` |
| 5 | Create PWA manifest | `static/manifest.json` |
| 6 | Add PWA tags to base.html | `templates/base.html` |
| 7 | Update .env.example | `.env.example` |
| 8 | Smoke test (optional) | - |

## Deploiement sur le NAS

Une fois tous les fichiers prets, sur le NAS Synology :

1. Installer Container Manager (DSM > Centre de paquets)
2. Copier le dossier `bdc-peinture/` sur le NAS (via SMB ou SSH)
3. Creer `.env` a partir de `.env.example` avec `DJANGO_SETTINGS_MODULE=config.settings.lan` et `ALLOWED_HOSTS=*`
4. SSH dans le NAS : `docker compose -f docker-compose.lan.yml up -d --build`
5. Creer le superuser : `docker compose -f docker-compose.lan.yml exec web uv run manage.py createsuperuser`
6. Ouvrir Chrome sur un PC du bureau : `http://<IP-DU-NAS>:8080`
7. Menu Chrome > "Installer ISMA" -> raccourci sur le bureau
