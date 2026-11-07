from ledgerlib.due_date import due_date


def test_net_terms():
    assert due_date("2024-01-10", 30) == "2024-02-09"
    assert due_date("2024-03-04", 0) == "2024-03-04"
    assert due_date("2024-02-15", 15) == "2024-03-01"
