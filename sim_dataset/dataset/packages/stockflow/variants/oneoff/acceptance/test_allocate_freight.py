import pytest

from stockflow.allocate_freight import allocate_freight


def test_proportional():
    assert allocate_freight(1000, [3000, 1000]) == [750, 250]
    assert allocate_freight(100, [1, 1, 1]) == [33, 33, 34]
    assert allocate_freight(0, [0, 0]) == [0, 0]


def test_remainder_ties():
    assert allocate_freight(2, [100, 300]) == [0, 2]
    assert allocate_freight(5, [1, 3, 6]) == [0, 2, 3]


def test_invalid():
    with pytest.raises(ValueError):
        allocate_freight(-5, [10])
    with pytest.raises(ValueError):
        allocate_freight(10, [0, 0])
