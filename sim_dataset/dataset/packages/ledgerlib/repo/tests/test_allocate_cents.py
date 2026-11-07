from ledgerlib.allocate_cents import allocate_cents


def test_examples():
    assert allocate_cents(100, [1, 1, 1]) == [34, 33, 33]
    assert allocate_cents(1000, [3, 1]) == [750, 250]
    assert allocate_cents(5, [0, 1]) == [0, 5]
