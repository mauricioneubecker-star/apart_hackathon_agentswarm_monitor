import pytest

from ledgerlib.installment_schedule import installment_schedule


def test_example():
    assert installment_schedule(100000, 2, "2024-07-01", 14) == [("2024-07-01", 50000), ("2024-07-15", 50000)]


def test_invalid_count():
    with pytest.raises(ValueError):
        installment_schedule(1000, 0, "2024-07-01", 30)
