"""Fake records for local testing. Names start with SAMPLE so they are easy to spot and remove."""
import json
from datetime import datetime, timezone

from app import db
from app.models import Community

SAMPLE_PREFIX = "SAMPLE"


def _square(lng, lat, d=0.002):
    ring = [[lng - d, lat - d], [lng + d, lat - d], [lng + d, lat + d], [lng - d, lat + d], [lng - d, lat - d]]
    return {"type": "Polygon", "coordinates": [ring]}


def _point(lng, lat):
    return {"type": "Point", "coordinates": [lng, lat]}


SAMPLES = [
    ("SAMPLE Test Village 1", "Metro Manila", "Quezon City", "fully_gated", _square(121.044, 14.676), 2),
    ("SAMPLE Test Village 2", "Metro Manila", "Marikina", "partially_gated", _square(121.100, 14.650), 3),
    ("SAMPLE Test Heights", "Metro Manila", "Makati", "open_or_unclear", _square(121.024, 14.554), None),
    ("SAMPLE Test Homes", "Metro Manila", "Taguig", "fully_gated", _square(121.050, 14.520), 1),
    ("SAMPLE Pin-only Village", "Metro Manila", "Pasig", "partially_gated", _point(121.080, 14.575), None),
    ("SAMPLE Test Heights (Rizal)", "Rizal", "Antipolo", "partially_gated", _square(121.176, 14.586), 2),
    ("SAMPLE Test Village (Cavite)", "Cavite", "Bacoor", "fully_gated", _square(120.964, 14.459), 1),
]


def seed_samples():
    """Insert sample approved communities. Returns how many were added."""
    added = 0
    for name, province, city, gating, geom, entries in SAMPLES:
        if Community.query.filter_by(name=name).first():
            continue
        db.session.add(Community(
            name=name,
            province=province,
            city=city,
            community_type="subdivision",
            gating_status=gating,
            entry_points=entries,
            notes="Sample record for testing. Not a real community.",
            source="Generated sample data",
            geometry=json.dumps(geom),
            status="approved",
            last_verified=datetime.now(timezone.utc),
        ))
        added += 1
    db.session.commit()
    return added


def clear_samples():
    """Delete all sample communities. Returns how many were removed."""
    rows = Community.query.filter(Community.name.like(f"{SAMPLE_PREFIX}%")).all()
    for row in rows:
        db.session.delete(row)
    db.session.commit()
    return len(rows)
