import json

from app.validation import validate_geometry, validate_submission

SQUARE = {
    "type": "Polygon",
    "coordinates": [[[121.04, 14.67], [121.05, 14.67], [121.05, 14.68], [121.04, 14.68], [121.04, 14.67]]],
}
PIN = {"type": "Point", "coordinates": [121.04, 14.67]}


def geom(value):
    return validate_geometry(json.dumps(value))


def test_valid_polygon_and_pin():
    assert geom(SQUARE)[1] is None
    assert geom(PIN)[1] is None


def test_empty_or_garbage_geometry_rejected():
    assert validate_geometry("")[1]
    assert validate_geometry("not json")[1]
    assert validate_geometry("[1, 2]")[1]


def test_unclosed_polygon_rejected():
    bad = {"type": "Polygon", "coordinates": [SQUARE["coordinates"][0][:-1] + [[121.0401, 14.6701]]]}
    assert geom(bad)[1]


def test_outside_metro_manila_rejected():
    assert geom({"type": "Point", "coordinates": [139.69, 35.68]})[1]  # Tokyo


def test_oversized_polygon_rejected():
    big = {"type": "Polygon", "coordinates": [[[120.95, 14.4], [121.15, 14.4], [121.15, 14.7], [120.95, 14.7], [120.95, 14.4]]]}
    assert geom(big)[1]


def test_other_geometry_types_rejected():
    assert geom({"type": "LineString", "coordinates": [[121.0, 14.6], [121.01, 14.61]]})[1]


def test_submission_requires_fields_and_valid_choices():
    data, errors = validate_submission({"city": "Atlantis"})
    assert errors
    assert any("Name" in e for e in errors)
    assert any("Source" in e for e in errors)


def test_valid_submission_has_no_errors():
    form = {
        "name": "Test Village", "city": "Marikina", "community_type": "subdivision",
        "gating_status": "fully_gated", "source": "I live here", "entry_points": "2",
        "geometry": json.dumps(SQUARE),
    }
    data, errors = validate_submission(form)
    assert errors == []
    assert data["entry_points"] == 2
