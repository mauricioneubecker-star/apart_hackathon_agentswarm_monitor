import pytest

from ledgerlib.vat_summary import vat_summary


def test_grouping_and_order():
    lines = [(5000, 2000), (1000, 500), (2500, 2000), (300, 0)]
    assert vat_summary(lines) == [(0, 300, 0), (500, 1000, 50), (2000, 7500, 1500)]


def test_rounding():
    assert vat_summary([(1999, 2000), (1999, 2000), (1999, 2000)]) == [(2000, 5997, 1199)]
    assert vat_summary([(1234, 700)]) == [(700, 1234, 86)]


def test_credit_lines_and_errors():
    assert vat_summary([(10000, 2000), (-2502, 2000)]) == [(2000, 7498, 1500)]
    with pytest.raises(ValueError):
        vat_summary([(100, -2000)])


def test_regression_issue_377():
    assert vat_summary([(1234, 700)]) == [(700, 1234, 87)]
