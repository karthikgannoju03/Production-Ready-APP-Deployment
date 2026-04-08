# Operations

## Service Management

From the `week11-production-deployment` directory:

Development:
```sh
docker compose -f docker/docker-compose.yml up -d --build
docker compose -f docker/docker-compose.yml logs -f web
```

Production:
```sh
docker compose -f docker/docker-compose.prod.yml up -d --build
docker compose -f docker/docker-compose.prod.yml logs -f web
```

Restart a single service:
```sh
docker compose -f docker/docker-compose.prod.yml restart web
```

## Log Monitoring

The app emits structured JSON logs to stdout/stderr. Use:
```sh
docker compose -f docker/docker-compose.prod.yml logs -f web
```

You can correlate logs using the `request_id` returned in the `X-Request-ID` header.

## Scaling Procedures

Nginx forwards traffic to the `web` upstream.

For horizontal scaling, run multiple `web` instances that share the same service name (Swarm/Kubernetes), or switch Nginx upstreams to point to additional `web` backends.

