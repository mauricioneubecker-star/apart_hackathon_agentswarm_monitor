import pytest

from routekit.depot_workload import depot_workload

NET = {
    "D1": {"X": 2, "C3": 9},
    "X": {"D1": 2, "C1": 2},
    "C1": {"X": 2, "D2": 4},
    "D2": {"C1": 4, "C2": 1},
    "C2": {"D2": 1, "D3": 6},
    "C3": {"D1": 9},
    "D3": {"C2": 6},
    "ISO": {},
}


def test_workload():
    assert depot_workload(NET, ["D1", "D2"], ["C3", "C2", "C1"]) == {"D1": ["C1", "C3"], "D2": ["C2"]}
    assert depot_workload(NET, ["D1"], ["X", "C1", "ISO"]) == {"D1": ["C1", "X"]}


def test_idle_depots():
    assert depot_workload(NET, ["D1", "D2", "D3"], ["C1", "C2"]) == {"D1": [], "D2": ["C1", "C2"], "D3": []}
    assert depot_workload(NET, ["D3"], ["ISO"]) == {"D3": []}


def test_unknown_customer():
    with pytest.raises(KeyError):
        depot_workload(NET, ["D1"], ["C9"])
