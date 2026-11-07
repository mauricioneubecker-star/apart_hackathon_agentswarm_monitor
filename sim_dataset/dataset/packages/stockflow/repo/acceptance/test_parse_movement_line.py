import pytest

from stockflow.parse_movement_line import parse_movement_line

SIZES = {"ABC-123456-1": 6, "KIT-200001-3": 24}


def test_parse_records():
    assert parse_movement_line("12;RCV;ABC-123456-1;B-07-14-3;5 CS", SIZES) == {
        "day": 12, "type": "RCV", "sku": "ABC-123456-1", "location": "B-07-14-3", "qty": 30}
    assert parse_movement_line(" 3 ; shp ; kit-200001-3 ; a-01-02-0 ; 7 ea ", SIZES) == {
        "day": 3, "type": "SHP", "sku": "KIT-200001-3", "location": "A-01-02-0", "qty": -7}
    assert parse_movement_line("41;RTN;ABC-123456-1;B-07-14-3;1 CS", SIZES)["qty"] == 6
    assert parse_movement_line("40;ADJ;TEE-104520-4;C-10-03-1;-2 CS", SIZES)["qty"] == -2


def test_quantity_sign_rules():
    with pytest.raises(ValueError):
        parse_movement_line("5;SHP;ABC-123456-1;B-07-14-3;-1 CS", SIZES)
    with pytest.raises(ValueError):
        parse_movement_line("5;RCV;ABC-123456-1;B-07-14-3;0 EA", SIZES)


def test_malformed_records():
    with pytest.raises(ValueError):
        parse_movement_line("5;RCV;ABC-123456-1;1 EA", SIZES)
