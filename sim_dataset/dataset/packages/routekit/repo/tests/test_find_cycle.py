from routekit.find_cycle import find_cycle


def test_find():
    assert find_cycle([("A", "B", 1), ("B", "C", 1), ("C", "A", 1)]) == ["A", "B", "C", "A"]
    assert find_cycle([("A", "B", 1), ("B", "C", 1)]) is None
