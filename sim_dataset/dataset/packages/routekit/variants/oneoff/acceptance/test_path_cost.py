import pytest

from routekit.path_cost import path_cost

NET = {"A": {"B": 4}, "B": {"A": 4, "C": 6}, "C": {"B": 6, "D": 1}, "D": {"C": 1}}


def test_distance_cost():
    assert path_cost(NET, ["A", "B", "C"], 100) == 1000
    assert path_cost(NET, ["D"], 100) == 0


def test_tolls():
    assert path_cost(NET, ["A", "B", "C", "D"], 10, {"B": 30, "C": 20}) == 150
    assert path_cost(NET, ["A", "B", "C"], 10, {"A": 50, "B": 5, "C": 50}) == 105
    assert path_cost(NET, ["C", "B", "A", "B", "C"], 10, {"B": 7}) == 214


def test_broken_routes():
    with pytest.raises(ValueError):
        path_cost(NET, ["A", "C"], 100)
    with pytest.raises(ValueError):
        path_cost(NET, [], 100)
