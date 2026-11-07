import pytest

from routekit.isolated_by_closures import isolated_by_closures

ROADS = [("BER", "HAM", 289), ("HAM", "KIE", 96), ("BER", "LEI", 190), ("LEI", "DRE", 115), ("BER", "DRE", 193)]


def test_closures():
    assert isolated_by_closures(ROADS, "BER", []) == []
    assert isolated_by_closures(ROADS, "BER", [("BER", "HAM")]) == ["HAM", "KIE"]
    assert isolated_by_closures(ROADS, "BER", [("BER", "LEI"), ("LEI", "DRE")]) == ["LEI"]
    assert isolated_by_closures([("A", "B", 1)], "A", [("A", "B")]) == ["B"]


def test_closure_orientation():
    assert isolated_by_closures(ROADS, "BER", [("KIE", "HAM")]) == ["KIE"]
    assert isolated_by_closures([("A", "B", 1), ("B", "C", 1)], "A", [("C", "B")], directed=True) == ["C"]


def test_unknown_depot():
    with pytest.raises(KeyError):
        isolated_by_closures(ROADS, "XXX", [])


def test_regression_issue_388():
    assert isolated_by_closures(ROADS, "BER", [("BER", "HAM")]) == ["HAM"]
