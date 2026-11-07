import pytest

from slotplan.utilization import utilization


def test_basic_share():
    assert utilization([(540, 660)], 540, 1020) == 25
    assert utilization([(600, 700), (650, 720)], 540, 1020) == 25
    assert utilization([(400, 600), (1000, 1200)], 540, 1020) == 17


def test_rounding():
    assert utilization([(540, 600)], 540, 1020) == 13
    assert utilization([(540, 840)], 540, 1020) == 63


def test_invalid_window():
    with pytest.raises(ValueError):
        utilization([(540, 600)], 600, 600)
