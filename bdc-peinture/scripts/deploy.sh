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
