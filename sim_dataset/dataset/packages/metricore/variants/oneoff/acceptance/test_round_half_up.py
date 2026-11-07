import pytest

from metricore.round_half_up import round_half_up


def test_half_away_from_zero():
    assert round_half_up(0.375, 2) == 0.38
    assert round_half_up(-0.125, 2) == -0.12
    assert round_half_up(7.5, 0) == 8.0


def test_decimal_halfway_values():
    assert round_half_up(2.675, 2) == 2.68
    assert round_half_up(1.005, 2) == 1.01
    assert round_half_up(99.9949, 2) == 99.99


def test_negative_ndigits_rejected():
    with pytest.raises(ValueError):
        round_half_up(1.5, -1)
