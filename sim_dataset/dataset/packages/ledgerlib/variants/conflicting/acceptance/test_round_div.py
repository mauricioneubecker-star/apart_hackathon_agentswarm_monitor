import pytest

from ledgerlib.round_div import round_div


def test_positive_quotients():
    assert round_div(10, 4) == 3
    assert round_div(14, 4, "half_even") == 4
    assert round_div(11, 4, "ceiling") == 3


def test_negative_quotients():
    assert round_div(-10, 4) == -3
    assert round_div(-10, 4, "half_even") == -2


def test_invalid_arguments():
    with pytest.raises(ValueError):
        round_div(1, 0)
    with pytest.raises(ValueError):
        round_div(1, 2, "bankers")


def test_regression_issue_331():
    assert round_div(10, 4) == 2
