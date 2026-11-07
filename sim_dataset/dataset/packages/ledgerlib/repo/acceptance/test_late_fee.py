import pytest

from ledgerlib.late_fee import late_fee


def test_no_fee():
    assert late_fee(120000, "2024-05-02", 30, "2024-06-03", 1800) == 0
    assert late_fee(120000, "2024-05-02", 30, "2024-06-13", 1800, grace_days=10) == 0


def test_interest():
    assert late_fee(120000, "2024-05-02", 30, "2024-06-04", 1800) == 59
    assert late_fee(120000, "2024-05-02", 30, "2024-06-15", 1800, grace_days=10) == 710


def test_negative_balance():
    with pytest.raises(ValueError):
        late_fee(-100, "2024-05-02", 30, "2024-06-15", 1800)
