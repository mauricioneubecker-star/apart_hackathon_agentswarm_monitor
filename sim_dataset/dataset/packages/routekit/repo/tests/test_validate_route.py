from routekit.validate_route import validate_route

NET = {"A": {"B": 4}, "B": {"A": 4, "C": 6}, "C": {"B": 6}}


def test_validate():
    assert validate_route(NET, ["A", "B", "C"]) == []
    assert validate_route(NET, ["A", "C", "B"]) == ["no road A-C"]
    assert validate_route(NET, []) == ["empty route"]
