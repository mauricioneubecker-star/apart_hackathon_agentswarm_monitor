from ledgerlib.format_cents import format_cents


def test_examples():
    assert format_cents(123456) == "1,234.56"
    assert format_cents(5, "$") == "$0.05"
    assert format_cents(-250) == "-2.50"
