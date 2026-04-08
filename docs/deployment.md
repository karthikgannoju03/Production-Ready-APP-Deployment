# Deployment (Docker + Compose + CI/CD)

This project is a production-ready Flask API packaged as a multi-container system:

`web` (Flask/Gunicorn) behind `nginx`, with `postgres` + `redis`, and observability via `prometheus` + `grafana`.

## Environment Setup

1. Create an environment file based on `.env.example`:
   - Copy `./.env.example` to `./.env`
2. Ensure you set a strong `SECRET_KEY` in `.env`.
3. Verify the variables used by Compose:
   - `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
   - `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`
   - `GF_SECURITY_ADMIN_USER`, `GF_SECURITY_ADMIN_PASSWORD`

## Local Docker (Development)

From the `week11-production-deployment` directory:

```sh
docker compose -f docker/docker-compose.yml up -d --build
```

Access:
- API: `http://localhost:8000/health`
- Metrics: `http://localhost:8000/metrics`

## Production Docker (Single Host)

From the `week11-production-deployment` directory:

```sh
docker compose -f docker/docker-compose.prod.yml up -d --build
```

Access:
- Web (behind nginx): `http://localhost/health`
- Prometheus UI: `http://localhost:9090`
- Grafana UI: `http://localhost:3000`

## Database Migrations

Migrations in this sample are schema bootstrap via SQLAlchemy metadata:

Run:

```sh
docker compose -f docker/docker-compose.prod.yml exec -T web ./scripts/migrate.sh
```

## Backup PostgreSQL

Run:

```sh
bash ./scripts/backup.sh
```

Backups are stored under `./backups/` on the host and rotated (keep last 7).

## CI/CD Explanation (GitHub Actions)

### CI (`.github/workflows/ci.yml`)
- Runs on `push`
- Installs Python deps
- Executes:
  - `pytest`
  - `python -m black .`
  - `python -m isort .`
  - `mypy src tests`

### CD (`.github/workflows/cd-staging.yml`, `.github/workflows/cd-production.yml`)
- Builds and pushes a production Docker image to your registry
- Deploys via SSH by running `scripts/deploy.sh` on the target host

### Required GitHub Secrets (CD)
- `DOCKER_REGISTRY_URL`
- `DOCKER_REGISTRY_USERNAME`
- `DOCKER_REGISTRY_PASSWORD`
- `DOCKER_IMAGE_NAME`
- `SSH_HOST`
- `SSH_USER`
- `SSH_PRIVATE_KEY`
- `DEPLOY_DIR` (production)
- `DEPLOY_DIR_STAGING` (staging)

