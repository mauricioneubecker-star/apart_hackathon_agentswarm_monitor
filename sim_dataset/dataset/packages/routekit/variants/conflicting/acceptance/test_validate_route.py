from routekit.validate_route import validate_route

NET = {"A": {"B": 4}, "B": {"A": 4, "C": 6}, "C": {"B": 6}}


def test_valid_routes():
    assert validate_route(NET, ["A", "B", "C"]) == []
    assert validate_route(NET, ["C"], max_legs=0) == []


def test_reported_problems():
    assert validate_route(NET, []) == ["empty route"]
    assert validate_route(NET, ["A", "C", "B"]) == ["no road A-C"]
    assert validate_route(NET, ["A", "B", "C"], max_legs=1) == ["too many legs: 2 > 1"]


def test_unknown_depots():
    assert validate_route(NET, ["A", "X", "C"]) == ["unknown depot X"]
    assert validate_route(NET, ["A", "C", "Y"], max_legs=1) == ["no road A-C", "unknown depot Y", "too many legs: 2 > 1"]


def test_regression_issue_150():
    assert validate_route(NET, ["C"], max_legs=0) == ["route has no legs"]
