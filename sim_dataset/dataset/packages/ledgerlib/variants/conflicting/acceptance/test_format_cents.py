import pytest

from ledgerlib.format_cents import format_cents


def test_grouping():
    assert format_cents(0) == "0.00"
    assert format_cents(100000000) == "1,000,000.00"
    assert format_cents(-123456) == "-1,234.56"


def test_currency_symbol():
    assert format_cents(99, "€") == "€0.99"
    assert format_cents(-500, "$") == "-$5.00"


def test_rejects_non_int():
    with pytest.raises(TypeError):
        format_cents(12.5)


def test_regression_issue_57():
    assert format_cents(-123456) == "(1,234.56)"
