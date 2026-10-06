"""Small, safe schema upgrades for databases created by earlier versions."""
from sqlalchemy import inspect, text

from app import db


def upgrade_schema():
    """Add columns introduced after the first release. Safe to run repeatedly.

    Returns a list describing what was changed (empty if nothing was needed).
    """
    changes = []
    inspector = inspect(db.engine)
    if "community" in inspector.get_table_names():
        columns = {c["name"] for c in inspector.get_columns("community")}
        if "province" not in columns:
            db.session.execute(text(
                "ALTER TABLE community ADD COLUMN province VARCHAR(60) NOT NULL DEFAULT 'Metro Manila'"
            ))
            changes.append("community.province")
        db.session.execute(text("CREATE INDEX IF NOT EXISTS ix_community_province ON community (province)"))
        db.session.commit()
    return changes


def ensure_schema():
    """Create any missing tables, then apply upgrades. Returns the list of changes."""
    db.create_all()
    return upgrade_schema()
