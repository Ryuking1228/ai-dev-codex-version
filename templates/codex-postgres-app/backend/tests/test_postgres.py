"""Explicit integration target: missing TEST_DATABASE_URL is a failure, never a skip."""
import os
from uuid import uuid4
from app.main import PostgresItems
from app.migrate import migrate


def test_persistence_and_migrations(monkeypatch):
    database_url = os.environ.get("TEST_DATABASE_URL")
    assert database_url, "Set TEST_DATABASE_URL to a dedicated PostgreSQL test database"
    monkeypatch.setenv("DATABASE_URL", database_url)
    migrate()
    migrate()  # Repeat application must be safe.
    created = PostgresItems().create("integration-" + str(uuid4()))
    try:
        assert created in PostgresItems().list()  # New connection proves persistence.
    finally:
        assert PostgresItems().delete(created["id"])
