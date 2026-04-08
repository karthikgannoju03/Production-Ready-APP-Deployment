from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime
from typing import Any

import psutil
import redis as redis_lib
from flask import Flask, Response, g, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from redis import Redis
from sqlalchemy import DateTime, Integer, String, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool
from werkzeug.exceptions import HTTPException

from config import BaseConfig, get_config_class


class Base(DeclarativeBase):
    """Declarative base for database models."""


class ExampleRecord(Base):
    __tablename__ = "example_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message: Mapped[str] = mapped_column(String(length=200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )


# Prometheus metrics (module-level to avoid double-registration).
REQUESTS_TOTAL = Counter(
    "app_requests_total",
    "Total requests served",
    labelnames=["method", "endpoint", "status"],
)
ERRORS_TOTAL = Counter(
    "app_errors_total",
    "Total errors served",
    labelnames=["method", "endpoint", "error_type"],
)
REQUEST_DURATION_SECONDS = Histogram(
    "app_request_duration_seconds",
    "Request duration in seconds",
    labelnames=["method", "endpoint", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)

APP_CPU_PERCENT = Gauge("app_cpu_percent", "Process CPU usage percent (best-effort)")
APP_MEMORY_MB = Gauge("app_memory_mb", "Process RSS memory usage in MB (best-effort)")

DB_CONNECTED = Gauge("db_connected", "Database connectivity (1=true, 0=false)")
REDIS_CONNECTED = Gauge("redis_connected", "Redis connectivity (1=true, 0=false)")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


_health_updater_started = False
_health_updater_lock = threading.Lock()


def _configure_logging(level: str) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers in test/dev re-creations.
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.addHandler(handler)


def _create_db_engine(config: BaseConfig) -> Engine:
    database_url = config.DATABASE_URL
    if database_url.startswith("sqlite"):
        # Keep an in-memory SQLite database alive across threads.
        connect_args: dict[str, Any] = {"check_same_thread": False}
        if "uri=true" in database_url:
            connect_args["uri"] = True
        return create_engine(
            database_url,
            connect_args=connect_args,
            poolclass=StaticPool,
        )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=config.DB_POOL_SIZE,
        max_overflow=config.DB_MAX_OVERFLOW,
        pool_recycle=3600,
    )


def _check_database(engine: Engine) -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False
    except Exception:
        return False


def _check_redis(redis_client: Redis | None, redis_enabled: bool) -> bool:
    if not redis_enabled:
        return True
    if redis_client is None:
        return False
    try:
        return bool(redis_client.ping())
    except Exception:
        return False


def _start_health_and_resource_updater(
    *,
    config: BaseConfig,
    engine: Engine,
    redis_client: Redis | None,
) -> None:
    global _health_updater_started

    with _health_updater_lock:
        if _health_updater_started:
            return
        _health_updater_started = True

    def loop() -> None:
        process = psutil.Process(os.getpid())
        process.cpu_percent(interval=None)

        interval = max(int(config.METRICS_HEALTHCHECK_INTERVAL_SECONDS), 1)
        while True:
            try:
                cpu_percent = float(process.cpu_percent(interval=None))
                mem_mb = float(process.memory_info().rss) / (1024 * 1024)
                APP_CPU_PERCENT.set(cpu_percent)
                APP_MEMORY_MB.set(mem_mb)

                DB_CONNECTED.set(1 if _check_database(engine) else 0)
                REDIS_CONNECTED.set(1 if _check_redis(redis_client, config.REDIS_ENABLED) else 0)
            except Exception:
                # Best-effort metrics: never crash the app.
                pass

            time.sleep(interval)

    thread = threading.Thread(target=loop, name="health-and-metrics-updater", daemon=True)
    thread.start()


def _safe_request_id() -> str:
    return (
        request.headers.get("X-Request-ID")
        or getattr(g, "request_id", None)
        or uuid.uuid4().hex
    )


def _parse_json_body() -> dict[str, Any]:
    # Flask returns False for request.is_json when body is empty.
    if not request.is_json:
        raise ValueError("Request must be JSON")
    payload = request.get_json(silent=False)
    if payload is None:
        raise ValueError("Invalid JSON payload")
    if not isinstance(payload, dict):
        raise ValueError("JSON body must be an object")
    return payload


def create_app(app_config: type[BaseConfig] | None = None) -> Flask:
    config_class = app_config or get_config_class()
    config = config_class()

    # Load local env vars for developers. No dependency in production images.
    if config.APP_ENV != "production":
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except Exception:
            pass

    _configure_logging(config.LOG_LEVEL)

    engine = _create_db_engine(config)
    session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

    redis_client: Redis | None = None
    if config.REDIS_ENABLED:
        redis_client = redis_lib.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            socket_connect_timeout=3,
            socket_timeout=3,
            decode_responses=True,
        )

    _start_health_and_resource_updater(
        config=config, engine=engine, redis_client=redis_client
    )

    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH_BYTES
    app.config["JSON_SORT_KEYS"] = False

    # Auto-migrate only in non-production environments.
    if config.AUTO_MIGRATE:
        Base.metadata.create_all(bind=engine)

    # Security hardening (TLS headers etc. depend on Nginx / app environment).
    Talisman(
        app,
        content_security_policy=None,
        force_https=config.FORCE_HTTPS,
        strict_transport_security=config.FORCE_HTTPS,
    )

    limiter: Limiter | None = None
    if config.RATE_LIMIT_ENABLED:
        storage_uri = config.RATE_LIMIT_STORAGE_URI
        if not storage_uri and config.REDIS_ENABLED and redis_client is not None:
            storage_uri = f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}"
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=[config.RATE_LIMIT_DEFAULT],
            storage_uri=storage_uri,
        )

    @app.before_request
    def _before_request() -> None:
        g.request_id = _safe_request_id()
        g.start_time = time.perf_counter()

    @app.after_request
    def _after_request(response: Response) -> Response:
        request_id = getattr(g, "request_id", None)
        if request_id:
            response.headers["X-Request-ID"] = request_id

        method = request.method
        endpoint = request.endpoint or request.path
        status_code = str(response.status_code)
        elapsed = float(time.perf_counter() - g.start_time)

        REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=status_code).inc()
        REQUEST_DURATION_SECONDS.labels(
            method=method, endpoint=endpoint, status=status_code
        ).observe(elapsed)

        return response

    @app.get("/metrics")
    def metrics() -> Any:
        data = generate_latest()
        return Response(
            response=data,
            status=200,
            mimetype="text/plain; version=0.0.4; charset=utf-8",
        )

    @app.get("/health")
    def health() -> Any:
        db_ok = _check_database(engine)
        redis_ok = _check_redis(redis_client, config.REDIS_ENABLED)

        DB_CONNECTED.set(1 if db_ok else 0)
        REDIS_CONNECTED.set(1 if redis_ok else 0)

        overall_ok = db_ok and redis_ok
        status_code = 200 if overall_ok else 503

        payload: dict[str, Any] = {
            "status": "ok" if overall_ok else "degraded",
            "database": {"connected": db_ok},
            "redis": {"enabled": config.REDIS_ENABLED, "connected": redis_ok},
        }
        return jsonify(payload), status_code

    @app.post("/api/v1/items")
    def create_item() -> Any:
        if request.content_length and request.content_length > config.MAX_CONTENT_LENGTH_BYTES:
            return jsonify({"error": "payload_too_large"}), 413

        try:
            body = _parse_json_body()
            message = body.get("message")
            if not isinstance(message, str):
                return jsonify({"error": "invalid_message_type"}), 400
            message = message.strip()
            if not message:
                return jsonify({"error": "message_required"}), 400
            if len(message) > 200:
                return jsonify({"error": "message_too_long"}), 400
        except ValueError as exc:
            return jsonify({"error": "invalid_request", "message": str(exc)}), 400

        try:
            with Session(engine) as session:
                rec = ExampleRecord(message=message)
                session.add(rec)
                session.commit()
                session.refresh(rec)
                return jsonify({"id": rec.id, "created_at": rec.created_at.isoformat()}), 201
        except SQLAlchemyError:
            app.logger.exception("Database error while creating item", extra={"request_id": _safe_request_id()})
            return jsonify({"error": "database_error"}), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException) -> Any:
        request_id = _safe_request_id()
        method = request.method
        endpoint = request.endpoint or request.path

        error_type = f"http_{exc.code}"
        ERRORS_TOTAL.labels(method=method, endpoint=endpoint, error_type=error_type).inc()

        # Avoid leaking internal details; HTTPException.description can reveal internals.
        payload = {"error": exc.name, "request_id": request_id}
        return jsonify(payload), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(exc: Exception) -> Any:
        request_id = _safe_request_id()
        method = request.method
        endpoint = request.endpoint or request.path

        ERRORS_TOTAL.labels(method=method, endpoint=endpoint, error_type="unhandled_exception").inc()

        # Log with exception traceback.
        app.logger.error(
            "Unhandled exception",
            exc_info=exc,
            extra={"request_id": request_id},
        )
        return jsonify({"error": "internal_error", "request_id": request_id}), 500

    @app.after_request
    def _security_headers(response: Response) -> Response:
        # Ensure required headers exist even if upstream middleware changes.
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        return response

    return app


# Gunicorn entrypoint.
app = create_app()

