import os

from . import BaseConfig


class TestingConfig(BaseConfig):
    APP_ENV = "testing"
    DEBUG = False
    TESTING = True
    FORCE_HTTPS = False

    SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-change-me")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()

    # Disable rate limiting for tests to keep assertions deterministic.
    RATE_LIMIT_ENABLED = False

    # Use a shared in-memory SQLite database across connections.
    # This avoids nondeterministic schema visibility issues in tests.
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite+pysqlite:///file::memory:?cache=shared&uri=true",
    )
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "1"))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "0"))

    # Disable Redis for tests; health endpoint should still succeed.
    REDIS_ENABLED = False
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))

    AUTO_MIGRATE = os.getenv("AUTO_MIGRATE", "true").lower() == "true"

    METRICS_HEALTHCHECK_INTERVAL_SECONDS = int(
        os.getenv("METRICS_HEALTHCHECK_INTERVAL_SECONDS", "2")
    )

    GUNICORN_WORKERS = int(os.getenv("GUNICORN_WORKERS", "1"))
    GUNICORN_THREADS = int(os.getenv("GUNICORN_THREADS", "1"))

