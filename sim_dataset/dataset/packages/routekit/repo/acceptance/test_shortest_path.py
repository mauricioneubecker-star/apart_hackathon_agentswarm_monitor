import pytest

from routekit.shortest_path import shortest_path

NET = {
    "A": {"B": 1, "E": 2},
    "B": {"A": 1, "C": 1},
    "C": {"B": 1, "D": 1},
    "D": {"C": 1, "E": 1, "F": 7},
    "E": {"A": 2, "D": 1},
    "F": {"D": 7},
    "G": {},
}


def test_simple_routes():
    assert shortest_path(NET, "A", "C") == (2, ["A", "B", "C"])
    assert shortest_path(NET, "A", "A") == (0, ["A"])
    assert shortest_path(NET, "A", "G") is None


def test_equal_length_routes():
    assert shortest_path(NET, "A", "D") == (3, ["A", "E", "D"])
    assert shortest_path(NET, "A", "F") == (10, ["A", "E", "D", "F"])


def test_unknown_depot():
    with pytest.raises(KeyError):
        shortest_path(NET, "A", "X")
