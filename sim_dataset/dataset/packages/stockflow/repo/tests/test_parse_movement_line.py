import pytest

from stockflow.parse_movement_line import parse_movement_line


def test_example():
    assert parse_movement_line("12;SHP;abc-123456-1;b-07-14-3;2 CS", {"ABC-123456-1": 6}) == {
        "day": 12, "type": "SHP", "sku": "ABC-123456-1", "location": "B-07-14-3", "qty": -12}


def test_unknown_type():
    with pytest.raises(ValueError):
        parse_movement_line("12;XFR;ABC-123456-1;B-07-14-3;1 EA", {})
