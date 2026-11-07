from routekit.parse_network import parse_network


def test_parse_lines():
    text = "# north\nBER-HAM:289\n\nHAM-KIE:96"
    assert parse_network(text) == [("BER", "HAM", 289), ("HAM", "KIE", 96)]
    assert parse_network("") == []
