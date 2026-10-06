"""Turn OpenStreetMap elements (Overpass `out geom` output) into simple polygon rings.

Pure Python: no Flask or database needed, so it is easy to test.
Coordinates are [lng, lat] pairs, as in GeoJSON.
"""
import math

MAX_POINTS = 450  # stay under the 500-vertex limit used by submission validation


def _coords(geometry):
    """Overpass geometry list -> [[lng, lat], ...]. Returns [] if any point is missing."""
    if not geometry or any(p is None for p in geometry):
        return []
    return [[p["lon"], p["lat"]] for p in geometry]


def _dist(p, a, b):
    """Distance from point p to the segment a-b (in degrees)."""
    (x, y), (x1, y1), (x2, y2) = p, a, b
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(x - x1, y - y1)
    t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))


def _rdp(points, tolerance):
    """Ramer-Douglas-Peucker line simplification (iterative)."""
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        far, far_i = 0.0, None
        for i in range(a + 1, b):
            d = _dist(points[i], points[a], points[b])
            if d > far:
                far, far_i = d, i
        if far_i is not None and far > tolerance:
            keep[far_i] = True
            stack.extend([(a, far_i), (far_i, b)])
    return [p for p, k in zip(points, keep) if k]


def simplify_ring(ring, max_points=MAX_POINTS):
    """Reduce a closed ring to at most max_points vertices, keeping its overall shape."""
    if len(ring) <= max_points:
        return ring
    open_pts = ring[:-1]
    tolerance = 1e-5  # about 1 metre
    while True:
        simple = _rdp(open_pts, tolerance)
        if len(simple) + 1 <= max_points:
            break
        tolerance *= 2
    return simple + [simple[0]]


def stitch_rings(segments):
    """Join way segments end-to-end into closed rings. Returns None if a ring can't be closed."""
    segments = [list(s) for s in segments if len(s) >= 2]
    rings = []
    while segments:
        ring = segments.pop(0)
        while ring[0] != ring[-1]:
            for i, seg in enumerate(segments):
                if seg[0] == ring[-1]:
                    ring.extend(seg[1:])
                    del segments[i]
                    break
                if seg[-1] == ring[-1]:
                    ring.extend(seg[-2::-1])
                    del segments[i]
                    break
            else:
                return None  # a gap: this relation is incomplete
        rings.append(ring)
    return rings


def element_to_ring(element):
    """Return (ring, None) for a usable shape, or (None, reason) if it must be skipped."""
    kind = element.get("type")
    if kind == "way":
        ring = _coords(element.get("geometry"))
        if len(ring) < 4 or ring[0] != ring[-1]:
            return None, "shape is not a closed area"
    elif kind == "relation":
        outer = [
            _coords(m.get("geometry"))
            for m in element.get("members", [])
            if m.get("type") == "way" and m.get("role") == "outer" and m.get("geometry")
        ]
        if not outer:
            return None, "relation has no outer boundary"
        rings = stitch_rings(outer)
        if rings is None:
            return None, "relation boundary has gaps"
        if len(rings) != 1:
            return None, "relation has several separate parts"
        ring = rings[0]
        if len(ring) < 4:
            return None, "shape is not a closed area"
    else:
        return None, "not a way or relation"
    return simplify_ring(ring), None
