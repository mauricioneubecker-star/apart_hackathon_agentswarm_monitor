from metricore.count_breach_episodes import count_breach_episodes


def test_episodes():
    assert count_breach_episodes([100, 400, 450, 120, 500], 300) == 2
    assert count_breach_episodes([400, 100, 400, 400], 300, min_duration=2) == 1
    assert count_breach_episodes([], 300) == 0
