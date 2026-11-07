from ledgerlib.tiered_fee import tiered_fee


def test_example():
    assert tiered_fee(1500000, [(1000000, 290), (None, 250)]) == 41500


def test_single_tier_and_minimum():
    assert tiered_fee(100000, [(None, 300)]) == 3000
    assert tiered_fee(10000, [(None, 300)], min_fee_cents=500) == 500
