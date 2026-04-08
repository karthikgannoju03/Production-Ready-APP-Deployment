#!/usr/bin/env bash
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-/opt/week11-production-deployment}"
COMPOSE_FILE="${COMPOSE_FILE:-$DEPLOY_DIR/docker/docker-compose.prod.yml}"

if [ -d "$DEPLOY_DIR" ]; then
  if [ -d "$DEPLOY_DIR/.git" ]; then
    echo "Pulling latest code in $DEPLOY_DIR..."
    git -C "$DEPLOY_DIR" pull --ff-only
  else
    echo "DEPLOY_DIR is not a git repo: $DEPLOY_DIR/.git missing" >&2
    exit 1
  fi
else
  echo "DEPLOY_DIR does not exist: $DEPLOY_DIR" >&2
  exit 1
fi

echo "Building web image..."
docker compose -f "$COMPOSE_FILE" build web

echo "Starting / updating services..."
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

echo "Restarting core services..."
docker compose -f "$COMPOSE_FILE" restart web nginx prometheus grafana || true

echo "Deployment complete."

