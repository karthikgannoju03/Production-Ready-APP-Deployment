import os

from . import BaseConfig


class DevelopmentConfig(BaseConfig):
    APP_ENV = "development"
    DEBUG = True
    FORCE_HTTPS = False

    # In dev, allow a default secret to avoid boot failures.
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # Allow bigger payloads in development.
    MAX_CONTENT_LENGTH_BYTES = int(os.getenv("MAX_CONTENT_LENGTH_BYTES", 512 * 1024))

    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()

    # Rate limiting (kept enabled so nginx/flask behavior is exercised).
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "200 per hour")
    RATE_LIMIT_STORAGE_URI = os.getenv("RATE_LIMIT_STORAGE_URI")

    # Database (Postgres by default for parity with production).
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://{user}:{password}@{host}:{port}/{db}".format(
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            host=os.getenv("POSTGRES_HOST", "postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            db=os.getenv("POSTGRES_DB", "postgres"),
        ),
    )

    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))

    # Redis
    REDIS_ENABLED = os.getenv("REDIS_ENABLED", "true").lower() == "true"
    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))

    # Make local development smooth.
    AUTO_MIGRATE = os.getenv("AUTO_MIGRATE", "true").lower() == "true"

    METRICS_HEALTHCHECK_INTERVAL_SECONDS = int(
        os.getenv("METRICS_HEALTHCHECK_INTERVAL_SECONDS", "10")
    )

    GUNICORN_WORKERS = int(os.getenv("GUNICORN_WORKERS", "2"))
    GUNICORN_THREADS = int(os.getenv("GUNICORN_THREADS", "4"))

