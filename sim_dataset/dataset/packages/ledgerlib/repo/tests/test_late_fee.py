from ledgerlib.late_fee import late_fee


def test_example():
    assert late_fee(365000, "2024-01-10", 30, "2024-02-19", 1000) == 1000


def test_paid_early():
    assert late_fee(365000, "2024-01-10", 30, "2024-02-01", 1000) == 0
