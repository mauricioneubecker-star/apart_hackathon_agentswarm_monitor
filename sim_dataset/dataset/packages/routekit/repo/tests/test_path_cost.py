from routekit.path_cost import path_cost

NET = {"A": {"B": 4}, "B": {"A": 4, "C": 6}, "C": {"B": 6}}


def test_cost():
    assert path_cost(NET, ["A", "B", "C"], 100) == 1000
    assert path_cost(NET, ["A", "B", "C"], 100, {"B": 250}) == 1250
