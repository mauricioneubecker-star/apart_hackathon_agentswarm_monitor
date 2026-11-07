from metricore.round_half_up import round_half_up


def test_ties_go_away_from_zero():
    assert round_half_up(0.125, 2) == 0.13
    assert round_half_up(-2.5, 0) == -3.0


def test_regular_rounding():
    assert round_half_up(1.234, 2) == 1.23
    assert round_half_up(9.87, 1) == 9.9
