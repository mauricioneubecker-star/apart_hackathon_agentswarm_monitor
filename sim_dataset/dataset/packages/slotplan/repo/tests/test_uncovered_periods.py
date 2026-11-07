from slotplan.uncovered_periods import uncovered_periods


def test_uncovered_basic():
    rota = {"kim": ["Mon 08:00-12:00"], "ann": ["Mon 13:00-18:00"]}
    assert uncovered_periods(rota, 0, 480, 1080) == [(720, 780)]
    assert uncovered_periods(rota, 2, 480, 1080) == [(480, 1080)]
