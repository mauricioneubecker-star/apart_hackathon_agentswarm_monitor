from routekit.min_spanning_tree import min_spanning_tree


def test_tree():
    roads = [("HAM", "BER", 289), ("BER", "LEI", 190), ("HAM", "LEI", 395)]
    assert min_spanning_tree(roads) == [("BER", "LEI", 190), ("BER", "HAM", 289)]
    assert min_spanning_tree([("A", "B", 3), ("B", "A", 1)]) == [("A", "B", 1)]
