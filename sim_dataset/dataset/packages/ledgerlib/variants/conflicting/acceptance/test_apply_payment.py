import pytest

from ledgerlib.apply_payment import apply_payment

OPEN = [
    ("INV-000301", "2024-05-02", 30, 80000),
    ("INV-000302", "2024-05-04", 30, 30000),
    ("INV-000300", "2024-04-15", 30, 15000),
]


def test_oldest_first():
    assert apply_payment(15000, OPEN) == ({"INV-000300": 15000}, 0)
    assert apply_payment(200000, OPEN) == ({"INV-000300": 15000, "INV-000302": 30000, "INV-000301": 80000}, 75000)


def test_same_due_date():
    assert apply_payment(65000, OPEN) == ({"INV-000300": 15000, "INV-000302": 30000, "INV-000301": 20000}, 0)


def test_settled_invoices_and_errors():
    paid_up = [("INV-000299", "2024-03-01", 30, 0), ("INV-000303", "2024-06-01", 14, 500)]
    assert apply_payment(1000, paid_up) == ({"INV-000303": 500}, 500)
    with pytest.raises(ValueError):
        apply_payment(-100, OPEN)


def test_regression_issue_703():
    assert apply_payment(15000, OPEN) == ({"INV-000301": 15000}, 0)
