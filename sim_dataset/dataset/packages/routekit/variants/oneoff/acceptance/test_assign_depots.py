import pytest

from routekit.assign_depots import assign_depots

NET = {
    "D1": {"X": 2, "C3": 9, "C4": 5},
    "X": {"D1": 2, "C1": 2},
    "C1": {"X": 2, "D2": 4},
    "D2": {"C1": 4, "C2": 1, "C4": 5},
    "C2": {"D2": 1},
    "C3": {"D1": 9},
    "C4": {"D1": 5, "D2": 5},
    "ISO": {},
}


def test_nearest_depot():
    assert assign_depots(NET, ["D1", "D2"], ["C2", "C3"]) == {"C2": "D2", "C3": "D2"}
    assert assign_depots(NET, ["D1", "D2"], ["ISO", "D1"]) == {"ISO": None, "D1": "D1"}


def test_equal_distances():
    assert assign_depots(NET, ["D1", "D2"], ["C1"]) == {"C1": "D2"}
    assert assign_depots(NET, ["D2", "D1"], ["C4", "C1"]) == {"C4": "D1", "C1": "D2"}


def test_unknown_codes():
    with pytest.raises(KeyError):
        assign_depots(NET, ["D9"], ["C1"])
