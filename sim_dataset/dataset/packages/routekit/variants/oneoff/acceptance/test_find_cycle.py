from routekit.find_cycle import find_cycle


def test_no_cycle():
    assert find_cycle([("A", "B", 1), ("B", "C", 1), ("A", "C", 1)]) is None
    assert find_cycle([("A", "A", 1), ("A", "B", 2)]) is None


def test_cycles():
    assert find_cycle([("A", "B", 1), ("B", "A", 1)]) == ["A", "B", "A"]
    assert find_cycle([("A", "C", 1), ("C", "D", 1), ("D", "B", 1), ("B", "C", 1)]) == ["B", "D", "C", "B"]
    assert find_cycle([("K", "L", 1), ("L", "M", 1), ("M", "N", 1), ("N", "L", 1), ("B", "C", 1)]) == ["L", "M", "N", "L"]
