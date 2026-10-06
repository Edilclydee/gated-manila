"""What approving, rejecting and unpublishing actually do to the database."""
import json

from app import db
from app.constants import (
    STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED, STATUS_UNPUBLISHED,
)
from app.models import Community, utcnow

COMMUNITY_FIELDS = [
    "name", "alt_names", "community_type", "province", "city", "barangay",
    "gating_status", "entry_points", "notes", "source",
]


class ReviewError(Exception):
    """Raised when an action isn't allowed; the message is safe to show the admin."""


def _close(submission, status, admin_id, notes):
    submission.status = status
    submission.reviewed_at = utcnow()
    submission.reviewed_by_id = admin_id
    submission.reviewer_notes = (notes or "").strip() or None


def approve_submission(submission, data, admin_id, notes=None):
    """Publish a pending submission using `data` (already validated, possibly admin-edited)."""
    if submission.status != STATUS_PENDING:
        raise ReviewError("This submission has already been reviewed.")

    if submission.community_id:
        community = submission.community
        if community is None or community.status != STATUS_APPROVED:
            raise ReviewError("The community this edit refers to is no longer public.")
        is_new = False
    else:
        community = Community()
        is_new = True

    for field in COMMUNITY_FIELDS:
        setattr(community, field, data[field])
    community.geometry = json.dumps(data["geometry"])
    community.status = STATUS_APPROVED
    community.last_verified = utcnow()
    if is_new:
        db.session.add(community)

    _close(submission, STATUS_APPROVED, admin_id, notes)
    db.session.commit()
    return community


def reject_submission(submission, admin_id, reason):
    if submission.status != STATUS_PENDING:
        raise ReviewError("This submission has already been reviewed.")
    if not (reason or "").strip():
        raise ReviewError("Please give a reason for rejecting.")
    _close(submission, STATUS_REJECTED, admin_id, reason)
    db.session.commit()


def unpublish_community(community):
    if community.status != STATUS_APPROVED:
        raise ReviewError("Only live communities can be unpublished.")
    community.status = STATUS_UNPUBLISHED
    db.session.commit()


def republish_community(community):
    if community.status != STATUS_UNPUBLISHED:
        raise ReviewError("Only unpublished communities can be republished.")
    community.status = STATUS_APPROVED
    db.session.commit()
