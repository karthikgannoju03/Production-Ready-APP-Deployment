# Troubleshooting

## Container Failures

1. Inspect logs for the failing service:
   ```sh
   docker compose -f docker/docker-compose.prod.yml logs -f <service>
   ```
2. Check health status:
   ```sh
   docker compose -f docker/docker-compose.prod.yml ps
   ```

## Database Connection Issues

1. Verify Postgres health:
   ```sh
   docker compose -f docker/docker-compose.prod.yml exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
   ```
2. Ensure your environment variables match Compose:
   - `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
3. If `/health` shows `database.connected=false`, check:
   - Postgres container logs
   - network connectivity between `web` and `postgres`

## Redis Connectivity Issues

If `/health` is degraded and `redis.connected=false`:
1. Verify Redis container health:
   ```sh
   docker compose -f docker/docker-compose.prod.yml ps redis
   ```
2. Confirm `REDIS_HOST` and `REDIS_PORT` values match your Compose network.

## Metrics / Monitoring Not Showing

If Grafana panels are empty:
1. Confirm Prometheus is scraping:
   - `http://localhost:9090/targets`
2. Confirm the app exposes:
   - `http://<web-host>:8000/metrics`

