import pytest

from metricore.percent_shares import percent_shares


def test_exact_and_rounded_shares():
    assert percent_shares({"api": 1, "web": 1, "db": 2}) == {"api": 25, "web": 25, "db": 50}
    assert percent_shares({"a": 1, "b": 2}) == {"a": 33, "b": 67}


def test_all_zero_rejected():
    with pytest.raises(ValueError):
        percent_shares({"a": 0})
