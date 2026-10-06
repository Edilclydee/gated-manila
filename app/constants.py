"""Shared constants: allowed choices for form fields and database columns."""

# Metro Manila: 16 cities plus the municipality of Pateros
CITIES = [
    "Caloocan", "Las Piñas", "Makati", "Malabon", "Mandaluyong", "Manila",
    "Marikina", "Muntinlupa", "Navotas", "Parañaque", "Pasay", "Pasig",
    "Pateros", "Quezon City", "San Juan", "Taguig", "Valenzuela",
]

COMMUNITY_TYPES = ["subdivision", "village", "condo_compound", "other"]

GATING_STATUSES = ["fully_gated", "partially_gated", "open_or_unclear"]

GATING_LABELS = {
    "fully_gated": "Fully gated",
    "partially_gated": "Partially gated",
    "open_or_unclear": "Open or unclear",
}

# Map colours per gating status
GATING_COLORS = {
    "fully_gated": "#c0392b",
    "partially_gated": "#e67e22",
    "open_or_unclear": "#7f8c8d",
}

# Lifecycle of a Community record and of a Submission
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUSES = [STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED]

# Only these fields may be proposed by contributors
SUBMITTABLE_FIELDS = [
    "name", "alt_names", "community_type", "city", "barangay",
    "gating_status", "entry_points", "notes", "source", "geometry",
]

# Rough bounding box around Metro Manila: (lat_min, lng_min, lat_max, lng_max).
# Submitted shapes must fall inside it.
METRO_BOUNDS = (14.33, 120.90, 14.82, 121.20)

# Largest allowed width/height of a submitted shape, in degrees (~9 km).
MAX_SHAPE_SPAN_DEG = 0.08
MAX_POLYGON_VERTICES = 500
