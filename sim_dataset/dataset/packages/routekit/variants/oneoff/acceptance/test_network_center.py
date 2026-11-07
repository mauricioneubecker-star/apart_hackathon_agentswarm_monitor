import pytest

from routekit.network_center import network_center


def undirected(*pairs):
    adj = {}
    for a, b in pairs:
        adj.setdefault(a, {})[b] = 1
        adj.setdefault(b, {})[a] = 1
    return adj


def test_line_and_single_depot():
    assert network_center(undirected(("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"))) == "B"
    assert network_center({"SOLO": {}}) == "SOLO"


def test_equal_eccentricity():
    assert network_center(undirected(("A", "B"), ("B", "C"), ("C", "D"), ("C", "E"))) == "C"
    assert network_center(undirected(("A", "B"), ("B", "C"), ("C", "D"))) == "B"


def test_unusable_networks():
    with pytest.raises(ValueError):
        network_center({})
    with pytest.raises(ValueError):
        network_center(undirected(("A", "B"), ("C", "D")))
