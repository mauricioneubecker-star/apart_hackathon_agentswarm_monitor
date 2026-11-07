import pytest

from stockflow.abc_classify import abc_classify


def test_example():
    assert abc_classify({"S1": 80, "S2": 15, "S3": 5}) == {"S1": "A", "S2": "B", "S3": "C"}
    assert abc_classify({}) == {}


def test_negative_value():
    with pytest.raises(ValueError):
        abc_classify({"S1": -1})
