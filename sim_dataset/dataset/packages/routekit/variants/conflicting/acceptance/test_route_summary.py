import pytest

from routekit.route_summary import route_summary

NET = {
    "BER": {"LEI": 190, "HAM": 289},
    "LEI": {"BER": 190, "DRE": 115},
    "DRE": {"LEI": 115},
    "HAM": {"BER": 289},
    "KIE": {},
}


def test_summaries():
    assert route_summary(NET, "BER", "DRE", 150, {"LEI": 900}) == "BER > LEI > DRE (305 km) | EUR 466.50"
    assert route_summary(NET, "HAM", "HAM", 150) == "HAM (0 km) | EUR 0.00"
    assert route_summary(NET, "BER", "KIE", 150) == "no route BER -> KIE"


def test_large_amounts():
    assert route_summary(NET, "HAM", "DRE", 250, {"BER": 1500, "LEI": 1500}) == "HAM > BER > LEI > DRE (594 km) | EUR 1,515.00"


def test_unknown_depot():
    with pytest.raises(KeyError):
        route_summary(NET, "BER", "MUC", 150)


def test_regression_issue_190():
    assert route_summary(NET, "BER", "KIE", 150) == "no route: BER -> KIE"
