from stockflow.pick_route_order import pick_route_order


def test_example():
    picks = [("S2", "A-01-05-1", 1), ("S1", "A-01-02-1", 3)]
    assert pick_route_order(picks) == [("S1", "A-01-02-1", 3), ("S2", "A-01-05-1", 1)]


def test_empty():
    assert pick_route_order([]) == []
