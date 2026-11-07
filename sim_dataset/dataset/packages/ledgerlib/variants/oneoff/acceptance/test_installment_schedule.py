import pytest

from ledgerlib.installment_schedule import installment_schedule


def test_amounts():
    schedule = installment_schedule(100000, 3, "2024-07-01", 30)
    assert [amount for _, amount in schedule] == [33333, 33333, 33334]
    assert installment_schedule(5000, 1, "2024-07-03", 30) == [("2024-07-03", 5000)]


def test_weekend_due_dates():
    assert installment_schedule(90000, 3, "2024-06-01", 30) == [
        ("2024-06-03", 30000),
        ("2024-07-01", 30000),
        ("2024-07-31", 30000),
    ]


def test_invalid_interval():
    with pytest.raises(ValueError):
        installment_schedule(1000, 2, "2024-07-01", 0)
