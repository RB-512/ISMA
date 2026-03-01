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
