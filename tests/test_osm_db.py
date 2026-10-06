import json

from app import db
from app.models import Community, Submission
from app.osm_import import IMPORT_CONTACT, run_import

P1, P2, P3, P4 = [121.040, 14.670], [121.045, 14.670], [121.045, 14.675], [121.040, 14.675]


def way(osm_id, name, **tags):
    pts = [P1, P2, P3, P4, P1]
    return {"type": "way", "id": osm_id, "tags": {"name": name, **tags},
            "geometry": [{"lat": lat, "lon": lng} for lng, lat in pts]}


ELEMENTS = [way(1, "Alpha Village", access="private"), way(2, "Beta Homes", access="private")]


def test_import_creates_pending_submissions_only(app):
    stats = run_import(ELEMENTS)
    assert stats["created"] == 2
    subs = Submission.query.all()
    assert {s.status for s in subs} == {"pending"}
    assert {s.contact for s in subs} == {IMPORT_CONTACT}
    assert Community.query.count() == 0  # nothing public until an admin approves


def test_dry_run_saves_nothing(app):
    stats = run_import(ELEMENTS, dry_run=True)
    assert stats["created"] == 2
    assert Submission.query.count() == 0


def test_running_twice_does_not_duplicate(app):
    run_import(ELEMENTS)
    stats = run_import(ELEMENTS)
    assert stats["created"] == 0 and stats["duplicates"] == 2
    assert Submission.query.count() == 2


def test_rejected_imports_are_not_reimported(app):
    run_import(ELEMENTS)
    for s in Submission.query.all():
        s.status = "rejected"
    db.session.commit()
    assert run_import(ELEMENTS)["created"] == 0


def test_live_community_with_same_osm_source_blocks_reimport(app):
    db.session.add(Community(name="Alpha Village", city="Makati", status="approved",
                             geometry=json.dumps({"type": "Point", "coordinates": [121.0, 14.6]}),
                             source="https://www.openstreetmap.org/way/1"))
    db.session.commit()
    stats = run_import(ELEMENTS)
    assert stats["created"] == 1 and stats["duplicates"] == 1


def test_limit(app):
    assert run_import(ELEMENTS, limit=1)["created"] == 1
    assert Submission.query.count() == 1
