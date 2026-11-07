import pytest

from ledgerlib.prorate_subscription import prorate_subscription


def test_full_and_nothing():
    assert prorate_subscription(4900, "2024-02-01", "2024-02-29", "2024-01-20") == 4900
    assert prorate_subscription(4900, "2024-02-01", "2024-02-29", "2024-03-02") == 0


def test_bad_period():
    with pytest.raises(ValueError):
        prorate_subscription(4900, "2024-02-29", "2024-02-01", "2024-02-10")
