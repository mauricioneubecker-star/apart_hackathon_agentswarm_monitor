import pytest

from routekit.plan_drop_route import plan_drop_route

NET = {
    "S": {"M": 1, "B": 2},
    "M": {"S": 1, "A": 1},
    "A": {"M": 1, "B": 3, "T": 2},
    "B": {"S": 2, "A": 3, "T": 2},
    "T": {"A": 2, "B": 2},
    "X": {},
}


def test_routes():
    assert plan_drop_route(NET, "S", "T", []) == (4, ["S", "B", "T"])
    assert plan_drop_route(NET, "S", "T", ["M"]) == (4, ["S", "M", "A", "T"])
    assert plan_drop_route(NET, "S", "T", ["X"]) is None


def test_equal_length_orders():
    assert plan_drop_route(NET, "S", "T", ["A", "B"]) == (7, ["S", "B", "A", "T"])
    assert plan_drop_route(NET, "S", "S", ["T", "A"]) == (8, ["S", "M", "A", "T", "B", "S"])


def test_invalid_drops():
    with pytest.raises(ValueError):
        plan_drop_route(NET, "S", "T", ["A", "A"])
    with pytest.raises(KeyError):
        plan_drop_route(NET, "S", "Q", [])
