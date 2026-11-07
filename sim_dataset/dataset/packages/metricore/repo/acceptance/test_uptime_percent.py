import pytest

from metricore.uptime_percent import uptime_percent


def test_overlapping_incidents():
    assert uptime_percent([(100, 400), (300, 700), (1000, 1100)], 0, 10_000) == 93.0
    assert uptime_percent([(0, 1), (0, 1)], 0, 86_400) == 99.999


def test_incidents_clipped_to_window():
    assert uptime_percent([(-600, 360)], 0, 3600) == 90.0
    assert uptime_percent([(3500, 4000), (5000, 6000)], 0, 3600) == 97.222
    assert uptime_percent([(-100, 7200)], 0, 3600) == 0.0


def test_bad_window():
    with pytest.raises(ValueError):
        uptime_percent([], 500, 500)
