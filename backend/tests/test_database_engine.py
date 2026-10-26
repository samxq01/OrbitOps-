"""Tests for SQLAlchemy database engine and SQLite pragmas."""

import tempfile

from sqlalchemy import text

from app.db.session import create_database_engine


def test_sqlite_foreign_keys_enforced() -> None:
    """Verify that foreign keys are enforced by SQLite connection listeners."""
    engine = create_database_engine("sqlite:///:memory:", is_test=True)
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA foreign_keys;")).scalar()
        assert result == 1, "SQLite foreign keys must be active (1)"


def test_sqlite_busy_timeout_configured() -> None:
    """Verify that SQLite busy timeout is configured to 5000ms."""
    engine = create_database_engine("sqlite:///:memory:", is_test=True)
    with engine.connect() as conn:
        timeout = conn.execute(text("PRAGMA busy_timeout;")).scalar()
        assert timeout == 5000, "SQLite busy timeout must be 5000ms"


def test_sqlite_wal_mode_on_file_database() -> None:
    """Verify that file-backed SQLite engines activate WAL mode."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite3") as f:
        db_path = f.name

    engine = create_database_engine(f"sqlite:///{db_path}", is_test=False)
    with engine.connect() as conn:
        mode = conn.execute(text("PRAGMA journal_mode;")).scalar()
        assert mode.upper() == "WAL", "File-backed database must use WAL journal mode"
    engine.dispose()
