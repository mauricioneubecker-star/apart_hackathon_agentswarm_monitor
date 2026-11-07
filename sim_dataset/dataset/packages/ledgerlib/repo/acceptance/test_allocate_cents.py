import pytest

from ledgerlib.allocate_cents import allocate_cents


def test_largest_remainder():
    assert allocate_cents(1000, [1, 2, 3]) == [167, 333, 500]
    assert allocate_cents(10, [3, 3, 4]) == [3, 3, 4]
    assert allocate_cents(2, [1, 1, 1]) == [1, 1, 0]


def test_refund_total():
    assert allocate_cents(-100, [1, 1, 1]) == [-34, -33, -33]


def test_invalid_weights():
    with pytest.raises(ValueError):
        allocate_cents(100, [0, 0])
    with pytest.raises(ValueError):
        allocate_cents(100, [])
