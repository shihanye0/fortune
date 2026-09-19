"""Regression coverage for a fresh database initialized through Alembic only."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.config import settings


EXPECTED_TABLES = {
    "users",
    "bazi_profiles",
    "daily_fortunes",
    "divination_records",
    "prediction_outcomes",
    "probability_event_feedbacks",
    "push_deliveries",
}


def test_alembic_initializes_a_fresh_database_and_is_idempotent(tmp_path, monkeypatch):
    database_path = tmp_path / "fresh.db"
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{database_path.as_posix()}")
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))

    command.upgrade(config, "head")
    command.downgrade(config, "6f442fb65ec6")
    command.upgrade(config, "head")

    engine = create_engine(settings.DATABASE_URL)
    try:
        assert EXPECTED_TABLES <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()
