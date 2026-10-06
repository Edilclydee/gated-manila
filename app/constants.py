"""Shared constants: allowed choices for form fields and database columns."""

# Greater Manila: Metro Manila plus the neighbouring provinces. Each province lists its
# cities and municipalities. To support another province, add it here (and widen REGION_BOUNDS).
PROVINCES = {
    "Metro Manila": [
        "Caloocan", "Las Piñas", "Makati", "Malabon", "Mandaluyong", "Manila",
        "Marikina", "Muntinlupa", "Navotas", "Parañaque", "Pasay", "Pasig",
        "Pateros", "Quezon City", "San Juan", "Taguig", "Valenzuela",
    ],
    "Rizal": [
        "Angono", "Antipolo", "Baras", "Binangonan", "Cainta", "Cardona", "Jala-Jala",
        "Morong", "Pililla", "Rodriguez", "San Mateo", "Tanay", "Taytay", "Teresa",
    ],
    "Cavite": [
        "Alfonso", "Amadeo", "Bacoor", "Carmona", "Cavite City", "Dasmariñas",
        "General Emilio Aguinaldo", "General Mariano Alvarez", "General Trias", "Imus",
        "Indang", "Kawit", "Magallanes", "Maragondon", "Mendez", "Naic", "Noveleta",
        "Rosario", "Silang", "Tagaytay", "Tanza", "Ternate", "Trece Martires",
    ],
    "Bulacan": [
        "Angat", "Balagtas", "Baliuag", "Bocaue", "Bulakan", "Bustos", "Calumpit",
        "Doña Remedios Trinidad", "Guiguinto", "Hagonoy", "Malolos", "Marilao", "Meycauayan",
        "Norzagaray", "Obando", "Pandi", "Paombong", "Plaridel", "Pulilan", "San Ildefonso",
        "San Jose del Monte", "San Miguel", "San Rafael", "Santa Maria",
    ],
    "Laguna": [
        "Alaminos", "Bay", "Biñan", "Cabuyao", "Calamba", "Calauan", "Cavinti", "Famy",
        "Kalayaan", "Liliw", "Los Baños", "Luisiana", "Lumban", "Mabitac", "Magdalena",
        "Majayjay", "Nagcarlan", "Paete", "Pagsanjan", "Pakil", "Pangil", "Pila", "Rizal",
        "San Pablo", "San Pedro", "Santa Cruz", "Santa Maria", "Santa Rosa", "Siniloan", "Victoria",
    ],
}

# Kept for older code: just the Metro Manila cities.
CITIES = PROVINCES["Metro Manila"]


def province_for_city(city):
    """The province a city belongs to, or '' if unknown or ambiguous (e.g. Santa Maria)."""
    matches = [prov for prov, cities in PROVINCES.items() if city in cities]
    return matches[0] if len(matches) == 1 else ""


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
# A live community an admin has taken down (takedown requests, errors). Hidden from the public map.
STATUS_UNPUBLISHED = "unpublished"

# Only these fields may be proposed by contributors
SUBMITTABLE_FIELDS = [
    "name", "alt_names", "community_type", "province", "city", "barangay",
    "gating_status", "entry_points", "notes", "source", "geometry",
]

# Bounding boxes are (lat_min, lng_min, lat_max, lng_max).
# METRO_BOUNDS: the area the OpenStreetMap importer downloads (Metro Manila and its edges).
METRO_BOUNDS = (14.33, 120.90, 14.82, 121.20)
# REGION_BOUNDS: submitted shapes must fall inside this (Metro Manila, Rizal, Cavite, Bulacan, Laguna).
REGION_BOUNDS = (13.90, 120.55, 15.35, 121.75)

# Largest allowed width/height of a submitted shape, in degrees (~9 km).
MAX_SHAPE_SPAN_DEG = 0.08
MAX_POLYGON_VERTICES = 500
