import pytest

from routekit.parse_network import parse_network


def test_records_in_file_order():
    assert parse_network("BER-HAM:289\nHAM-BRE:125\n") == [("BER", "HAM", 289), ("HAM", "BRE", 125)]
    assert parse_network("BER-HAM:289\nBER-HAM:289") == [("BER", "HAM", 289), ("BER", "HAM", 289)]


def test_comments_and_blank_lines():
    text = "# region north\n\n   \nKIE-HAM:96\n  # ferry pending\nHAM-BRE:125"
    assert parse_network(text) == [("KIE", "HAM", 96), ("HAM", "BRE", 125)]
    assert parse_network("BER-HAM:289  # A24\nHAM-KIE:96# A7") == [("BER", "HAM", 289), ("HAM", "KIE", 96)]


def test_bad_line_reports_number():
    with pytest.raises(ValueError, match="line 3"):
        parse_network("BER-HAM:289\n\nBER-HAM\n")
