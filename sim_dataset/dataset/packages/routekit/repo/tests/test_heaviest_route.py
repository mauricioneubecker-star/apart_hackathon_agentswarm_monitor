from routekit.heaviest_route import heaviest_route

LIMITS = {"A": {"B": 40, "C": 12}, "B": {"A": 40, "C": 30}, "C": {"A": 12, "B": 30}}


def test_heaviest():
    assert heaviest_route(LIMITS, "A", "C") == (30, ["A", "B", "C"])
    assert heaviest_route(LIMITS, "C", "A") == (30, ["C", "B", "A"])
