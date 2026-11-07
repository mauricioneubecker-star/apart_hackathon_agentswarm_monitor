import pytest

from routekit.hub_depots import hub_depots

ROADS = [
    ("BER", "HAM", 289), ("BER", "LEI", 190), ("BER", "DRE", 193), ("LEI", "DRE", 115),
    ("HAM", "KIE", 96), ("HAM", "BRE", 125), ("HAM", "BER", 290),
]


def test_ranking():
    assert hub_depots(ROADS, 2) == [("BER", 3), ("HAM", 3)]
    assert hub_depots(ROADS, 10) == [("BER", 3), ("HAM", 3), ("DRE", 2), ("LEI", 2), ("BRE", 1), ("KIE", 1)]


def test_ties_at_the_cut():
    assert hub_depots(ROADS, 1) == [("BER", 3), ("HAM", 3)]
    assert hub_depots(ROADS, 3) == [("BER", 3), ("HAM", 3), ("DRE", 2), ("LEI", 2)]


def test_invalid_top_n():
    with pytest.raises(ValueError):
        hub_depots(ROADS, 0)
