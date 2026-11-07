from stockflow.allocate_freight import allocate_freight


def test_examples():
    assert allocate_freight(1000, [3000, 1000]) == [750, 250]
    assert allocate_freight(100, [1, 1, 1]) == [34, 33, 33]


def test_no_freight():
    assert allocate_freight(0, [5, 5]) == [0, 0]
