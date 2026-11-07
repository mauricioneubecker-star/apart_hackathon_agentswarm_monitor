from routekit.shortest_path import shortest_path

NET = {"A": {"B": 2}, "B": {"A": 2, "C": 3}, "C": {"B": 3}, "D": {}}


def test_routes():
    assert shortest_path(NET, "A", "C") == (5, ["A", "B", "C"])
    assert shortest_path(NET, "C", "C") == (0, ["C"])
    assert shortest_path(NET, "A", "D") is None
