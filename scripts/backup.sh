#!/usr/bin/env bash
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-/opt/week11-production-deployment}"
COMPOSE_FILE="${COMPOSE_FILE:-$DEPLOY_DIR/docker/docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-$DEPLOY_DIR/.env}"

BACKUP_DIR="${BACKUP_DIR:-$DEPLOY_DIR/backups}"
mkdir -p "$BACKUP_DIR"

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-postgres}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"

timestamp="$(date -u +"%Y%m%dT%H%M%SZ")"
backup_file="$BACKUP_DIR/postgres_backup_${timestamp}.sql.gz"

if [ -z "$POSTGRES_PASSWORD" ]; then
  echo "POSTGRES_PASSWORD is not set; backup cannot proceed." >&2
  exit 1
fi

# Stream pg_dump out of the Postgres container, compress, and store on the host.
docker compose -f "$COMPOSE_FILE" exec -T \
  -e PGPASSWORD="$POSTGRES_PASSWORD" \
  "$POSTGRES_HOST" \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  | gzip -c > "$backup_file"

# Keep last 7 backups.
ls -1t "$BACKUP_DIR"/postgres_backup_*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm -f

echo "Backup created: $backup_file"

