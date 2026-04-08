import os

from . import BaseConfig


def _required_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


class ProductionConfig(BaseConfig):
    APP_ENV = "production"
    DEBUG = False
    FORCE_HTTPS = os.getenv("FORCE_HTTPS", "true").lower() == "true"

    SECRET_KEY = _required_env("SECRET_KEY")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    MAX_CONTENT_LENGTH_BYTES = int(os.getenv("MAX_CONTENT_LENGTH_BYTES", 256 * 1024))

    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "200 per hour")
    RATE_LIMIT_STORAGE_URI = os.getenv("RATE_LIMIT_STORAGE_URI")

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

    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))

    REDIS_ENABLED = os.getenv("REDIS_ENABLED", "true").lower() == "true"
    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))

    AUTO_MIGRATE = os.getenv("AUTO_MIGRATE", "false").lower() == "true"

    METRICS_HEALTHCHECK_INTERVAL_SECONDS = int(
        os.getenv("METRICS_HEALTHCHECK_INTERVAL_SECONDS", "15")
    )

    GUNICORN_WORKERS = int(os.getenv("GUNICORN_WORKERS", "2"))
    GUNICORN_THREADS = int(os.getenv("GUNICORN_THREADS", "4"))

