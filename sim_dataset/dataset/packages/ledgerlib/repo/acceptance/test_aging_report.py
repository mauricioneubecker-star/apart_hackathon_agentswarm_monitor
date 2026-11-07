from ledgerlib.aging_report import aging_report

INVOICES = [
    ("INV-000201", "2024-06-10", 30, 50000),
    ("INV-000202", "2024-05-02", 30, 120000),
    ("INV-000203", "2024-04-01", 30, 7550),
    ("INV-000204", "2024-03-01", 30, 2500),
    ("INV-000205", "2024-01-15", 14, 99900),
]


def test_buckets():
    assert aging_report(INVOICES, "2024-06-30") == [
        "current        $500.00",
        "1-30         $1,200.00",
        "31-60           $75.50",
        "61-90           $25.00",
        "90+            $999.00",
        "total        $2,799.50",
    ]


def test_invoice_issued_in_advance():
    lines = aging_report(INVOICES + [("INV-000206", "2024-07-01", 30, 30000)], "2024-06-30")
    assert lines[0] == "current        $500.00"
    assert lines[-1] == "total        $2,799.50"


def test_credit_and_empty():
    assert aging_report([("INV-000207", "2024-06-20", 0, -4500)], "2024-06-30")[1] == "1-30           -$45.00"
    assert aging_report([], "2024-06-30")[-1] == "total            $0.00"
