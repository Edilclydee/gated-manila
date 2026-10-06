import json

import pytest

from app import db
from app.models import Admin, Community, Submission

SQUARE = {
    "type": "Polygon",
    "coordinates": [[[121.04, 14.67], [121.05, 14.67], [121.05, 14.68], [121.04, 14.68], [121.04, 14.67]]],
}
PASSWORD = "correct-horse-battery"


def sub_data(**overrides):
    data = {
        "name": "New Village", "alt_names": None, "community_type": "subdivision",
        "province": "Metro Manila", "city": "Marikina", "barangay": None, "gating_status": "fully_gated",
        "entry_points": 2, "notes": None, "source": "I live here", "geometry": SQUARE,
    }
    data.update(overrides)
    return data


def form_from(data, **overrides):
    form = {k: ("" if v is None else v) for k, v in data.items()}
    form["geometry"] = json.dumps(data["geometry"])
    form.update(overrides)
    return form


def make_submission(community_id=None, **overrides):
    sub = Submission(community_id=community_id, contact="me@example.com")
    sub.data = sub_data(**overrides)
    db.session.add(sub)
    db.session.commit()
    return sub


def make_community(name="Existing", status="approved"):
    c = Community(name=name, city="Makati", status=status, geometry=json.dumps(SQUARE),
                  community_type="subdivision", gating_status="open_or_unclear", source="old")
    db.session.add(c)
    db.session.commit()
    return c


@pytest.fixture
def admin(app):
    a = Admin(username="boss")
    a.set_password(PASSWORD)
    db.session.add(a)
    db.session.commit()
    return a


@pytest.fixture
def client(app, admin):
    c = app.test_client()
    resp = c.post("/admin/login", data={"username": "boss", "password": PASSWORD})
    assert resp.status_code == 302
    return c


def public_names(app):
    data = app.test_client().get("/api/communities").get_json()
    return [f["properties"]["name"] for f in data["features"]]


# ---------- access control ----------

def test_admin_pages_require_login(app):
    c = app.test_client()
    for url in ("/admin/", "/admin/communities", "/admin/submission/1"):
        resp = c.get(url)
        assert resp.status_code == 302 and "/admin/login" in resp.headers["Location"]


def test_admin_actions_require_login(app):
    sub = make_submission()
    resp = app.test_client().post(f"/admin/submission/{sub.id}/approve", data=form_from(sub_data()))
    assert resp.status_code == 302 and "/admin/login" in resp.headers["Location"]
    assert Community.query.count() == 0


def test_wrong_password_rejected(app, admin):
    c = app.test_client()
    assert c.post("/admin/login", data={"username": "boss", "password": "nope"}).status_code == 401
    assert c.post("/admin/login", data={"username": "ghost", "password": "nope"}).status_code == 401
    assert c.get("/admin/").status_code == 302


def test_login_works_and_logout_locks_again(client):
    assert client.get("/admin/").status_code == 200
    client.post("/admin/logout")
    assert client.get("/admin/").status_code == 302


def test_login_ignores_external_next_url(app, admin):
    c = app.test_client()
    resp = c.post("/admin/login?next=//evil.example", data={"username": "boss", "password": PASSWORD})
    assert resp.status_code == 302
    assert "evil.example" not in resp.headers["Location"]


# ---------- review actions ----------

def test_queue_lists_pending_submissions(app, client):
    make_submission(name="Queue Test Village")
    assert "Queue Test Village" in client.get("/admin/").get_data(as_text=True)


def test_review_page_loads(app, client):
    sub = make_submission()
    assert client.get(f"/admin/submission/{sub.id}").status_code == 200


def test_approve_new_submission_publishes_it(app, client, admin):
    sub = make_submission()
    resp = client.post(f"/admin/submission/{sub.id}/approve", data=form_from(sub_data()))
    assert resp.status_code == 302
    assert public_names(app) == ["New Village"]
    sub = db.session.get(Submission, sub.id)
    assert sub.status == "approved"
    assert sub.reviewed_by_id == admin.id
    assert Community.query.one().last_verified is not None


def test_admin_can_edit_before_approving(app, client):
    sub = make_submission(name="Typo Vilage")
    client.post(f"/admin/submission/{sub.id}/approve", data=form_from(sub_data(name="Fixed Village")))
    assert public_names(app) == ["Fixed Village"]


def test_approve_edit_updates_existing_community(app, client):
    c = make_community()
    sub = make_submission(community_id=c.id, name="Existing (renamed)", city="Makati")
    client.post(f"/admin/submission/{sub.id}/approve", data=form_from(sub_data(name="Existing (renamed)", city="Makati")))
    assert Community.query.count() == 1
    assert db.session.get(Community, c.id).name == "Existing (renamed)"


def test_invalid_approval_creates_nothing(app, client):
    sub = make_submission()
    resp = client.post(f"/admin/submission/{sub.id}/approve", data=form_from(sub_data(), source=""))
    assert resp.status_code == 400
    assert Community.query.count() == 0
    assert db.session.get(Submission, sub.id).status == "pending"


def test_reject_requires_a_reason(app, client):
    sub = make_submission()
    resp = client.post(f"/admin/submission/{sub.id}/reject", data={"reviewer_notes": ""})
    assert resp.status_code == 400
    assert db.session.get(Submission, sub.id).status == "pending"


def test_reject_with_reason(app, client):
    sub = make_submission()
    resp = client.post(f"/admin/submission/{sub.id}/reject", data={"reviewer_notes": "Duplicate entry"})
    assert resp.status_code == 302
    sub = db.session.get(Submission, sub.id)
    assert sub.status == "rejected"
    assert sub.reviewer_notes == "Duplicate entry"
    assert Community.query.count() == 0


def test_reviewed_submission_cannot_be_approved_twice(app, client):
    sub = make_submission()
    client.post(f"/admin/submission/{sub.id}/approve", data=form_from(sub_data()))
    client.post(f"/admin/submission/{sub.id}/approve", data=form_from(sub_data()))
    assert Community.query.count() == 1
    assert client.get(f"/admin/submission/{sub.id}").status_code == 200  # read-only view


def test_edit_of_unpublished_community_cannot_be_approved(app, client):
    c = make_community()
    sub = make_submission(community_id=c.id)
    c.status = "unpublished"
    db.session.commit()
    client.post(f"/admin/submission/{sub.id}/approve", data=form_from(sub_data()))
    assert db.session.get(Submission, sub.id).status == "pending"


# ---------- takedown ----------

def test_unpublish_and_republish(app, client):
    c = make_community()
    assert public_names(app) == ["Existing"]
    client.post(f"/admin/communities/{c.id}/unpublish")
    assert public_names(app) == []
    client.post(f"/admin/communities/{c.id}/republish")
    assert public_names(app) == ["Existing"]


def test_approve_publishes_province_in_public_data(app, client):
    sub = make_submission(province="Rizal", city="Antipolo")
    client.post(f"/admin/submission/{sub.id}/approve", data=form_from(sub_data(province="Rizal", city="Antipolo")))
    feature = app.test_client().get("/api/communities").get_json()["features"][0]
    assert feature["properties"]["province"] == "Rizal"
    assert feature["properties"]["city"] == "Antipolo"


def test_old_submission_without_province_still_reviewable(app, client):
    sub = Submission()
    old = sub_data()
    del old["province"]
    sub.data = old  # as created before provinces existed
    db.session.add(sub)
    db.session.commit()
    resp = client.get(f"/admin/submission/{sub.id}")
    assert resp.status_code == 200
    assert 'value="Metro Manila" selected' in resp.get_data(as_text=True)
