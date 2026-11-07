from ledgerlib.apply_payment import apply_payment


def test_example():
    invoices = [("INV-000010", "2024-01-05", 30, 6000), ("INV-000011", "2024-01-20", 30, 6000)]
    assert apply_payment(10000, invoices) == ({"INV-000010": 6000, "INV-000011": 4000}, 0)


def test_overpayment():
    assert apply_payment(7000, [("INV-000012", "2024-02-01", 14, 5000)]) == ({"INV-000012": 5000}, 2000)
