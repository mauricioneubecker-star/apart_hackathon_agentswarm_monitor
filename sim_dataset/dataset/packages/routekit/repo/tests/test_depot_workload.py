from routekit.depot_workload import depot_workload

NET = {"D1": {"C1": 3, "C2": 1}, "C1": {"D1": 3}, "C2": {"D1": 1}}


def test_workload():
    assert depot_workload(NET, ["D1"], ["C2", "C1"]) == {"D1": ["C1", "C2"]}
    assert depot_workload(NET, ["D1"], ["C1"]) == {"D1": ["C1"]}
