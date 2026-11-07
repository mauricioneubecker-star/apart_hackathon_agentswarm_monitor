from ledgerlib.running_balance import running_balance


def test_example():
    txns = [("2024-03-02", -200), ("2024-03-01", 500)]
    assert running_balance(1000, txns) == [("2024-03-01", 500, 1500), ("2024-03-02", -200, 1300)]
    assert txns == [("2024-03-02", -200), ("2024-03-01", 500)]


def test_extra_fields_kept():
    assert running_balance(0, [("2024-01-01", 99, "fee")]) == [("2024-01-01", 99, "fee", 99)]
