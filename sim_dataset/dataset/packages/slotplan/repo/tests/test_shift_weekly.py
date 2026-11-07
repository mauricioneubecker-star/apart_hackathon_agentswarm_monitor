from slotplan.shift_weekly import shift_weekly


def test_shift_basic():
    assert shift_weekly([(0, 600, 660)], -120) == [(0, 480, 540)]
    assert shift_weekly([(0, 60, 120)], -120) == [(6, 1380, 1440)]
    assert shift_weekly([(2, 600, 660), (1, 600, 660)], 0) == [(1, 600, 660), (2, 600, 660)]
