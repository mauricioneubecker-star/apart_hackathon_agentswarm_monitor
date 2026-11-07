from ledgerlib.reconcile_payments import reconcile_payments

INVOICES = {"INV-000101": 4900, "INV-000102": 12000, "INV-000103": 4900, "INV-000104": 2500}


def test_reference_matches():
    assert reconcile_payments([("b1", "49.00", "ACME PAYMENT INV 103")], INVOICES) == {"b1": "INV-000103"}
    lines = [("b7", "49.00", "INV-000103"), ("b8", "49.00", "TRANSFER")]
    assert reconcile_payments(lines, INVOICES) == {"b7": "INV-000103", "b8": "INV-000101"}


def test_amount_matches():
    assert reconcile_payments([("b2", "120.00", "TRANSFER")], INVOICES) == {"b2": "INV-000102"}
    assert reconcile_payments([("b3", "49.00", "TRANSFER")], INVOICES) == {"b3": None}


def test_each_invoice_once():
    lines = [("b4", "25.00", "inv#104"), ("b5", "25.00", "INV-104 again"), ("b6", "-25.00", "refund")]
    assert reconcile_payments(lines, INVOICES) == {"b4": "INV-000104", "b5": None, "b6": None}
    assert INVOICES["INV-000104"] == 2500
