import json

import pytest

from app import db
from app.models import Admin, Community, Submission

POINT = json.dumps({"type": "Point", "coordinates": [121.0, 14.6]})


def make_community(name, status):
    return Community(name=name, city="Quezon City", geometry=POINT, status=status)


def test_only_approved_communities_are_public(app):
    db.session.add_all([
        make_community("A", "approved"),
        make_community("B", "pending"),
        make_community("C", "rejected"),
    ])
    db.session.commit()
    assert [c.name for c in Community.approved().all()] == ["A"]


def test_feature_is_valid_geojson(app):
    c = make_community("A", "approved")
    db.session.add(c)
    db.session.commit()
    feature = c.to_feature()
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Point"
    assert feature["properties"]["name"] == "A"


def test_submission_defaults_to_pending_and_roundtrips_data(app):
    s = Submission()
    s.data = {"name": "New Village", "city": "Marikina"}
    db.session.add(s)
    db.session.commit()
    assert s.status == "pending"
    assert s.community_id is None
    assert s.data["name"] == "New Village"


def test_admin_password_is_hashed_and_checked(app):
    a = Admin(username="boss")
    a.set_password("correct-horse")
    assert a.password_hash != "correct-horse"
    assert a.check_password("correct-horse")
    assert not a.check_password("wrong")


def test_short_admin_password_rejected(app):
    with pytest.raises(ValueError):
        Admin(username="x").set_password("short")
