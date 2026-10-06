from flask import Blueprint, abort, current_app, redirect, render_template, request, url_for

from app import db
from app.constants import (
    CITIES, COMMUNITY_TYPES, GATING_LABELS, STATUS_APPROVED,
)
from app.extensions import limiter
from app.models import Community, Submission
from app.turnstile import verify_turnstile
from app.validation import validate_submission

bp = Blueprint("submit", __name__)

TYPE_LABELS = {
    "subdivision": "Subdivision",
    "village": "Village",
    "condo_compound": "Condo compound",
    "other": "Other",
}


def _community_values(community):
    """Pre-fill values when suggesting an edit to an existing community."""
    return {
        "name": community.name,
        "alt_names": community.alt_names or "",
        "community_type": community.community_type,
        "city": community.city,
        "barangay": community.barangay or "",
        "gating_status": community.gating_status,
        "entry_points": community.entry_points if community.entry_points is not None else "",
        "notes": community.notes or "",
        "geometry": community.geometry,
        "source": "",  # contributors must give fresh evidence for an edit
    }


def _render_form(values, errors, community, status=200):
    lat, lng = current_app.config["MAP_CENTER"]
    page_config = {
        "lat": lat,
        "lng": lng,
        "zoom": current_app.config["MAP_ZOOM"],
        "excludeId": community.id if community else None,
    }
    return render_template(
        "submit.html",
        values=values,
        errors=errors,
        community=community,
        cities=CITIES,
        type_labels={k: TYPE_LABELS[k] for k in COMMUNITY_TYPES},
        gating_labels=GATING_LABELS,
        site_key=current_app.config["TURNSTILE_SITE_KEY"],
        page_config=page_config,
        initial_geometry=values.get("geometry") or "",
    ), status


@bp.route("/submit", methods=["GET", "POST"])
@limiter.limit(lambda: current_app.config["SUBMIT_RATE_LIMIT"], methods=["POST"])
def submit():
    community = None
    edit_id = request.args.get("edit", type=int)
    if edit_id:
        community = db.session.get(Community, edit_id)
        if community is None or community.status != STATUS_APPROVED:
            abort(404)

    if request.method == "GET":
        values = _community_values(community) if community else {"gating_status": "open_or_unclear"}
        return _render_form(values, [], community)

    # Honeypot: real people never see or fill this field. Pretend success to bots.
    if request.form.get("website"):
        return redirect(url_for("submit.thanks"))

    data, errors = validate_submission(request.form)
    if not verify_turnstile(request.form.get("cf-turnstile-response", ""), request.remote_addr):
        errors.append("Please complete the spam check and try again.")

    if errors:
        values = request.form.to_dict()
        return _render_form(values, errors, community, status=400)

    contact = data.pop("contact")
    submission = Submission(community_id=community.id if community else None, contact=contact)
    submission.data = data
    db.session.add(submission)
    db.session.commit()
    return redirect(url_for("submit.thanks"))


@bp.route("/submit/thanks")
def thanks():
    return render_template("thanks.html")
