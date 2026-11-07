from routekit.isolated_by_closures import isolated_by_closures

ROADS = [("BER", "HAM", 289), ("HAM", "KIE", 96), ("BER", "LEI", 190)]


def test_isolated():
    assert isolated_by_closures(ROADS, "BER", [("BER", "HAM")]) == ["HAM", "KIE"]
    assert isolated_by_closures(ROADS, "BER", [("XXX", "YYY")]) == []
