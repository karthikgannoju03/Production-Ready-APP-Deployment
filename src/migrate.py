from __future__ import annotations

import os
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from config import BaseConfig, get_config_class
from src.app import Base


def _create_db_engine(config: BaseConfig) -> Engine:
    database_url = config.DATABASE_URL
    if database_url.startswith("sqlite"):
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


def main() -> None:
    config_class = get_config_class()
    config = config_class()
    engine = _create_db_engine(config)
    # For this sample project, migrations are "schema bootstrap" via SQLAlchemy metadata.
    # In a real enterprise setup, replace this with Alembic versioned migrations.
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    main()

