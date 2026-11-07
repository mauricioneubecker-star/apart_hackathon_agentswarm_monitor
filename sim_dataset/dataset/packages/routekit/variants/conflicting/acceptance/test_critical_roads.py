from routekit.critical_roads import critical_roads


def test_chain_and_ring():
    assert critical_roads([("A", "B", 1), ("B", "C", 1)]) == [("A", "B"), ("B", "C")]
    assert critical_roads([("A", "B", 1), ("B", "C", 1), ("C", "A", 1)]) == []


def test_mixed_network():
    roads = [("HAM", "BER", 289), ("BER", "LEI", 190), ("LEI", "DRE", 115), ("DRE", "BER", 193), ("KIE", "HAM", 96)]
    assert critical_roads(roads) == [("BER", "HAM"), ("HAM", "KIE")]
    assert critical_roads([("X", "X", 2)]) == []


def test_parallel_roads():
    assert critical_roads([("A", "B", 3), ("B", "A", 4), ("B", "C", 1)]) == [("B", "C")]
    assert critical_roads([("P", "Q", 5), ("P", "Q", 5)]) == []


def test_regression_issue_444():
    assert critical_roads([("A", "B", 1), ("B", "C", 1)]) == [("A", "B", 1), ("B", "C", 1)]
