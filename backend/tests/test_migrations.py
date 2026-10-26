"""Tests for Alembic database migration execution."""

from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command


def test_alembic_upgrade_creates_all_twelve_tables(temp_db_file: str) -> None:
    """Verify that Alembic initial schema migration cleanly constructs all 12 tables."""
    backend_dir = Path(__file__).resolve().parent.parent
    ini_path = backend_dir / "alembic.ini"
    assert ini_path.exists(), "alembic.ini must exist"

    alembic_cfg = Config(str(ini_path))
    db_url = f"sqlite:///{temp_db_file}"
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # Run upgrade head
    command.upgrade(alembic_cfg, "head")

    # Inspect created schema
    engine = create_engine(db_url)
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    expected_tables = {
        "alembic_version",
        "missions",
        "satellites",
        "satellite_subsystems",
        "telemetry_samples",
        "fault_scenarios",
        "incident_records",
        "incident_evidence",
        "ground_stations",
        "contact_windows",
        "satellite_commands",
        "mission_events",
        "simulation_checkpoints",
    }

    missing_tables = expected_tables - table_names
    assert not missing_tables, f"Missing migrated tables: {missing_tables}"
    engine.dispose()
