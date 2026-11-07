import pytest

from slotplan.split_meeting import split_meeting


def test_exact_splits():
    assert split_meeting(540, 720, 90) == [(540, 630), (630, 720)]
    assert split_meeting(540, 750, 60, 15) == [(540, 600), (615, 675), (690, 750)]
    assert split_meeting(600, 645, 60) == [(600, 660)]


def test_uneven_sessions():
    assert split_meeting(540, 740, 90) == [(540, 607), (607, 674), (674, 740)]
    assert split_meeting(780, 1000, 100, 10) == [(780, 847), (857, 924), (934, 1000)]


def test_invalid_settings():
    with pytest.raises(ValueError):
        split_meeting(600, 600, 30)
    with pytest.raises(ValueError):
        split_meeting(600, 700, 0)
