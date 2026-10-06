"""Server-side validation of contributor submissions. Never trust the browser."""
import json
import math

from app.constants import (
    COMMUNITY_TYPES, GATING_STATUSES, MAX_POLYGON_VERTICES,
    MAX_SHAPE_SPAN_DEG, PROVINCES, REGION_BOUNDS,
)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _in_bounds(lng, lat):
    lat_min, lng_min, lat_max, lng_max = REGION_BOUNDS
    return lat_min <= lat <= lat_max and lng_min <= lng <= lng_max


def validate_geometry(raw):
    """Return (clean_geometry_dict, None) or (None, error_message)."""
    try:
        geom = json.loads(raw or "")
    except (ValueError, RecursionError):
        return None, "Please draw a boundary or drop a pin on the map."
    if not isinstance(geom, dict):
        return None, "The map shape is invalid."

    gtype, coords = geom.get("type"), geom.get("coordinates")
    if gtype == "Point":
        points = [coords]
    elif gtype == "Polygon":
        if not (isinstance(coords, list) and len(coords) == 1 and isinstance(coords[0], list)):
            return None, "The boundary must be a single polygon."
        points = coords[0]
        if not 4 <= len(points) <= MAX_POLYGON_VERTICES:
            return None, "The boundary needs at least 3 corners and no more than 500 points."
        if points[0] != points[-1]:
            return None, "The boundary is not closed."
    else:
        return None, "Only a polygon boundary or a single pin is allowed."

    clean = []
    for p in points:
        if not (isinstance(p, list) and len(p) == 2 and all(_is_number(x) for x in p)):
            return None, "The map shape has invalid coordinates."
        lng, lat = p
        if not _in_bounds(lng, lat):
            return None, "The shape must be inside the Greater Manila area (Metro Manila, Rizal, Cavite, Bulacan or Laguna)."
        clean.append([round(lng, 6), round(lat, 6)])

    if gtype == "Polygon":
        lngs = [p[0] for p in clean]
        lats = [p[1] for p in clean]
        if max(lngs) - min(lngs) > MAX_SHAPE_SPAN_DEG or max(lats) - min(lats) > MAX_SHAPE_SPAN_DEG:
            return None, "That boundary is too large for a single community."
        clean[-1] = clean[0]
        return {"type": "Polygon", "coordinates": [clean]}, None
    return {"type": "Point", "coordinates": clean[0]}, None


def validate_submission(form):
    """Return (clean_data, errors). clean_data also holds 'contact', which is stored separately."""
    errors = []
    data = {}

    def text(key, label, max_len, required=False):
        value = (form.get(key) or "").strip()
        if required and not value:
            errors.append(f"{label} is required.")
        elif len(value) > max_len:
            errors.append(f"{label} must be {max_len} characters or fewer.")
        data[key] = value or None

    text("name", "Name", 200, required=True)
    text("alt_names", "Other names", 300)
    text("barangay", "Barangay", 100)
    text("notes", "Notes", 1000)
    text("source", "Source or evidence", 500, required=True)
    text("contact", "Contact", 200)

    def choice(key, label, allowed):
        value = (form.get(key) or "").strip()
        if value not in allowed:
            errors.append(f"Please choose a valid {label}.")
        data[key] = value

    province = (form.get("province") or "").strip()
    city = (form.get("city") or "").strip()
    if province not in PROVINCES:
        errors.append("Please choose a valid province.")
    elif city not in PROVINCES[province]:
        errors.append(f"Please choose a valid city or municipality in {province}.")
    data["province"] = province
    data["city"] = city
    choice("community_type", "type", COMMUNITY_TYPES)
    choice("gating_status", "gating status", GATING_STATUSES)

    raw_entries = (form.get("entry_points") or "").strip()
    data["entry_points"] = None
    if raw_entries:
        try:
            entries = int(raw_entries)
            if not 0 <= entries <= 50:
                raise ValueError
            data["entry_points"] = entries
        except ValueError:
            errors.append("Entry points must be a whole number from 0 to 50.")

    geometry, geom_error = validate_geometry(form.get("geometry"))
    if geom_error:
        errors.append(geom_error)
    data["geometry"] = geometry

    return data, errors
