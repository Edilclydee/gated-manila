import json

from app import db
from app.models import Community
from app.sample_data import SAMPLES, clear_samples, seed_samples

POINT = json.dumps({"type": "Point", "coordinates": [121.0, 14.6]})


def test_home_page_loads(app):
    assert app.test_client().get("/").status_code == 200


def test_api_returns_only_approved(app):
    db.session.add_all([
        Community(name="Visible", city="Makati", geometry=POINT, status="approved"),
        Community(name="Hidden", city="Makati", geometry=POINT, status="pending"),
    ])
    db.session.commit()
    data = app.test_client().get("/api/communities").get_json()
    assert data["type"] == "FeatureCollection"
    assert [f["properties"]["name"] for f in data["features"]] == ["Visible"]


def test_seed_and_clear_samples(app):
    assert seed_samples() == len(SAMPLES)
    assert seed_samples() == 0  # running twice adds nothing
    assert Community.approved().count() == len(SAMPLES)
    assert clear_samples() == len(SAMPLES)
    assert Community.query.count() == 0
