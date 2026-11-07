from ledgerlib.extract_invoice_refs import extract_invoice_refs


def test_spellings():
    assert extract_invoice_refs("ACH CREDIT INV#7731 ACME") == ["INV-007731"]
    assert extract_invoice_refs("paid inv 12, Inv-13") == ["INV-000012", "INV-000013"]


def test_not_references():
    assert extract_invoice_refs("INVOICE 55") == []
    assert extract_invoice_refs("ref INV1234567") == []


def test_repeated_mentions():
    assert extract_invoice_refs("INV-42 / inv#0042 / INV-43") == ["INV-000042", "INV-000043"]
