"""Import candidate subdivisions from OpenStreetMap into the pending review queue.

Nothing imported here is public: every record becomes a pending Submission that an
admin must check (especially the city and the gating status) before approving.

OSM data is licensed ODbL: keep the attribution and the per-record source link.
"""
import json
import re

from app.constants import CITIES, METRO_BOUNDS
from app.osm_geometry import element_to_ring
from app.validation import validate_geometry

# Public Overpass servers, tried in order if one is busy or down.
ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
USER_AGENT = "gated-manila-importer/0.1 (open-source community map)"
IMPORT_CONTACT = "Imported from OpenStreetMap"
OSM_REF_RE = re.compile(r"openstreetmap\.org/(way|relation)/(\d+)")
NAME_KEYWORDS = "subdivision|village|homes|estates|heights|hills"


class OsmImportError(Exception):
    """A problem fetching or reading OSM data; the message is safe to show."""


def split_bounds(parts=2, bounds=None):
    """Cut a bounding box (default: Metro Manila) into parts x parts tiles."""
    south, west, north, east = bounds or METRO_BOUNDS
    lat_step = (north - south) / parts
    lng_step = (east - west) / parts
    return [
        (round(south + i * lat_step, 4), round(west + j * lng_step, 4),
         round(south + (i + 1) * lat_step, 4), round(west + (j + 1) * lng_step, 4))
        for i in range(parts) for j in range(parts)
    ]


def build_query(broad=False, bounds=None):
    """Overpass QL for named residential areas tagged as private access.

    broad=True also includes residential areas whose name looks like a subdivision
    (more results, but many will not be gated). bounds is (south, west, north, east);
    it defaults to all of Metro Manila.
    """
    south, west, north, east = bounds or METRO_BOUNDS
    bbox = f"({south},{west},{north},{east})"
    selectors = ['["landuse"="residential"]["name"]["access"~"^(private|permit)$"]']
    if broad:
        selectors.append(f'["landuse"="residential"]["name"~"{NAME_KEYWORDS}",i]')
    lines = [f"  {kind}{sel}{bbox};" for sel in selectors for kind in ("way", "relation")]
    return "[out:json][timeout:90];\n(\n" + "\n".join(lines) + "\n);\nout geom;"


def _post_query(query, rounds=2):
    """Run one query, trying each server in turn (and waiting between rounds)."""
    import time

    import requests

    last_error = None
    for attempt in range(rounds):
        for url in ENDPOINTS:
            try:
                resp = requests.post(
                    url, data={"data": query}, headers={"User-Agent": USER_AGENT}, timeout=120,
                )
                resp.raise_for_status()
                payload = resp.json()
                remark = str(payload.get("remark", ""))
                if "error" in remark.lower() or "timed out" in remark.lower():
                    raise ValueError(remark)  # server gave up but still answered 200
                return payload.get("elements", [])
            except (requests.RequestException, ValueError) as err:
                last_error = err
        if attempt < rounds - 1:
            time.sleep(10)
    raise OsmImportError(f"Could not fetch data from Overpass: {last_error}")


def _fetch_area(bounds, broad, progress, depth=0):
    """Fetch one area; if it fails, retry it as four smaller pieces.

    Returns (elements, failed_areas). Areas that still fail at the smallest size are
    reported instead of aborting the whole import.
    """
    try:
        return _post_query(build_query(broad=broad, bounds=bounds), rounds=2 if depth == 0 else 1), []
    except OsmImportError:
        if depth >= 2:
            return [], [bounds]
        if progress:
            progress("  That area timed out; retrying it in smaller pieces...")
        elements, failed = [], []
        for piece in split_bounds(bounds=bounds):
            got, bad = _fetch_area(piece, broad, progress, depth + 1)
            elements.extend(got)
            failed.extend(bad)
        return elements, failed


def fetch_overpass(broad=False, progress=None):
    """Download candidates area by area. Returns (elements, failed_areas)."""
    merged, failed = {}, []
    tiles = split_bounds()
    for number, bounds in enumerate(tiles, start=1):
        if progress:
            progress(f"Downloading area {number} of {len(tiles)}...")
        elements, bad = _fetch_area(bounds, broad, progress)
        failed.extend(bad)
        for element in elements:
            merged[(element.get("type"), element.get("id"))] = element
    return list(merged.values()), failed


def load_elements(path):
    """Read elements from a saved Overpass JSON file."""
    try:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, ValueError) as err:
        raise OsmImportError(f"Could not read {path}: {err}")
    return payload if isinstance(payload, list) else payload.get("elements", [])


def _norm_city(text):
    t = (text or "").lower().strip().replace("ñ", "n")
    if t.startswith("city of "):
        t = t[len("city of "):]
    if t.endswith(" city"):
        t = t[: -len(" city")]
    return t.strip()


_CITY_LOOKUP = {_norm_city(c): c for c in CITIES}


def city_from_tags(tags):
    """Match an OSM address tag to one of our cities, or '' if unsure (the admin then picks)."""
    for key in ("addr:city", "addr:municipality", "is_in:city"):
        match = _CITY_LOOKUP.get(_norm_city(tags.get(key)))
        if match:
            return match
    return ""


def guess_type(name):
    return "village" if "village" in name.lower() else "subdivision"


def element_ref(element):
    return f"{element.get('type')}/{element.get('id')}"


def element_to_submission_data(element):
    """Return (data_dict, None) ready for a Submission, or (None, reason_skipped)."""
    tags = element.get("tags") or {}
    name = (tags.get("name") or "").strip()
    if not name:
        return None, "no name"

    ring, reason = element_to_ring(element)
    if reason:
        return None, reason
    geometry, error = validate_geometry(json.dumps({"type": "Polygon", "coordinates": [ring]}))
    if error:
        return None, "shape outside Metro Manila or too large"

    alts = []
    for key in ("alt_name", "name:en", "old_name", "official_name"):
        value = (tags.get(key) or "").strip()
        if value and value != name and value not in alts:
            alts.append(value)

    ref = element_ref(element)
    access = tags.get("access")
    note = f"Imported from OpenStreetMap ({ref})."
    if access:
        note += f" OSM access tag: {access}."
    note += " Verify the city, gating status and boundary before approving."

    data = {
        "name": name[:200],
        "alt_names": "; ".join(alts)[:300] or None,
        "community_type": guess_type(name),
        "city": city_from_tags(tags),
        "barangay": None,
        "gating_status": "open_or_unclear",  # never assumed; the reviewer decides
        "entry_points": None,
        "notes": note[:1000],
        "source": f"https://www.openstreetmap.org/{ref}",
        "geometry": geometry,
    }
    return data, None


def existing_osm_refs():
    """OSM elements we already have (as submissions of any status, or live communities)."""
    from app import db
    from app.models import Community, Submission

    refs = set()

    def add(source):
        match = OSM_REF_RE.search(source or "")
        if match:
            refs.add(f"{match.group(1)}/{match.group(2)}")

    for (source,) in db.session.query(Community.source).all():
        add(source)
    for submission in Submission.query.all():
        add(submission.data.get("source"))
    return refs


def run_import(elements, dry_run=False, limit=None):
    """Create pending submissions from OSM elements. Returns a stats dict."""
    from app import db
    from app.models import Submission

    stats = {"found": len(elements), "created": 0, "duplicates": 0, "skipped": {}}
    seen = existing_osm_refs()

    for element in elements:
        if limit is not None and stats["created"] >= limit:
            break
        ref = element_ref(element)
        if ref in seen:
            stats["duplicates"] += 1
            continue
        data, reason = element_to_submission_data(element)
        if reason:
            stats["skipped"][reason] = stats["skipped"].get(reason, 0) + 1
            continue
        seen.add(ref)
        stats["created"] += 1
        if not dry_run:
            submission = Submission(contact=IMPORT_CONTACT)
            submission.data = data
            db.session.add(submission)

    if not dry_run:
        db.session.commit()
    return stats
