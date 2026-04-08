# Production-Ready APP Deployment System

Enterprise-grade Dockerized Flask API deployment with:
`web` behind `nginx`, `postgres`, `redis`, plus monitoring via `prometheus` and `grafana`.

## Architecture (Text Diagram)

```
           +------------------+
           |     Clients     |
           +------------------+
                    |
                    v
             +-------------+
             |    NGINX    |  rate limiting + security headers
             +-------------+
                    |
                    v
             +------------------+
             |   web (gunicorn)|
             | Flask API         |
             | /health /metrics |
             +------------------+
                    |             \
                    |              \ (caching/limits)
                    v               v
             +-------------+   +--------+
             |  Postgres   |   | Redis  |
             +-------------+   +--------+
                    |
                    v
          +----------------------+
          | Prometheus + Alerts |
          +----------------------+
                    |
                    v
               +---------+
               | Grafana |
               +---------+
```

## Setup

1. Copy environment template:
   - `./.env.example` -> `./.env`
2. Review required variables in `.env` (at minimum: `SECRET_KEY`).

## Deployment

### Development

```sh
docker compose -f docker/docker-compose.yml up -d --build
```

### Production (Single Host)

```sh
docker compose -f docker/docker-compose.prod.yml up -d --build
```

Run migrations:
```sh
docker compose -f docker/docker-compose.prod.yml exec -T web ./scripts/migrate.sh
```

Backups:
```sh
./scripts/backup.sh
```

## Monitoring

Prometheus scrapes `web` at `/metrics` and evaluates alerts from `monitoring/alerts.yml`.

Open:
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

Grafana dashboard is stored at `monitoring/grafana-dashboard.json` (import it in the Grafana UI).

## CI/CD

- CI: runs on `push` (`.github/workflows/ci.yml`) and executes `pytest`, `black`, `isort`, and `mypy`.
- CD: builds and pushes the production Docker image, then deploys via SSH (`.github/workflows/cd-*.yml`).

