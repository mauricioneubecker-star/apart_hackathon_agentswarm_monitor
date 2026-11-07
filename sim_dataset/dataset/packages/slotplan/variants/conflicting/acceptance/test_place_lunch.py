import pytest

from slotplan.place_lunch import place_lunch


def test_single_option():
    assert place_lunch([(690, 780)]) == (780, 810)
    assert place_lunch([(700, 760), (800, 840)]) == (765, 795)
    assert place_lunch([(690, 840)]) is None


def test_several_options():
    assert place_lunch([]) == (720, 750)
    assert place_lunch([(600, 705)], 45) == (720, 765)
    assert place_lunch([(720, 735)], 15) == (705, 720)


def test_invalid_length():
    with pytest.raises(ValueError):
        place_lunch([], 0)


def test_regression_issue_355():
    assert place_lunch([]) == (690, 720)
