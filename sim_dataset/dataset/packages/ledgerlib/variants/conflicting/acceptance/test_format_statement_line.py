import pytest

from ledgerlib.format_statement_line import format_statement_line


def test_layout():
    assert format_statement_line("2024-03-01", "Pro plan - March", 4900, 123456) == (
        "2024-03-01  Pro plan - March                  49.00     1,234.56")
    assert format_statement_line("2024-03-06", "Chargeback", -10000, -2550) == (
        "2024-03-06  Chargeback                      -100.00       -25.50")
    assert len(format_statement_line("2024-03-02", "Card fee", -30, 0, width=50)) == 50


def test_long_description():
    line = format_statement_line("2024-03-05", "Refund for duplicate charge on order 99812", -4900, 0)
    assert line[12:38] == "Refund for duplicate ch..."
    assert len(line) == 64


def test_too_narrow():
    with pytest.raises(ValueError):
        format_statement_line("2024-03-05", "x", 1, 1, width=40)


def test_regression_issue_233():
    assert format_statement_line("2024-03-01", "Pro plan - March", 4900, 123456) == (
        "2024-03-01  Pro plan - March                  49.00      1234.56")
