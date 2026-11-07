import pytest

from routekit.parse_edge import parse_edge


def test_parse_record():
    assert parse_edge("BER-HAM:289") == ("BER", "HAM", 289)
    assert parse_edge(" A1 - B2 : 7 ") == ("A1", "B2", 7)


def test_rejects_garbage():
    with pytest.raises(ValueError):
        parse_edge("BER HAM 289")
