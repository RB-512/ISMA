# Design — Déploiement BDC Peinture sur VPS

**Date :** 2026-03-01
**Statut :** Validé
**Référence :** ARCHITECTURE.md §2.4, §9

---

## 1. Contexte

Application Django interne pour une entreprise de peinture (~30 employés).
**2-3 utilisateurs** (secrétaire + CDT), **50-150 BDC/mois**.
Usage : bureau + accès distant (CDT en déplacement).
Email : Gmail / Google Workspace (SMTP).

---

## 2. Décision d'architecture

Conforme à `ARCHITECTURE.md §2.4` :

- **Hébergement** : VPS (OVH ou Hetzner), ~4-5 EUR/mois
- **Conteneurisation** : Docker + Docker Compose
- **Reverse proxy** : Nginx
- **HTTPS** : Let's Encrypt via Certbot
- **Base de données** : PostgreSQL 16 (conteneur Docker)
- **Stockage fichiers** : filesystem local `/data/media/` (volume Docker persistant)
- **Email** : Gmail SMTP (mot de passe d'application Google)
- **CI/CD** : GitHub Actions (lint + tests + deploy SSH)

---

## 3. Architecture Docker Compose (production)

3 services :

```
┌───────────────────────────────────────────────┐
│                 VPS (4 EUR/mois)               │
│                                               │
│  ┌────────────────────────────────────────┐   │
│  │          docker-compose.prod.yml        │   │
│  │                                        │   │
│  │  nginx (:80, :443)                     │   │
│  │    ├── HTTPS + Let's Encrypt (Certbot) │   │
│  │    ├── Sert /data/static/ directement  │   │
│  │    └── Proxy → web:8000               │   │
│  │                                        │   │
│  │  web (Django + Gunicorn)               │   │
│  │    └── Connexion → db:5432             │   │
│  │                                        │   │
│  │  db (PostgreSQL 16)                    │   │
│  │    └── Volume /data/postgres/          │   │
│  └────────────────────────────────────────┘   │
│                                               │
│  Volumes Docker persistants :                  │
│    - postgres_data → /var/lib/postgresql/data │
│    - media_data    → /data/media/ (PDFs)      │
│    - static_data   → /data/static/ (CSS/JS)   │
│    - certbot_data  → /etc/letsencrypt/        │
└───────────────────────────────────────────────┘
```

---

## 4. Fichiers à créer

| Fichier | Description |
|---|---|
| `docker-compose.prod.yml` | Compose production : nginx + web + db + volumes |
| `nginx/nginx.conf` | Config Nginx : HTTP→HTTPS redirect, proxy Gunicorn, statiques |
| `.env.example` | Template de toutes les variables d'environnement requises |
| `scripts/initial_setup.sh` | Setup initial du VPS (Docker install, clone, certbot) |
| `scripts/deploy.sh` | Redéploiement (git pull + docker compose up --build) |
| `scripts/backup.sh` | Backup quotidien (pg_dump + rsync media) |
| `.github/workflows/ci.yml` | CI : lint (Ruff) + tests (pytest) sur chaque push/PR |
| `.github/workflows/deploy.yml` | CD : deploy SSH automatique sur push `main` |

---

## 5. Variables d'environnement (`.env`)

```
# Django
SECRET_KEY=...
DJANGO_SETTINGS_MODULE=config.settings.prod
ALLOWED_HOSTS=bdc-peinture.fr,www.bdc-peinture.fr

# Base de données
DB_NAME=bdc_peinture
DB_USER=bdc_user
DB_PASSWORD=...
DB_HOST=db
DB_PORT=5432

# Email (Gmail SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=contact@entreprise.fr
EMAIL_HOST_PASSWORD=...  # mot de passe d'application Google (pas le mdp du compte)
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=contact@entreprise.fr

# Fichiers
MEDIA_ROOT=/data/media/

# SMS (optionnel MVP)
SMS_BACKEND=apps.notifications.backends.LogSmsBackend
```

---

## 6. Étapes de mise en production (manuel)

1. **Acheter un VPS** (Hetzner CX22 ~4 EUR/mois ou OVH VPS Starter)
2. **Acheter un nom de domaine** (~10 EUR/an, ex: bdc-peinture.fr)
3. **Configurer DNS** : enregistrement A pointant vers l'IP du VPS
4. **Lancer `scripts/initial_setup.sh`** sur le VPS
5. **Configurer `.env`** avec les vraies valeurs
6. **Lancer `docker compose -f docker-compose.prod.yml up -d`**
7. **Certbot obtient le certificat HTTPS** automatiquement
8. **Appliquer les migrations** : `docker compose exec web uv run manage.py migrate`
9. **Créer les comptes** secrétaire + CDT via Django admin
10. **Configurer le cron** pour les backups quotidiens

---

## 7. CI/CD GitHub Actions

**Sur chaque push/PR :**
- Lint Ruff (`ruff check .` + `ruff format --check .`)
- Tests pytest (avec PostgreSQL en service GitHub Actions)

**Sur push `main` (deploy automatique) :**
- SSH vers le VPS
- `git pull origin main`
- `docker compose -f docker-compose.prod.yml up -d --build`
- `docker compose exec web uv run manage.py migrate`
- `docker compose exec web uv run manage.py collectstatic --noinput`

---

## 8. Backups

Script `scripts/backup.sh` (cron quotidien à 2h00) :

```bash
# Dump PostgreSQL
docker compose exec db pg_dump -U bdc_user bdc_peinture > /backup/db_$(date +%Y%m%d).sql

# Backup media (PDFs)
rsync -av /data/media/ /backup/media/

# Rotation : garder 30 jours
find /backup -name "*.sql" -mtime +30 -delete
```

---

## 9. Décisions repoussées à V2+

Conformes à `ARCHITECTURE.md §12` :

- Stockage objet S3 pour les PDFs (si volume augmente)
- Tâches asynchrones Celery + Redis (si envoi SMS/email devient bloquant)
- CDN pour les statiques
