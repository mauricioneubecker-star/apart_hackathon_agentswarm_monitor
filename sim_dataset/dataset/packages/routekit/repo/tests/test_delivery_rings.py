from routekit.delivery_rings import delivery_rings

NET = {"HUB": {"A": 1, "B": 1}, "A": {"HUB": 1, "C": 1}, "B": {"HUB": 1}, "C": {"A": 1}}


def test_rings():
    assert delivery_rings(NET, "HUB", 2) == [["A", "B"], ["C"]]
    assert delivery_rings(NET, "HUB", 1) == [["A", "B"]]
