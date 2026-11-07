import pytest

from stockflow.abc_classify import abc_classify


def test_thresholds():
    assert abc_classify({"S1": 80, "S2": 15, "S3": 5}) == {"S1": "A", "S2": "B", "S3": "C"}
    assert abc_classify({"X": 50, "Y": 40, "Z": 10}) == {"X": "A", "Y": "A", "Z": "B"}


def test_ties_and_zero_values():
    values = {"K2": 30, "K1": 30, "K3": 30, "K4": 10, "K0": 0}
    assert abc_classify(values) == {"K1": "A", "K2": "A", "K3": "A", "K4": "B", "K0": "C"}
    assert abc_classify({"Q": 0}) == {"Q": "C"}


def test_custom_thresholds():
    assert abc_classify({"a": 60, "b": 25, "c": 15}, a_pct=50, b_pct=80) == {"a": "A", "b": "B", "c": "C"}
    with pytest.raises(ValueError):
        abc_classify({"a": 1}, a_pct=90, b_pct=80)


def test_regression_issue_98():
    assert abc_classify({"X": 50, "Y": 40, "Z": 10}) == {"X": "A", "Y": "B", "Z": "C"}
