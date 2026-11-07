import pytest

from routekit.parse_edge import parse_edge


def test_well_formed_records():
    assert parse_edge("BER-HAM:289") == ("BER", "HAM", 289)
    assert parse_edge("  MUC - NUE : 170 ") == ("MUC", "NUE", 170)
    assert parse_edge("D1-D2:0") == ("D1", "D2", 0)


def test_codes_are_case_insensitive():
    assert parse_edge("ber-Ham:12") == ("BER", "HAM", 12)


def test_malformed_records():
    with pytest.raises(ValueError):
        parse_edge("BER-HAM")
    with pytest.raises(ValueError):
        parse_edge("BER-:5")
    with pytest.raises(ValueError):
        parse_edge("BER-HAM:-4")
