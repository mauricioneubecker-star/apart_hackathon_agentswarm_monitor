import pytest

from metricore.percent_shares import percent_shares


def test_largest_remainder():
    assert percent_shares({"a": 1, "b": 2}) == {"a": 34, "b": 66}
    assert percent_shares({"x": 7, "y": 7, "z": 6}) == {"x": 35, "y": 35, "z": 30}
    assert sum(percent_shares({"p": 3, "q": 3, "r": 3, "s": 2}).values()) == 100


def test_equal_remainders():
    assert percent_shares({"web": 1, "api": 1, "db": 1}) == {"web": 33, "api": 34, "db": 33}
    six = {"f": 1, "e": 1, "d": 1, "c": 1, "b": 1, "a": 1}
    assert percent_shares(six) == {"f": 16, "e": 16, "d": 17, "c": 17, "b": 17, "a": 17}


def test_rejects_bad_counts():
    with pytest.raises(ValueError):
        percent_shares({"a": 0, "b": 0})
    with pytest.raises(ValueError):
        percent_shares({"a": -1, "b": 3})
