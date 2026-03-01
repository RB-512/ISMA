# Déploiement VPS — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Mettre en production l'application BDC Peinture sur un VPS avec Docker Compose, Nginx, HTTPS Let's Encrypt, et CI/CD GitHub Actions.

**Architecture:** 3 conteneurs Docker Compose (nginx, web, db). Nginx est le reverse proxy qui gère HTTPS via Let's Encrypt (Certbot) et sert les fichiers statiques directement. Gunicorn tourne dans le conteneur `web`. PostgreSQL 16 dans le conteneur `db` avec volume persistant.

**Tech Stack:** Docker Compose, Nginx, Certbot (Let's Encrypt), Gunicorn, PostgreSQL 16, GitHub Actions, Gmail SMTP.

---

## Prérequis (à faire manuellement AVANT de commencer)

1. Acheter un VPS (Hetzner CX22 ~4 EUR/mois ou OVH VPS Starter)
   - OS : Ubuntu 22.04 LTS
   - Notez l'IP publique du VPS
2. Acheter un nom de domaine (ex: `bdc-peinture.fr`, ~10 EUR/an chez OVH ou Gandi)
3. Configurer le DNS :
   - Enregistrement A : `bdc-peinture.fr` → IP du VPS
   - Enregistrement A : `www.bdc-peinture.fr` → IP du VPS
   - Attendre la propagation DNS (5-30 min)
4. Avoir un mot de passe d'application Google :
   - Compte Google → Sécurité → Validation en 2 étapes → Mots de passe d'application
   - Notez le mot de passe généré (16 caractères)
5. Accès SSH au VPS (clé SSH ou mot de passe)

---

## Task 1 : Mettre à jour le Dockerfile

WeasyPrint (génération PDF ERILIA) nécessite des dépendances système supplémentaires non présentes dans le Dockerfile actuel.

**Files:**
- Modify: `bdc-peinture/Dockerfile`

**Step 1 : Lire le Dockerfile actuel**

```
FROM python:3.12-slim
...
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*
```

Il manque les dépendances WeasyPrint.

**Step 2 : Remplacer le bloc apt-get**

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Dépendances système (libpq pour PostgreSQL, WeasyPrint pour PDF)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Installer uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

COPY . .

RUN uv run manage.py collectstatic --noinput --settings=config.settings.prod || true

EXPOSE 8000

CMD ["uv", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
```

**Step 3 : Vérifier que le build fonctionne en local**

```bash
cd bdc-peinture/
docker build -t bdc-peinture-test .
```

Résultat attendu : `Successfully built <image-id>`

**Step 4 : Commit**

```bash
git add bdc-peinture/Dockerfile
git commit -m "fix: add WeasyPrint system dependencies to Dockerfile"
```

---

## Task 2 : Créer docker-compose.prod.yml

Le `docker-compose.yml` existant est pour le dev (pas de nginx, pas de SSL). On crée un compose dédié à la production.

**Files:**
- Create: `bdc-peinture/docker-compose.prod.yml`

**Step 1 : Créer le fichier**

```yaml
services:
  nginx:
    image: nginx:1.27-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - static_data:/data/static:ro
      - media_data:/data/media:ro
      - certbot_webroot:/var/www/certbot:ro
      - certbot_certs:/etc/letsencrypt:ro
    depends_on:
      - web

  web:
    build: .
    restart: unless-stopped
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.prod
    env_file:
      - .env
    volumes:
      - media_data:/data/media
      - static_data:/data/static
    depends_on:
      db:
        condition: service_healthy
    expose:
      - "8000"

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

  certbot:
    image: certbot/certbot
    volumes:
      - certbot_webroot:/var/www/certbot
      - certbot_certs:/etc/letsencrypt
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

volumes:
  postgres_data:
  media_data:
  static_data:
  certbot_webroot:
  certbot_certs:
```

**Step 2 : Commit**

```bash
git add bdc-peinture/docker-compose.prod.yml
git commit -m "feat: add docker-compose.prod.yml with nginx + certbot"
```

---

## Task 3 : Créer la configuration Nginx

Nginx gère le HTTPS, le redirect HTTP→HTTPS, les fichiers statiques et le proxy vers Gunicorn.

**Files:**
- Create: `bdc-peinture/nginx/nginx.conf`

**Step 1 : Créer le répertoire et le fichier**

> Remplacez `bdc-peinture.fr` par votre vrai nom de domaine dans le fichier ci-dessous.

```nginx
# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name bdc-peinture.fr www.bdc-peinture.fr;

    # Nécessaire pour Certbot (vérification de domaine)
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS
server {
    listen 443 ssl;
    server_name bdc-peinture.fr www.bdc-peinture.fr;

    ssl_certificate /etc/letsencrypt/live/bdc-peinture.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bdc-peinture.fr/privkey.pem;

    # Sécurité SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    # Fichiers statiques servis directement par Nginx (rapide)
    location /static/ {
        alias /data/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Fichiers media : NE PAS servir directement (Django vérifie les permissions)
    # Les PDFs passent toujours par Gunicorn

    # Proxy vers Gunicorn
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout pour l'upload de PDFs
        proxy_read_timeout 60s;
        client_max_body_size 20M;
    }
}
```

**Step 2 : Commit**

```bash
git add bdc-peinture/nginx/
git commit -m "feat: add Nginx config for production (HTTPS, static files, proxy)"
```

---

## Task 4 : Mettre à jour .env.example

Le `.env.example` actuel est incomplet (références à Twilio, valeurs incorrectes pour la prod).

**Files:**
- Modify: `bdc-peinture/.env.example`

**Step 1 : Remplacer le contenu**

```bash
# ============================================================
# Variables d'environnement — BDC Peinture
# Copier vers .env et remplir les vraies valeurs
# NE JAMAIS committer le fichier .env
# ============================================================

# Django
SECRET_KEY=changez-moi-par-une-cle-secrete-de-50-caracteres-minimum
DJANGO_SETTINGS_MODULE=config.settings.prod
ALLOWED_HOSTS=bdc-peinture.fr,www.bdc-peinture.fr

# Base de données PostgreSQL
DB_NAME=bdc_peinture
DB_USER=bdc_user
DB_PASSWORD=changez-moi-mot-de-passe-fort
DB_HOST=db
DB_PORT=5432

# Fichiers media (PDFs uploadés) — volume Docker
MEDIA_ROOT=/data/media/

# Email — Gmail SMTP
# Utiliser un "mot de passe d'application" Google (pas le mot de passe du compte)
# Google Account → Sécurité → Mots de passe d'application
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=contact@votre-entreprise.fr
EMAIL_HOST_PASSWORD=xxxx-xxxx-xxxx-xxxx
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=contact@votre-entreprise.fr

# SMS (optionnel en MVP — LogBackend par défaut = logs uniquement)
SMS_BACKEND=apps.notifications.backends.LogSmsBackend
# Pour OVH SMS en production :
# SMS_BACKEND=apps.notifications.backends.OvhSmsBackend
# OVH_APPLICATION_KEY=
# OVH_APPLICATION_SECRET=
# OVH_CONSUMER_KEY=
# OVH_SMS_SERVICE_NAME=
# OVH_SMS_SENDER=
```

**Step 2 : Commit**

```bash
git add bdc-peinture/.env.example
git commit -m "docs: update .env.example for production (Gmail SMTP, complete variables)"
```

---

## Task 5 : Créer le script de setup initial du VPS

Ce script s'exécute une seule fois sur un VPS vierge Ubuntu 22.04.

**Files:**
- Create: `bdc-peinture/scripts/initial_setup.sh`

**Step 1 : Créer le répertoire scripts**

```bash
mkdir -p bdc-peinture/scripts/
```

**Step 2 : Créer le fichier**

```bash
#!/bin/bash
# Setup initial du VPS Ubuntu 22.04
# Usage : bash scripts/initial_setup.sh
# Prérequis : être connecté en SSH sur le VPS en tant que root ou sudo

set -e

REPO_URL="https://github.com/VOTRE-ORG/bdc-peinture.git"  # À modifier
APP_DIR="/opt/bdc-peinture"
DOMAIN="bdc-peinture.fr"  # À modifier

echo "=== 1. Mise à jour système ==="
apt-get update && apt-get upgrade -y

echo "=== 2. Installation Docker ==="
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "=== 3. Clone du dépôt ==="
mkdir -p "$APP_DIR"
git clone "$REPO_URL" "$APP_DIR"
cd "$APP_DIR/bdc-peinture"

echo "=== 4. Créer le fichier .env ==="
cp .env.example .env
echo ""
echo ">>> IMPORTANT : éditez maintenant le fichier .env avec vos vraies valeurs"
echo ">>> Commande : nano $APP_DIR/bdc-peinture/.env"
echo ">>> Appuyez sur Entrée quand c'est fait..."
read -r

echo "=== 5. Démarrer les services (sans SSL d'abord) ==="
# On lance nginx en mode HTTP seul pour que Certbot puisse valider le domaine
docker compose -f docker-compose.prod.yml up -d db web nginx

echo "=== 6. Obtenir le certificat SSL ==="
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email admin@"$DOMAIN" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    -d www."$DOMAIN"

echo "=== 7. Redémarrer Nginx avec SSL ==="
docker compose -f docker-compose.prod.yml restart nginx

echo "=== 8. Migrations et données initiales ==="
docker compose -f docker-compose.prod.yml exec web uv run manage.py migrate
docker compose -f docker-compose.prod.yml exec web uv run manage.py collectstatic --noinput

echo "=== 9. Créer le superutilisateur ==="
docker compose -f docker-compose.prod.yml exec web uv run manage.py createsuperuser

echo "=== 10. Configurer le renouvellement SSL automatique (cron) ==="
(crontab -l 2>/dev/null; echo "0 3 * * * cd $APP_DIR/bdc-peinture && docker compose -f docker-compose.prod.yml run --rm certbot renew && docker compose -f docker-compose.prod.yml restart nginx") | crontab -

echo "=== 11. Configurer les backups (cron) ==="
(crontab -l 2>/dev/null; echo "0 2 * * * bash $APP_DIR/bdc-peinture/scripts/backup.sh >> /var/log/bdc-backup.log 2>&1") | crontab -

echo ""
echo "=== Setup terminé ! ==="
echo "Application accessible sur : https://$DOMAIN"
```

**Step 3 : Rendre exécutable**

```bash
chmod +x bdc-peinture/scripts/initial_setup.sh
```

**Step 4 : Commit**

```bash
git add bdc-peinture/scripts/
git commit -m "feat: add initial VPS setup script"
```

---

## Task 6 : Créer le script de déploiement

Ce script est utilisé pour redéployer l'application après chaque mise à jour du code.

**Files:**
- Create: `bdc-peinture/scripts/deploy.sh`

**Step 1 : Créer le fichier**

```bash
#!/bin/bash
# Redéploiement de l'application BDC Peinture
# Usage : bash scripts/deploy.sh
# À exécuter sur le VPS depuis /opt/bdc-peinture/

set -e

APP_DIR="/opt/bdc-peinture/bdc-peinture"
cd "$APP_DIR"

echo "=== Déploiement BDC Peinture ==="
echo "$(date): Début du déploiement"

echo ">>> 1. Récupération du code..."
git pull origin main

echo ">>> 2. Build et redémarrage des conteneurs..."
docker compose -f docker-compose.prod.yml up -d --build

echo ">>> 3. Migrations..."
docker compose -f docker-compose.prod.yml exec web uv run manage.py migrate --noinput

echo ">>> 4. Collecte des fichiers statiques..."
docker compose -f docker-compose.prod.yml exec web uv run manage.py collectstatic --noinput

echo "$(date): Déploiement terminé !"
```

**Step 2 : Rendre exécutable et commiter**

```bash
chmod +x bdc-peinture/scripts/deploy.sh
git add bdc-peinture/scripts/deploy.sh
git commit -m "feat: add deploy script"
```

---

## Task 7 : Créer le script de backup

**Files:**
- Create: `bdc-peinture/scripts/backup.sh`

**Step 1 : Créer le fichier**

```bash
#!/bin/bash
# Backup quotidien : base de données + fichiers media
# Exécuté par cron à 02h00 chaque nuit

set -e

APP_DIR="/opt/bdc-peinture/bdc-peinture"
BACKUP_DIR="/opt/bdc-peinture/backups"
DATE=$(date +%Y%m%d)

mkdir -p "$BACKUP_DIR/db" "$BACKUP_DIR/media"

echo "$(date): Début backup"

# 1. Backup base de données
cd "$APP_DIR"
DB_USER=$(grep DB_USER .env | cut -d= -f2)
DB_NAME=$(grep DB_NAME .env | cut -d= -f2)

docker compose -f docker-compose.prod.yml exec -T db \
    pg_dump -U "$DB_USER" "$DB_NAME" \
    > "$BACKUP_DIR/db/${DATE}.sql"

gzip -f "$BACKUP_DIR/db/${DATE}.sql"

# 2. Backup media (PDFs)
# Les volumes Docker sont dans /var/lib/docker/volumes/
# On copie depuis le conteneur web
docker compose -f docker-compose.prod.yml exec -T web \
    tar czf - /data/media/ \
    > "$BACKUP_DIR/media/${DATE}_media.tar.gz"

# 3. Rotation : garder 30 jours
find "$BACKUP_DIR/db" -name "*.sql.gz" -mtime +30 -delete
find "$BACKUP_DIR/media" -name "*.tar.gz" -mtime +30 -delete

echo "$(date): Backup terminé — DB: ${DATE}.sql.gz, Media: ${DATE}_media.tar.gz"
```

**Step 2 : Rendre exécutable et commiter**

```bash
chmod +x bdc-peinture/scripts/backup.sh
git add bdc-peinture/scripts/backup.sh
git commit -m "feat: add daily backup script (DB + media, 30 days retention)"
```

---

## Task 8 : Créer le workflow GitHub Actions CI

Tests automatiques sur chaque push et pull request.

**Files:**
- Create: `bdc-peinture/.github/workflows/ci.yml`

**Step 1 : Créer le répertoire et le fichier**

```bash
mkdir -p bdc-peinture/.github/workflows/
```

```yaml
name: CI

on:
  push:
    branches: [ main, feat/* ]
  pull_request:
    branches: [ main ]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: bdc_test
          POSTGRES_USER: bdc_user
          POSTGRES_PASSWORD: bdc_password
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        working-directory: bdc-peinture
        run: uv sync

      - name: Lint with Ruff
        working-directory: bdc-peinture
        run: |
          uv run ruff check .
          uv run ruff format --check .

      - name: Run tests
        working-directory: bdc-peinture
        env:
          DB_NAME: bdc_test
          DB_USER: bdc_user
          DB_PASSWORD: bdc_password
          DB_HOST: localhost
          DB_PORT: 5432
          SECRET_KEY: test-secret-key-not-for-production
        run: uv run pytest -v --tb=short
```

**Step 2 : Commit**

```bash
git add bdc-peinture/.github/
git commit -m "feat: add GitHub Actions CI (lint + tests)"
```

---

## Task 9 : Créer le workflow GitHub Actions CD (déploiement automatique)

Déploiement automatique sur le VPS à chaque push sur `main`.

**Files:**
- Create: `bdc-peinture/.github/workflows/deploy.yml`

**Step 1 : Configurer les secrets GitHub**

Dans votre dépôt GitHub → Settings → Secrets and variables → Actions, ajouter :

| Secret | Valeur |
|---|---|
| `VPS_HOST` | IP ou hostname du VPS |
| `VPS_USER` | Utilisateur SSH (ex: `ubuntu` ou `root`) |
| `VPS_SSH_KEY` | Contenu de votre clé privée SSH (`cat ~/.ssh/id_rsa`) |

**Step 2 : Créer le workflow**

```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    needs: []  # Pas de dépendance au CI — ajouter "lint-and-test" si vous voulez l'ordre

    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            bash /opt/bdc-peinture/bdc-peinture/scripts/deploy.sh
```

> **Note :** Si vous préférez déclencher le déploiement seulement après que les tests CI passent, modifiez `needs: []` en `needs: [lint-and-test]` et mettez les deux jobs dans le même fichier ou ajoutez une dépendance inter-workflows.

**Step 3 : Commit**

```bash
git add bdc-peinture/.github/workflows/deploy.yml
git commit -m "feat: add GitHub Actions CD (auto-deploy on main push via SSH)"
```

---

## Task 10 : Vérifier .gitignore

S'assurer que `.env` n'est pas commité.

**Files:**
- Verify: `bdc-peinture/.gitignore`

**Step 1 : Vérifier que .env est ignoré**

```bash
cat bdc-peinture/.gitignore | grep .env
```

Attendu : `.env` présent. Si absent :

```bash
echo ".env" >> bdc-peinture/.gitignore
git add bdc-peinture/.gitignore
git commit -m "fix: ensure .env is gitignored"
```

**Step 2 : Vérifier que .env n'est pas dans l'index git**

```bash
git ls-files bdc-peinture/.env
```

Attendu : aucun output (le fichier n'est pas tracké).

---

## Task 11 : Setup du VPS et première mise en production

**Prérequis :** DNS propagé, VPS accessible en SSH.

**Step 1 : Se connecter au VPS**

```bash
ssh ubuntu@IP_DU_VPS
```

**Step 2 : Cloner le repo et lancer le setup**

```bash
git clone https://github.com/VOTRE-ORG/bdc-peinture.git /opt/bdc-peinture
bash /opt/bdc-peinture/bdc-peinture/scripts/initial_setup.sh
```

Suivre les instructions interactives :
- Remplir `.env` avec les vraies valeurs
- Créer le superutilisateur Django

**Step 3 : Vérifier que l'application tourne**

```bash
# Statut des conteneurs
docker compose -f /opt/bdc-peinture/bdc-peinture/docker-compose.prod.yml ps

# Logs en temps réel
docker compose -f /opt/bdc-peinture/bdc-peinture/docker-compose.prod.yml logs -f
```

Attendu : 4 conteneurs en état `Up` (nginx, web, db, certbot)

**Step 4 : Tester l'accès HTTPS**

Ouvrir dans le navigateur : `https://bdc-peinture.fr`

Attendu : page de login BDC Peinture avec cadenas HTTPS vert.

**Step 5 : Créer les utilisateurs métier via l'admin Django**

```
https://bdc-peinture.fr/admin/
```

- Créer un utilisateur pour la secrétaire → groupe "Secrétaire"
- Créer un utilisateur pour le CDT → groupe "CDT"

**Step 6 : Configurer les secrets GitHub Actions**

Dans GitHub → Settings → Secrets → Actions :
- `VPS_HOST` = IP du VPS
- `VPS_USER` = `ubuntu` (ou votre user)
- `VPS_SSH_KEY` = contenu de la clé privée SSH

**Step 7 : Tester le déploiement automatique**

```bash
# En local, faire un commit quelconque sur main et pousser
git push origin main
```

Vérifier dans GitHub → Actions que le workflow "Deploy" passe au vert.

---

## Résumé des fichiers créés

```
bdc-peinture/
├── Dockerfile                          (modifié — dépendances WeasyPrint)
├── docker-compose.prod.yml             (créé — nginx + web + db + certbot)
├── nginx/
│   └── nginx.conf                      (créé — HTTPS, statiques, proxy)
├── .env.example                        (mis à jour — complet pour la prod)
├── scripts/
│   ├── initial_setup.sh                (créé — setup VPS vierge)
│   ├── deploy.sh                       (créé — redéploiement)
│   └── backup.sh                       (créé — backup quotidien)
└── .github/
    └── workflows/
        ├── ci.yml                      (créé — lint + tests)
        └── deploy.yml                  (créé — deploy SSH auto)
```

## Commandes utiles après la mise en production

```bash
# Voir les logs
docker compose -f docker-compose.prod.yml logs -f web

# Redémarrer un service
docker compose -f docker-compose.prod.yml restart web

# Lancer une migration manuellement
docker compose -f docker-compose.prod.yml exec web uv run manage.py migrate

# Ouvrir un shell Django
docker compose -f docker-compose.prod.yml exec web uv run manage.py shell

# Voir l'état des backups
ls -lh /opt/bdc-peinture/backups/db/
```
