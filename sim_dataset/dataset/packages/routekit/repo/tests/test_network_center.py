from routekit.network_center import network_center


def test_center():
    net = {"A": {"B": 1}, "B": {"A": 1, "C": 1}, "C": {"B": 1, "D": 1}, "D": {"C": 1, "E": 1}, "E": {"D": 1}}
    assert network_center(net) == "C"
    assert network_center({"A": {"B": 1}, "B": {}}) == "A"
