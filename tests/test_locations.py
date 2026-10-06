from app.constants import PROVINCES, REGION_BOUNDS, province_for_city


def test_supported_provinces():
    assert list(PROVINCES) == ["Metro Manila", "Rizal", "Cavite", "Bulacan", "Laguna"]


def test_city_counts_match_official_lists():
    assert len(PROVINCES["Metro Manila"]) == 17
    assert len(PROVINCES["Rizal"]) == 14
    assert len(PROVINCES["Cavite"]) == 23
    assert len(PROVINCES["Bulacan"]) == 24
    assert len(PROVINCES["Laguna"]) == 30


def test_no_duplicate_cities_within_a_province():
    for province, cities in PROVINCES.items():
        assert len(cities) == len(set(cities)), province


def test_province_for_city():
    assert province_for_city("Makati") == "Metro Manila"
    assert province_for_city("Antipolo") == "Rizal"
    assert province_for_city("Santa Maria") == ""  # exists in Bulacan and Laguna
    assert province_for_city("Nowhere") == ""


def test_region_bounds_are_ordered():
    lat_min, lng_min, lat_max, lng_max = REGION_BOUNDS
    assert lat_min < lat_max and lng_min < lng_max
