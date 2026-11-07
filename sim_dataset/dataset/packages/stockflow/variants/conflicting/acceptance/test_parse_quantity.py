import pytest

from stockflow.parse_quantity import parse_quantity


def test_units():
    assert parse_quantity("5 CS", 12) == 60
    assert parse_quantity(" 7 ea ", 12) == 7
    assert parse_quantity("-2cs", 6) == -12


def test_bare_numbers():
    assert parse_quantity("12", 6) == 12
    assert parse_quantity(" -4 ", 6) == -4


def test_rejects():
    with pytest.raises(ValueError):
        parse_quantity("CS", 6)
    with pytest.raises(ValueError):
        parse_quantity("1 CS", 0)


def test_regression_issue_305():
    assert parse_quantity("12", 6) == 72
