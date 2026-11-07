from ledgerlib.account_balances import account_balances


def test_example():
    assert account_balances(["2024-01-02;OPS;-10.00;a", "2024-01-03;OPS;-2.50;b"]) == {"OPS": -1250}


def test_blank_lines_skipped():
    assert account_balances(["", "2024-01-03;SALES;5.00;x", "   "]) == {"SALES": 500}
