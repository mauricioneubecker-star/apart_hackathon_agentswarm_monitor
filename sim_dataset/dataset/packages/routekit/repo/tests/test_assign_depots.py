from routekit.assign_depots import assign_depots

NET = {"D1": {"C1": 3}, "C1": {"D1": 3, "D2": 5}, "D2": {"C1": 5}}


def test_assign():
    assert assign_depots(NET, ["D1", "D2"], ["C1"]) == {"C1": "D1"}
    assert assign_depots(NET, ["D2"], ["C1", "D1"]) == {"C1": "D2", "D1": "D2"}
