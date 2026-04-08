# Security

## Security Policies (What This Setup Does)

### Transport and HTTPS Readiness
- Flask uses `flask-talisman` to apply TLS-related headers based on `FORCE_HTTPS`.
- Nginx has a commented HTTPS/TLS block; enable it when you provide certificates.

### Response Headers
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`

### Rate Limiting
- Flask-Limiter enforces request rate limits (backed by Redis when enabled).
- Nginx also rate limits `/api/` traffic.

### Input Validation
- Endpoints validate JSON payloads and enforce basic constraints (for example, message length).
- Payload sizes are limited via Flask `MAX_CONTENT_LENGTH`.

### Least Privilege
- Containers run as a non-root user (`appuser`) in the web image.

## Backup Procedures

Use `scripts/backup.sh` on the host where the production compose stack runs:
```sh
bash ./scripts/backup.sh
```

Backups are rotated and only the last 7 `.sql.gz` files are retained.

## Incident Response (High-Level)

1. Confirm blast radius:
   - Check `/health` and Prometheus targets.
2. Look for authentication/traffic anomalies:
   - Inspect nginx logs and app JSON logs.
3. Capture evidence:
   - Take a database backup (if safe) and note timestamps.
4. Contain:
   - Scale down or restart affected services.
5. Recover:
   - Restore from backups if necessary.

