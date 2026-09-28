#!/bin/sh
# Daily backups of the database and uploaded media, used by the `backup` service
# in docker-compose.prod.yml. Keeps the last BACKUP_KEEP_DAYS days (default 14).
#
# Restore:
#   gunzip -c /backups/db-YYYY-MM-DD.sql.gz | psql -h db -U "$POSTGRES_USER" "$POSTGRES_DB"
#   tar xzf /backups/media-YYYY-MM-DD.tgz -C /media
set -eu

KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"
INTERVAL="${BACKUP_INTERVAL_SECONDS:-86400}"
export PGPASSWORD="$POSTGRES_PASSWORD"

backup() {
    stamp=$(date +%F)
    echo "[backup] $(date -Iseconds) starting"
    pg_dump -h db -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "/backups/db-$stamp.sql.gz.tmp"
    mv "/backups/db-$stamp.sql.gz.tmp" "/backups/db-$stamp.sql.gz"
    tar czf "/backups/media-$stamp.tgz.tmp" -C /media .
    mv "/backups/media-$stamp.tgz.tmp" "/backups/media-$stamp.tgz"
    find /backups -name 'db-*.sql.gz' -mtime +"$KEEP_DAYS" -delete
    find /backups -name 'media-*.tgz' -mtime +"$KEEP_DAYS" -delete
    echo "[backup] done: db-$stamp.sql.gz, media-$stamp.tgz"
}

if [ "${1:-}" = "--once" ]; then
    backup
    exit 0
fi

while true; do
    backup || echo "[backup] FAILED" >&2
    sleep "$INTERVAL"
done
