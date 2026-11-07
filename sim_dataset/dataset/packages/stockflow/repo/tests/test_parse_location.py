import pytest

from stockflow.parse_location import parse_location


def test_parse():
    assert parse_location("b-07-14-3") == ("B", 7, 14, 3)


def test_malformed():
    with pytest.raises(ValueError):
        parse_location("B-7-14-3")
