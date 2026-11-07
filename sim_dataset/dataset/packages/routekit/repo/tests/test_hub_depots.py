from routekit.hub_depots import hub_depots


def test_rank():
    roads = [("A", "B", 1), ("A", "C", 1), ("C", "D", 1)]
    assert hub_depots(roads, 2) == [("A", 2), ("C", 2)]
    assert hub_depots(roads + [("A", "B", 5)], 4) == [("A", 2), ("C", 2), ("B", 1), ("D", 1)]
