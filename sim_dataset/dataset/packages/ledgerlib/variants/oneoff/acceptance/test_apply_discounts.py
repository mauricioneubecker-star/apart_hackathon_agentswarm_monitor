import pytest

from ledgerlib.apply_discounts import apply_discounts


def test_single_discounts():
    assert apply_discounts(4999, ["12.5%"]) == 4375
    assert apply_discounts(2000, ["$25"]) == 0


def test_stacked_discounts():
    assert apply_discounts(10000, ["5.00", "10%"]) == 8500
    assert apply_discounts(10000, ["10%", "10%"]) == 8100


def test_invalid_discounts():
    with pytest.raises(ValueError):
        apply_discounts(1000, ["110%"])
    with pytest.raises(ValueError):
        apply_discounts(1000, ["ten"])
