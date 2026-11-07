from routekit.route_summary import route_summary

NET = {"BER": {"LEI": 190}, "LEI": {"BER": 190, "DRE": 115}, "DRE": {"LEI": 115}}


def test_summary():
    assert route_summary(NET, "BER", "DRE", 150, {"LEI": 900}) == "BER > LEI > DRE (305 km) | EUR 466.50"
    assert route_summary(NET, "DRE", "LEI", 100) == "DRE > LEI (115 km) | EUR 115.00"
