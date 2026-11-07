import pytest

from routekit.heaviest_route import heaviest_route

LIMITS = {
    "A": {"B": 40, "E": 30},
    "B": {"A": 40, "C": 30},
    "C": {"B": 30, "D": 35},
    "D": {"C": 35, "E": 30, "F": 12},
    "E": {"A": 30, "D": 30},
    "F": {"D": 12},
    "G": {},
}


def test_heaviest_load():
    assert heaviest_route(LIMITS, "A", "B") == (40, ["A", "B"])
    assert heaviest_route(LIMITS, "A", "F") == (12, ["A", "E", "D", "F"])
    assert heaviest_route(LIMITS, "A", "G") is None


def test_fewest_roads_among_equal_loads():
    assert heaviest_route(LIMITS, "A", "D") == (30, ["A", "E", "D"])


def test_invalid_requests():
    with pytest.raises(ValueError):
        heaviest_route(LIMITS, "A", "A")
    with pytest.raises(KeyError):
        heaviest_route(LIMITS, "A", "Z")
