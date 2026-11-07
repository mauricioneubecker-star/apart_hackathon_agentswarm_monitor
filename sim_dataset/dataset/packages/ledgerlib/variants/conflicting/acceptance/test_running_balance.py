from ledgerlib.running_balance import running_balance


def test_date_order():
    txns = [("2024-03-05", -300), ("2024-03-01", 1000), ("2024-03-03", -200)]
    assert running_balance(0, txns) == [
        ("2024-03-01", 1000, 1000),
        ("2024-03-03", -200, 800),
        ("2024-03-05", -300, 500),
    ]


def test_same_day_posting():
    txns = [("2024-04-01", -5000, "rent"), ("2024-04-01", 7000, "payout"), ("2024-04-01", -1000, "fees")]
    assert running_balance(100, txns) == [
        ("2024-04-01", 7000, "payout", 7100),
        ("2024-04-01", -5000, "rent", 2100),
        ("2024-04-01", -1000, "fees", 1100),
    ]


def test_edges():
    assert running_balance(250, []) == []
    assert running_balance(-50, [("2024-01-01", 50)]) == [("2024-01-01", 50, 0)]


def test_regression_issue_76():
    assert running_balance(-50, [("2024-01-01", 50)]) == [("2024-01-01", 50, -50)]
