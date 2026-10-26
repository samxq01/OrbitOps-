"""Pytest shared fixtures for OrbitOps persistence and API tests."""

import os
import tempfile
from collections.abc import Generator

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.session import create_database_engine


@pytest.fixture(scope="session")
def temp_db_file() -> Generator[str, None, None]:
    """Provide a path to a disposable temporary SQLite database file."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as f:
        temp_path = f.name
    try:
        yield temp_path
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@pytest.fixture
def test_engine() -> Generator[Engine, None, None]:
    """Provide an in-memory SQLite database engine with foreign-key enforcement."""
    engine = create_database_engine("sqlite:///:memory:", echo=False, is_test=True)
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Generator[Session, None, None]:
    """Provide an isolated, rollbacked SQLAlchemy session for unit and domain tests."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    session = session_factory()

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()
