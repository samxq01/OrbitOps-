"""OrbitOps database engine and session management."""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger("orbitops.db")


def _configure_sqlite_connection(dbapi_connection: Any, connection_record: Any) -> None:
    """Enforce SQLite foreign key constraints, busy timeout, and optional WAL mode."""
    cursor = dbapi_connection.cursor()
    # Enforce foreign key constraints strictly
    cursor.execute("PRAGMA foreign_keys=ON;")
    # Set busy timeout to 5000ms to avoid locking contention
    cursor.execute("PRAGMA busy_timeout=5000;")
    cursor.close()


def create_database_engine(
    database_url: str | None = None,
    echo: bool = False,
    is_test: bool = False,
) -> Engine:
    """Create and configure a SQLAlchemy engine with SQLite pragmas."""
    url = database_url or settings.database_url
    connect_args: dict[str, Any] = {}

    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(
        url,
        echo=echo,
        connect_args=connect_args,
    )

    if url.startswith("sqlite"):
        event.listen(engine, "connect", _configure_sqlite_connection)

        # Enable WAL mode for file-backed SQLite databases (not in-memory)
        if not is_test and ":memory:" not in url:
            try:
                with engine.connect() as conn:
                    conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
                    logger.info("SQLite WAL mode activated for %s", url)
            except Exception as e:
                logger.warning("Could not enable WAL mode for %s: %s", url, e)

    return engine


# Default application-wide engine and session maker
engine: Engine = create_database_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a managed database session."""
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_db_context(
    custom_session_factory: sessionmaker[Session] | None = None,
) -> Generator[Session, None, None]:
    """Context manager for programmatic database operations with automatic rollback."""
    factory = custom_session_factory or SessionLocal
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
