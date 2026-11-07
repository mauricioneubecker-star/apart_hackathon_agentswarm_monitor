import pytest

from metricore.uptime_percent import uptime_percent


def test_example_and_no_incidents():
    assert uptime_percent([(0, 36), (18, 72)], 0, 3600) == 98.0
    assert uptime_percent([], 0, 3600) == 100.0


def test_bad_window():
    with pytest.raises(ValueError):
        uptime_percent([], 10, 5)
