from routekit.hop_distances import hop_distances

NET = {"A": {"B": 3}, "B": {"A": 3, "C": 1}, "C": {"B": 1}}


def test_hops():
    assert hop_distances(NET, "A") == {"A": 0, "B": 1, "C": 2}
    assert hop_distances(NET, "A", max_hops=1) == {"A": 0, "B": 1}
