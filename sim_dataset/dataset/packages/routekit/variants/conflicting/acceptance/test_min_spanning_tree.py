from routekit.min_spanning_tree import min_spanning_tree


def test_backbone():
    roads = [("HAM", "BER", 289), ("BER", "LEI", 190), ("HAM", "LEI", 395), ("LEI", "DRE", 115), ("BER", "DRE", 193)]
    assert min_spanning_tree(roads) == [("DRE", "LEI", 115), ("BER", "LEI", 190), ("BER", "HAM", 289)]
    assert min_spanning_tree([]) == []


def test_equal_length_roads():
    assert min_spanning_tree([("B", "C", 2), ("C", "A", 2), ("A", "B", 1)]) == [("A", "B", 1), ("A", "C", 2)]
    assert min_spanning_tree([("Y", "Z", 5), ("X", "Z", 5), ("X", "Y", 5)]) == [("X", "Y", 5), ("X", "Z", 5)]


def test_regions_and_loops():
    assert min_spanning_tree([("A", "B", 3), ("X", "Y", 1), ("Z", "Z", 0)]) == [("X", "Y", 1), ("A", "B", 3)]


def test_regression_issue_188():
    assert min_spanning_tree([("A", "B", 3), ("X", "Y", 1), ("Z", "Z", 0)]) == [("A", "B", 3), ("X", "Y", 1)]
