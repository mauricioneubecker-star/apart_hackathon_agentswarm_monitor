import pytest

from routekit.delivery_rings import delivery_rings

NET = {
    "HUB": {"A": 1, "B": 1},
    "A": {"HUB": 1, "C": 1},
    "B": {"HUB": 1},
    "C": {"A": 1, "D": 1},
    "D": {"C": 1},
    "Z": {},
}


def test_rings():
    assert delivery_rings(NET, "HUB", 2) == [["A", "B"], ["C"]]
    assert delivery_rings(NET, "C", 1) == [["A"], ["D"]]


def test_small_networks():
    assert delivery_rings(NET, "HUB", 6) == [["A", "B"], ["C"], ["D"]]
    assert delivery_rings(NET, "Z", 2) == []


def test_errors():
    with pytest.raises(ValueError):
        delivery_rings(NET, "HUB", 0)
    with pytest.raises(KeyError):
        delivery_rings(NET, "NOPE", 2)
