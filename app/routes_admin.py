import json

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.constants import (
    COMMUNITY_TYPES, GATING_LABELS, STATUS_APPROVED, STATUS_PENDING, province_for_city,
    STATUS_REJECTED, STATUS_UNPUBLISHED,
)
from app.extensions import limiter, login_manager
from app.models import Admin, Community, Submission
from app.review import (
    ReviewError, approve_submission, reject_submission, republish_community, unpublish_community,
)
from app.validation import validate_submission

bp = Blueprint("admin", __name__, url_prefix="/admin")

# Used so a login attempt for an unknown user takes as long as one for a real user.
DUMMY_HASH = generate_password_hash("not-a-real-password")

TYPE_LABELS = {
    "subdivision": "Subdivision", "village": "Village",
    "condo_compound": "Condo compound", "other": "Other",
}
FIELD_LABELS = {
    "name": "Name", "alt_names": "Other names", "community_type": "Type", "province": "Province", "city": "City / municipality",
    "barangay": "Barangay", "gating_status": "Gating status", "entry_points": "Entry points",
    "notes": "Notes", "source": "Source",
}


@bp.before_request
def require_login():
    """Every admin page except the login form needs a signed-in admin."""
    if request.endpoint == "admin.login":
        return None
    if not current_user.is_authenticated:
        return login_manager.unauthorized()
    return None


def _safe_next(target):
    """Only allow redirects to paths on this site (blocks open-redirect tricks)."""
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return url_for("admin.queue")


# ---------- login / logout ----------

@bp.route("/login", methods=["GET", "POST"])
@limiter.limit(lambda: current_app.config["LOGIN_RATE_LIMIT"], methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.queue"))
    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        admin = Admin.query.filter_by(username=username).first()
        if admin:
            ok = admin.check_password(password)
        else:
            check_password_hash(DUMMY_HASH, password)
            ok = False
        if ok:
            login_user(admin)
            return redirect(_safe_next(request.args.get("next")))
        error = "Wrong username or password."
    return render_template("admin/login.html", error=error), (401 if error else 200)


@bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("Signed out.", "success")
    return redirect(url_for("admin.login"))


# ---------- review queue ----------

@bp.route("/")
def queue():
    status = request.args.get("status", STATUS_PENDING)
    if status not in (STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED):
        status = STATUS_PENDING
    order = Submission.created_at.asc() if status == STATUS_PENDING else Submission.created_at.desc()
    submissions = Submission.query.filter_by(status=status).order_by(order).all()
    counts = {
        s: Submission.query.filter_by(status=s).count()
        for s in (STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED)
    }
    return render_template("admin/queue.html", submissions=submissions, status=status, counts=counts)


def _with_province(data):
    """Older submissions have no province; infer it from the city when that is unambiguous."""
    data = dict(data)
    if not data.get("province") and data.get("city"):
        data["province"] = province_for_city(data["city"])
    return data


def _form_values(data):
    values = _with_province(data)
    values["geometry"] = json.dumps(data["geometry"]) if data.get("geometry") else ""
    return values


def _diffs(community, proposed):
    rows = []
    for key, label in FIELD_LABELS.items():
        old = getattr(community, key)
        new = proposed.get(key)
        old_text = "" if old is None else str(old)
        new_text = "" if new is None else str(new)
        rows.append((label, old_text, new_text, old_text != new_text))
    shape_changed = community.geometry_dict != proposed.get("geometry")
    return rows, shape_changed


def _render_review(submission, values, errors, status=200):
    community = submission.community
    diffs, shape_changed = _diffs(community, _with_province(submission.data)) if community else ([], False)
    lat, lng = current_app.config["MAP_CENTER"]
    page_config = {
        "lat": lat, "lng": lng, "zoom": current_app.config["MAP_ZOOM"],
        "excludeId": community.id if community else None,
        "existing": community.geometry_dict if community else None,
        "readOnly": submission.status != STATUS_PENDING,
    }
    return render_template(
        "admin/review.html",
        submission=submission, community=community, values=values, errors=errors,
        diffs=diffs, shape_changed=shape_changed,
        type_labels=TYPE_LABELS, gating_labels=GATING_LABELS,
        field_labels=FIELD_LABELS, page_config=page_config,
        initial_geometry=values.get("geometry") or "",
    ), status


@bp.route("/submission/<int:submission_id>")
def review(submission_id):
    submission = db.get_or_404(Submission, submission_id)
    return _render_review(submission, _form_values(submission.data), [])


@bp.route("/submission/<int:submission_id>/approve", methods=["POST"])
def approve(submission_id):
    submission = db.get_or_404(Submission, submission_id)
    data, errors = validate_submission(request.form)
    if errors:
        return _render_review(submission, request.form.to_dict(), errors, status=400)
    try:
        community = approve_submission(
            submission, data, current_user.id, request.form.get("reviewer_notes"),
        )
    except ReviewError as err:
        flash(str(err), "error")
        return redirect(url_for("admin.review", submission_id=submission.id))
    flash(f"Approved: “{community.name}” is now on the map.", "success")
    return redirect(url_for("admin.queue"))


@bp.route("/submission/<int:submission_id>/reject", methods=["POST"])
def reject(submission_id):
    submission = db.get_or_404(Submission, submission_id)
    try:
        reject_submission(submission, current_user.id, request.form.get("reviewer_notes"))
    except ReviewError as err:
        if submission.status == STATUS_PENDING:  # missing reason: keep the admin's edits
            return _render_review(submission, request.form.to_dict(), [str(err)], status=400)
        flash(str(err), "error")
        return redirect(url_for("admin.review", submission_id=submission.id))
    flash("Submission rejected.", "success")
    return redirect(url_for("admin.queue"))


# ---------- live communities (takedown) ----------

@bp.route("/communities")
def communities():
    rows = (
        Community.query
        .filter(Community.status.in_([STATUS_APPROVED, STATUS_UNPUBLISHED]))
        .order_by(Community.name)
        .all()
    )
    return render_template("admin/communities.html", communities=rows,
                           gating_labels=GATING_LABELS, STATUS_APPROVED=STATUS_APPROVED)


def _community_action(community_id, action, message):
    community = db.get_or_404(Community, community_id)
    try:
        action(community)
        flash(message.format(name=community.name), "success")
    except ReviewError as err:
        flash(str(err), "error")
    return redirect(url_for("admin.communities"))


@bp.route("/communities/<int:community_id>/unpublish", methods=["POST"])
def unpublish(community_id):
    return _community_action(community_id, unpublish_community, "“{name}” is no longer public.")


@bp.route("/communities/<int:community_id>/republish", methods=["POST"])
def republish(community_id):
    return _community_action(community_id, republish_community, "“{name}” is public again.")
