from routekit.connected_components import connected_components


def test_single_region():
    assert connected_components([("B", "A", 1), ("C", "B", 2)]) == [["A", "B", "C"]]
    assert connected_components([]) == []


def test_region_order():
    roads = [("A", "B", 1), ("X", "Y", 1), ("Y", "Z", 1), ("N", "M", 2)]
    assert connected_components(roads) == [["X", "Y", "Z"], ["A", "B"], ["M", "N"]]
    assert connected_components([("P", "Q", 1)], depots=["C", "P"]) == [["P", "Q"], ["C"]]


def test_isolated_depots():
    assert connected_components([("A", "B", 1)], depots=["Q", "A"]) == [["A", "B"], ["Q"]]
    assert connected_components([("S", "S", 0)]) == [["S"]]


def test_regression_issue_412():
    assert connected_components([("S", "S", 0)]) == []
