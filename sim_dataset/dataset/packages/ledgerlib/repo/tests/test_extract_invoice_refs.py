from ledgerlib.extract_invoice_refs import extract_invoice_refs


def test_example():
    assert extract_invoice_refs("Payment inv 42 and INV-000107") == ["INV-000042", "INV-000107"]
    assert extract_invoice_refs("monthly transfer") == []
    assert extract_invoice_refs("PINV12") == []
