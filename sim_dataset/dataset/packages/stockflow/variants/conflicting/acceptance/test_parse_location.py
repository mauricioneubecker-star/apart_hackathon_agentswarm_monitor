import pytest

from stockflow.parse_location import parse_location


def test_parse_codes():
    assert parse_location("B-07-14-3") == ("B", 7, 14, 3)
    assert parse_location("  a-12-01-0 ") == ("A", 12, 1, 0)
    assert parse_location("R-99-99-9") == ("R", 99, 99, 9)


def test_malformed():
    with pytest.raises(ValueError):
        parse_location("B-07-14")
    with pytest.raises(ValueError):
        parse_location("BB-07-14-3")


def test_numbering_starts_at_one():
    with pytest.raises(ValueError):
        parse_location("C-00-05-1")
    with pytest.raises(ValueError):
        parse_location("C-05-00-1")


def test_regression_issue_58():
    assert parse_location("  a-12-01-0 ") == ("a", 12, 1, 0)
