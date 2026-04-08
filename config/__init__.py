import importlib
import os
from typing import Any, Type, cast


class BaseConfig:
    """
    Central place for shared config keys.

    Concrete values are set in environment-specific classes.
    """

    APP_ENV: str = "development"

    # Security
    SECRET_KEY: str
    FORCE_HTTPS: bool = False

    # Flask
    DEBUG: bool = False
    TESTING: bool = False
    MAX_CONTENT_LENGTH_BYTES: int = 256 * 1024

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "200 per day"
    RATE_LIMIT_STORAGE_URI: str | None = None

    # Observability
    LOG_LEVEL: str = "INFO"
    METRICS_HEALTHCHECK_INTERVAL_SECONDS: int = 15

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_ENABLED: bool = True
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int = 0

    # Migrations / startup behavior
    AUTO_MIGRATE: bool = False

    # Gunicorn
    GUNICORN_WORKERS: int = 2
    GUNICORN_THREADS: int = 4


def get_config_class(app_env: str | None = None) -> Type[BaseConfig]:
    env_value = app_env or os.getenv("APP_ENV", "development") or "development"
    env = env_value.strip().lower()

    if env in {"prod", "production"}:
        module_name = "config.production"
        class_name = "ProductionConfig"
    elif env in {"test", "testing"}:
        module_name = "config.testing"
        class_name = "TestingConfig"
    else:
        module_name = "config.development"
        class_name = "DevelopmentConfig"

    cfg_module = importlib.import_module(module_name)
    cfg_class: Any = getattr(cfg_module, class_name)
    return cast(Type[BaseConfig], cfg_class)

