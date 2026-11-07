from routekit.format_route import format_route


def test_format():
    assert format_route(["BER", "HAM", "KIE"]) == "BER > HAM > KIE"
    assert format_route(["BER", "HAM"], 289) == "BER > HAM (289 km)"
