import pytest

from ledgerlib.prorate_subscription import prorate_subscription


def test_boundaries():
    assert prorate_subscription(4900, "2024-02-01", "2024-02-29", "2024-02-01") == 4900
    assert prorate_subscription(4900, "2024-02-01", "2024-02-29", "2024-03-01") == 0


def test_partial_periods():
    assert prorate_subscription(3000, "2024-04-01", "2024-04-30", "2024-04-16") == 1500
    assert prorate_subscription(9900, "2024-03-01", "2024-03-31", "2024-03-31") == 319
    assert prorate_subscription(1000, "2024-02-01", "2024-02-29", "2024-02-15") == 517


def test_malformed_date():
    with pytest.raises(ValueError):
        prorate_subscription(1000, "2024-02-01", "2024-02-30", "2024-02-15")
