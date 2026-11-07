import pytest

from routekit.hop_distances import hop_distances

NET = {
    "A": {"C": 5, "B": 2},
    "B": {"A": 2, "Z": 1},
    "C": {"A": 5, "D": 1},
    "D": {"C": 1, "E": 4},
    "E": {"D": 4},
    "Z": {"B": 1},
    "Q": {},
}


def test_hop_counts():
    assert hop_distances(NET, "A") == {"A": 0, "B": 1, "C": 1, "D": 2, "Z": 2, "E": 3}
    assert hop_distances(NET, "Q") == {"Q": 0}
    assert hop_distances(NET, "A", max_hops=1) == {"A": 0, "B": 1, "C": 1}


def test_report_order():
    assert list(hop_distances(NET, "A")) == ["A", "B", "C", "D", "Z", "E"]
    assert list(hop_distances(NET, "E", max_hops=2)) == ["E", "D", "C"]


def test_unknown_source():
    with pytest.raises(KeyError):
        hop_distances(NET, "X")
