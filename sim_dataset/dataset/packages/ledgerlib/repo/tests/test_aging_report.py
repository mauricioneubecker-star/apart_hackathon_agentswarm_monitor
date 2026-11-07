from ledgerlib.aging_report import aging_report


def test_example():
    assert aging_report([("INV-000001", "2024-06-03", 30, 12500)], "2024-06-10") == [
        "current        $125.00",
        "1-30             $0.00",
        "31-60            $0.00",
        "61-90            $0.00",
        "90+              $0.00",
        "total          $125.00",
    ]


def test_all_buckets_listed():
    assert len(aging_report([], "2024-06-10")) == 6
