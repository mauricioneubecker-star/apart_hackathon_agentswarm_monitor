from routekit.connected_components import connected_components


def test_regions():
    assert connected_components([("B", "A", 1), ("C", "B", 2)]) == [["A", "B", "C"]]
    assert connected_components([("A", "B", 1)], depots=["Q"]) == [["A", "B"], ["Q"]]
