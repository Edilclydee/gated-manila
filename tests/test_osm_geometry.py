import json
import math

import re

import app.osm_import as osm_import
from app.osm_geometry import element_to_ring, simplify_ring, stitch_rings
from app.constants import METRO_BOUNDS
from app.osm_import import (
    build_query, element_to_submission_data, guess_type, place_from_tags, split_bounds,
)

# lng, lat corners of a small square in Quezon City
P1, P2, P3, P4 = [121.040, 14.670], [121.045, 14.670], [121.045, 14.675], [121.040, 14.675]


def geom(points):
    return [{"lat": lat, "lon": lng} for lng, lat in points]


def way(osm_id, points, **tags):
    return {"type": "way", "id": osm_id, "tags": tags, "geometry": geom(points)}


def relation(osm_id, member_point_lists, **tags):
    members = [{"type": "way", "role": "outer", "geometry": geom(pts)} for pts in member_point_lists]
    return {"type": "relation", "id": osm_id, "tags": tags, "members": members}


def test_closed_way_becomes_ring():
    ring, reason = element_to_ring(way(1, [P1, P2, P3, P4, P1]))
    assert reason is None and ring[0] == ring[-1] and len(ring) == 5


def test_open_way_is_skipped():
    ring, reason = element_to_ring(way(1, [P1, P2, P3]))
    assert ring is None and reason


def test_relation_segments_are_stitched_even_if_reversed():
    ring, reason = element_to_ring(relation(2, [[P1, P2, P3], [P1, P4, P3]]))
    assert reason is None
    assert ring[0] == ring[-1]
    assert {tuple(p) for p in ring} == {tuple(P1), tuple(P2), tuple(P3), tuple(P4)}


def test_relation_with_gap_is_skipped():
    ring, reason = element_to_ring(relation(3, [[P1, P2, P3]]))
    assert ring is None and "gaps" in reason


def test_relation_with_two_separate_parts_is_skipped():
    far = [[121.10, 14.60], [121.11, 14.60], [121.11, 14.61], [121.10, 14.60]]
    ring, reason = element_to_ring(relation(4, [[P1, P2, P3, P4, P1], far]))
    assert ring is None and "several" in reason


def test_stitch_rings_returns_none_when_unclosable():
    assert stitch_rings([[P1, P2], [P3, P4]]) is None


def test_big_ring_is_simplified_under_limit():
    ring = [[121.04 + 0.004 * math.cos(t / 2000 * 2 * math.pi),
             14.67 + 0.004 * math.sin(t / 2000 * 2 * math.pi)] for t in range(2000)]
    ring.append(ring[0])
    simple = simplify_ring(ring)
    assert len(simple) <= 450 and simple[0] == simple[-1]
    lngs = [p[0] for p in simple]
    assert abs((max(lngs) - min(lngs)) - 0.008) < 0.0005  # overall size preserved


def test_valid_way_becomes_submission_data():
    data, reason = element_to_submission_data(
        way(123, [P1, P2, P3, P4, P1], name="Sample Village", access="private", **{"addr:city": "Quezon City"}))
    assert reason is None
    assert data["name"] == "Sample Village"
    assert data["province"] == "Metro Manila"
    assert data["city"] == "Quezon City"
    assert data["community_type"] == "village"
    assert data["gating_status"] == "open_or_unclear"
    assert data["source"] == "https://www.openstreetmap.org/way/123"
    assert "access tag: private" in data["notes"]
    assert data["geometry"]["type"] == "Polygon"


def test_unknown_city_left_blank_for_admin():
    data, _ = element_to_submission_data(way(5, [P1, P2, P3, P4, P1], name="X Homes"))
    assert data["city"] == "" and data["province"] == ""


def test_unnamed_elements_are_skipped():
    data, reason = element_to_submission_data(way(6, [P1, P2, P3, P4, P1]))
    assert data is None and reason == "no name"


def test_shape_outside_metro_manila_is_skipped():
    far = [[139.69, 35.68], [139.70, 35.68], [139.70, 35.69], [139.69, 35.68]]
    data, reason = element_to_submission_data(way(7, far, name="Tokyo Place"))
    assert data is None and reason


def test_place_matching():
    assert place_from_tags({"addr:city": "Makati City"}) == ("Metro Manila", "Makati")
    assert place_from_tags({"addr:city": "City of Manila"}) == ("Metro Manila", "Manila")
    assert place_from_tags({"addr:city": "Paranaque"}) == ("Metro Manila", "Parañaque")
    assert place_from_tags({"addr:municipality": "Las Piñas"}) == ("Metro Manila", "Las Piñas")
    assert place_from_tags({"addr:city": "Antipolo City"}) == ("Rizal", "Antipolo")
    assert place_from_tags({"addr:city": "Dasmarinas"}) == ("Cavite", "Dasmariñas")
    assert place_from_tags({"addr:city": "Gen. Trias"}) == ("Cavite", "General Trias")
    assert place_from_tags({"addr:city": "Montalban"}) == ("Rizal", "Rodriguez")
    assert place_from_tags({"addr:city": "Cebu City"}) == ("", "")


def test_ambiguous_city_needs_province_to_resolve():
    assert place_from_tags({"addr:city": "Santa Maria"}) == ("", "")
    assert place_from_tags({"addr:city": "Santa Maria", "addr:province": "Bulacan"}) == ("Bulacan", "Santa Maria")
    assert place_from_tags({"addr:city": "Sta. Maria", "addr:province": "Laguna"}) == ("Laguna", "Santa Maria")


def test_province_alone_is_kept_when_city_unknown():
    assert place_from_tags({"addr:province": "Rizal"}) == ("Rizal", "")
    assert place_from_tags({"addr:province": "NCR"}) == ("Metro Manila", "")


def test_type_guess():
    assert guess_type("Greenwoods Village") == "village"
    assert guess_type("Greenwoods Subdivision") == "subdivision"


def test_query_contains_bounds_and_broad_flag():
    strict, broad = build_query(), build_query(broad=True)
    assert "14.33" in strict and "121.2" in strict and "out geom" in strict
    assert "access" in strict and "subdivision" not in strict
    assert "subdivision" in broad


def test_tiles_cover_metro_manila_exactly():
    tiles = split_bounds()
    assert len(tiles) == 4
    south, west, north, east = METRO_BOUNDS
    assert min(t[0] for t in tiles) == south and max(t[2] for t in tiles) == north
    assert min(t[1] for t in tiles) == west and max(t[3] for t in tiles) == east


def test_query_can_target_a_tile():
    query = build_query(bounds=(14.5, 121.0, 14.6, 121.1))
    assert "(14.5,121.0,14.6,121.1)" in query


def _fake_server(fail_if_lat_span_over):
    """Pretend Overpass: big areas time out, small ones succeed with one element."""
    def fake_post(query, rounds=2):
        s, w, n, e = (float(x) for x in re.search(r"\(([\d.]+),([\d.]+),([\d.]+),([\d.]+)\)", query).groups())
        if n - s > fail_if_lat_span_over:
            raise osm_import.OsmImportError("504")
        return [way(int(s * 1000 + w), [P1, P2, P3, P4, P1], name="N")]
    return fake_post


def test_failed_area_is_retried_in_smaller_pieces():
    original = osm_import._post_query
    osm_import._post_query = _fake_server(fail_if_lat_span_over=0.13)
    try:
        elements, failed = osm_import.fetch_overpass()
    finally:
        osm_import._post_query = original
    assert failed == []
    assert len(elements) > 4  # more pieces than the original 4 tiles


def test_unreachable_areas_are_reported_not_fatal():
    original = osm_import._post_query
    osm_import._post_query = _fake_server(fail_if_lat_span_over=0.0)
    try:
        elements, failed = osm_import.fetch_overpass()
    finally:
        osm_import._post_query = original
    assert elements == []
    assert len(failed) == 4 * 4 * 4  # every tile split twice
