# Deploiement LAN Synology + PWA Chrome

**Date** : 2026-03-05
**Statut** : Approuve

## Contexte

Heberger l'application ISMA sur le NAS Synology de l'entreprise, accessible uniquement depuis le reseau local. Un raccourci Chrome (PWA) permettra d'ouvrir l'app comme une application native.

## Architecture

```
PC Bureau --> http://192.168.x.x:8080 --> NAS Synology (Docker)
                                           +-- web: Django + Gunicorn + WhiteNoise
                                           +-- db: PostgreSQL 16
```

Pas de Nginx, pas de SSL, pas de Certbot. WhiteNoise sert les fichiers statiques.

## Fichiers

| Fichier | Action |
|---------|--------|
| `config/settings/lan.py` | Nouveau - settings LAN |
| `docker-compose.lan.yml` | Nouveau - web + db, port 8080 |
| `deploy.sh` | Nouveau - collectstatic + migrate |
| `static/manifest.json` | Nouveau - PWA manifest |
| `static/icons/icon-192.svg` | Nouveau - icone PWA |
| `static/icons/icon-512.svg` | Nouveau - icone PWA |
| `templates/base.html` | Modifier - link manifest + meta PWA |
| `pyproject.toml` | Modifier - ajouter whitenoise |
| `.env.example` | Nouveau - template variables |

## Settings LAN (`lan.py`)

- Herite de `base.py`
- `DEBUG = False`
- Pas de SSL redirect ni cookies secure
- WhiteNoise dans MIDDLEWARE
- PostgreSQL via env vars
- `ALLOWED_HOSTS` configurable (defaut: `*`)

## PWA

- `manifest.json` avec `display: standalone`
- Icones SVG 192x192 et 512x512 (logo "I" bleu accent #3B82F6)
- Chrome propose "Installer ISMA" -> fenetre separee sans barre d'URL

## Docker Compose LAN

- Service `web` : build Dockerfile existant, port 8080:8000
- Service `db` : PostgreSQL 16 avec healthcheck
- Volumes : postgres_data, media_data, static_data
- `DJANGO_SETTINGS_MODULE: config.settings.lan`
