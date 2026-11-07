from ledgerlib.reconcile_payments import reconcile_payments


def test_reference_match():
    assert reconcile_payments([("b1", "49.00", "inv 101")], {"INV-000101": 4900, "INV-000102": 900}) == {"b1": "INV-000101"}


def test_outgoing_line():
    assert reconcile_payments([("b2", "-49.00", "INV-000101")], {"INV-000101": 4900}) == {"b2": None}


def test_amount_match():
    assert reconcile_payments([("b3", "12.00", "transfer")], {"INV-000007": 1200, "INV-000008": 999}) == {"b3": "INV-000007"}
