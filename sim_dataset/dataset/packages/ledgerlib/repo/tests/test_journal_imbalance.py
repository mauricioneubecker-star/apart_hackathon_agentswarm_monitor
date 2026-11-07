from ledgerlib.journal_imbalance import journal_imbalance


def test_examples():
    assert journal_imbalance([("1000 Cash", "100.00", ""), ("4000 Revenue", "", "90.00")]) == 1000
    assert journal_imbalance([("1000 Cash", "100.00", ""), ("4000 Revenue", "", "100.00")]) == 0
