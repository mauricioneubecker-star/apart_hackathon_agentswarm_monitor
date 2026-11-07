from routekit.critical_roads import critical_roads


def test_bridges():
    assert critical_roads([("A", "B", 1), ("B", "C", 1), ("C", "A", 1), ("C", "D", 4)]) == [("C", "D")]
    assert critical_roads([("B", "A", 1)]) == [("A", "B")]
