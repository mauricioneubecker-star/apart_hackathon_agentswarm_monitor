import pytest

from routekit.format_route import format_route


def test_plain_routes():
    assert format_route(["BER", "HAM", "KIE"]) == "BER > HAM > KIE"
    assert format_route(["BER", "HAM", "KIE"], 385) == "BER > HAM > KIE (385 km)"
    assert format_route(["MUC"], 0) == "MUC (0 km)"


def test_repeated_stops():
    assert format_route(["BER", "BER", "HAM", "HAM", "BER"], 578) == "BER > HAM > BER (578 km)"


def test_empty_route():
    with pytest.raises(ValueError):
        format_route([])
