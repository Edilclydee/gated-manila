import json
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.constants import STATUS_APPROVED, STATUS_PENDING


def utcnow():
    return datetime.now(timezone.utc)


class Community(db.Model):
    """A gated community or subdivision. Only status='approved' rows are public."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    province = db.Column(db.String(60), nullable=False, default="Metro Manila", index=True)
    alt_names = db.Column(db.String(300))
    community_type = db.Column(db.String(30), nullable=False, default="subdivision")
    city = db.Column(db.String(60), nullable=False, index=True)
    barangay = db.Column(db.String(100))
    gating_status = db.Column(db.String(30), nullable=False, default="open_or_unclear")
    entry_points = db.Column(db.Integer)
    notes = db.Column(db.Text)
    source = db.Column(db.String(500))  # evidence: link, photo, "I live here", etc.
    geometry = db.Column(db.Text, nullable=False)  # GeoJSON geometry (Polygon or Point) as text
    status = db.Column(db.String(20), nullable=False, default=STATUS_PENDING, index=True)
    last_verified = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    submissions = db.relationship("Submission", back_populates="community")

    @property
    def geometry_dict(self):
        return json.loads(self.geometry)

    def to_feature(self):
        """GeoJSON Feature used by the public map."""
        return {
            "type": "Feature",
            "geometry": self.geometry_dict,
            "properties": {
                "id": self.id,
                "name": self.name,
                "alt_names": self.alt_names,
                "type": self.community_type,
                "province": self.province,
                "city": self.city,
                "barangay": self.barangay,
                "gating_status": self.gating_status,
                "entry_points": self.entry_points,
                "notes": self.notes,
                "last_verified": self.last_verified.date().isoformat() if self.last_verified else None,
            },
        }

    @classmethod
    def approved(cls):
        return cls.query.filter_by(status=STATUS_APPROVED)


class Submission(db.Model):
    """A proposed new community (community_id is NULL) or edit (community_id set).

    Nothing here touches live data until an admin approves it.
    """

    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.Integer, db.ForeignKey("community.id"), nullable=True)
    proposed_data = db.Column(db.Text, nullable=False)  # JSON of SUBMITTABLE_FIELDS
    contact = db.Column(db.String(200))  # optional, never shown publicly
    status = db.Column(db.String(20), nullable=False, default=STATUS_PENDING, index=True)
    reviewer_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    reviewed_at = db.Column(db.DateTime(timezone=True))
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("admin.id"))

    community = db.relationship("Community", back_populates="submissions")
    reviewed_by = db.relationship("Admin")

    @property
    def data(self):
        return json.loads(self.proposed_data)

    @data.setter
    def data(self, value):
        self.proposed_data = json.dumps(value)


class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    def set_password(self, password):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
