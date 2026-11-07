import pytest

from metricore.count_breach_episodes import count_breach_episodes


def test_episodes_and_min_duration():
    series = [100, 350, 360, 90, 400, 80, 500, 510, 520]
    assert count_breach_episodes(series, 300) == 3
    assert count_breach_episodes(series, 300, min_duration=2) == 2
    assert count_breach_episodes(series, 300, min_duration=3) == 0
    assert count_breach_episodes([300, 300], 300) == 0


def test_missing_samples():
    assert count_breach_episodes([400, None, 420, 90], 300, min_duration=2) == 1
    assert count_breach_episodes([None, None], 300) == 0


def test_invalid_min_duration():
    with pytest.raises(ValueError):
        count_breach_episodes([1, 2], 1, min_duration=0)
