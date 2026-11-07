from routekit.count_transfers import count_transfers


def test_counts():
    assert count_transfers([]) == 0
    assert count_transfers([("A", "B", "L1"), ("B", "C", "L1"), ("C", "D", "L4")]) == 1
