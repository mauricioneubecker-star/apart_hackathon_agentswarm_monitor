import pytest

from routekit.dispatch_order import dispatch_order


def test_chains():
    assert dispatch_order({"B": ["A"], "C": ["B"]}) == ["A", "B", "C"]
    assert dispatch_order({}) == []
    assert dispatch_order({"Y": [], "X": [], "W": []}) == ["W", "X", "Y"]


def test_smallest_ready_job_first():
    assert dispatch_order({"B": ["Z"], "C": [], "Z": [], "A": ["C"]}) == ["C", "A", "Z", "B"]
    assert dispatch_order({"LOAD2": ["SCAN"], "SCAN": ["DOCK"], "AUDIT": []}) == ["AUDIT", "DOCK", "SCAN", "LOAD2"]


def test_circular_prerequisites():
    with pytest.raises(ValueError):
        dispatch_order({"A": ["B"], "B": ["C"], "C": ["A"]})
    with pytest.raises(ValueError):
        dispatch_order({"A": ["A"]})


def test_regression_issue_76():
    assert dispatch_order({"Y": [], "X": [], "W": []}) == ["Y", "X", "W"]
