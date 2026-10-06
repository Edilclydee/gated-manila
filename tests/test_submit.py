import json

import pytest

from app import db
from app.models import Community, Submission

SQUARE = {
    "type": "Polygon",
    "coordinates": [[[121.04, 14.67], [121.05, 14.67], [121.05, 14.68], [121.04, 14.68], [121.04, 14.67]]],
}


def good_form(**overrides):
    form = {
        "name": "Test Village", "city": "Marikina", "community_type": "subdivision",
        "gating_status": "fully_gated", "source": "I live here",
        "geometry": json.dumps(SQUARE), "contact": "me@example.com",
    }
    form.update(overrides)
    return form


@pytest.fixture
def turnstile_ok(monkeypatch):
    monkeypatch.setattr("app.routes_submit.verify_turnstile", lambda token, ip=None: True)


def make_community(status="approved"):
    c = Community(name="Existing", city="Makati", status=status, geometry=json.dumps(SQUARE))
    db.session.add(c)
    db.session.commit()
    return c


def test_form_page_loads(app):
    assert app.test_client().get("/submit").status_code == 200


def test_valid_submission_is_saved_as_pending(app, turnstile_ok):
    resp = app.test_client().post("/submit", data=good_form())
    assert resp.status_code == 302
    sub = Submission.query.one()
    assert sub.status == "pending"
    assert sub.community_id is None
    assert sub.contact == "me@example.com"
    assert sub.data["name"] == "Test Village"
    assert "contact" not in sub.data


def test_submission_never_goes_public_automatically(app, turnstile_ok):
    app.test_client().post("/submit", data=good_form())
    assert Community.query.count() == 0
    assert app.test_client().get("/api/communities").get_json()["features"] == []


def test_failed_turnstile_blocks_submission(app, monkeypatch):
    monkeypatch.setattr("app.routes_submit.verify_turnstile", lambda token, ip=None: False)
    resp = app.test_client().post("/submit", data=good_form())
    assert resp.status_code == 400
    assert Submission.query.count() == 0


def test_invalid_geometry_blocks_submission(app, turnstile_ok):
    resp = app.test_client().post("/submit", data=good_form(geometry=""))
    assert resp.status_code == 400
    assert Submission.query.count() == 0


def test_honeypot_silently_discards_bots(app, turnstile_ok):
    resp = app.test_client().post("/submit", data=good_form(website="http://spam.example"))
    assert resp.status_code == 302
    assert Submission.query.count() == 0


def test_edit_submission_links_to_existing_community(app, turnstile_ok):
    c = make_community()
    resp = app.test_client().post(f"/submit?edit={c.id}", data=good_form(name="Existing (renamed)"))
    assert resp.status_code == 302
    sub = Submission.query.one()
    assert sub.community_id == c.id
    assert Community.query.one().name == "Existing"  # live data untouched


def test_cannot_edit_unapproved_or_missing_community(app):
    pending = make_community(status="pending")
    client = app.test_client()
    assert client.get(f"/submit?edit={pending.id}").status_code == 404
    assert client.get("/submit?edit=9999").status_code == 404
