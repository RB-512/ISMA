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
docker compose -f docker-compose.prod.yml exec -T web \
    tar czf - /data/media/ \
    > "$BACKUP_DIR/media/${DATE}_media.tar.gz"

# 3. Rotation : garder 30 jours
find "$BACKUP_DIR/db" -name "*.sql.gz" -mtime +30 -delete
find "$BACKUP_DIR/media" -name "*.tar.gz" -mtime +30 -delete

echo "$(date): Backup terminé — DB: ${DATE}.sql.gz, Media: ${DATE}_media.tar.gz"
