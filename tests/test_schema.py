import sqlite3

import pytest
from sqlalchemy import text

from app import db
from app.schema import ensure_schema, upgrade_schema


def test_upgrade_adds_province_to_an_old_database(app):
    if sqlite3.sqlite_version_info < (3, 35, 0):
        pytest.skip("needs SQLite 3.35+ to simulate the old table")
    # Recreate the table as it looked before provinces existed.
    db.session.execute(text("DROP INDEX IF EXISTS ix_community_province"))
    db.session.execute(text("ALTER TABLE community DROP COLUMN province"))
    db.session.execute(text(
        "INSERT INTO community (name, community_type, city, gating_status, geometry, status) "
        "VALUES ('Old Village', 'subdivision', 'Makati', 'fully_gated', '{}', 'approved')"
    ))
    db.session.commit()

    assert upgrade_schema() == ["community.province"]
    row = db.session.execute(text("SELECT province FROM community WHERE name = 'Old Village'")).one()
    assert row[0] == "Metro Manila"  # existing entries are Metro Manila
    assert upgrade_schema() == []  # safe to run again


def test_ensure_schema_is_a_noop_on_a_current_database(app):
    assert ensure_schema() == []
