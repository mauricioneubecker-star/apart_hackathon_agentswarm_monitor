import pytest

from ledgerlib.tiered_fee import tiered_fee

TIERS = ((1000000, 290), (5000000, 250), (None, 200))


def test_bands():
    assert tiered_fee(1500000, TIERS) == 41500
    assert tiered_fee(6000000, TIERS) == 149000
    assert tiered_fee(12345, TIERS) == 358


def test_minimum_fee():
    assert tiered_fee(10000, TIERS, min_fee_cents=500) == 500
    assert tiered_fee(0, TIERS, min_fee_cents=500) == 0


def test_invalid_schedule():
    with pytest.raises(ValueError):
        tiered_fee(100, [(1000, 100), (500, 50), (None, 10)])
