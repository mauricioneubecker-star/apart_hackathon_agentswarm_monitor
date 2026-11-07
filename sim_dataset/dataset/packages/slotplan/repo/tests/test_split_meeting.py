from slotplan.split_meeting import split_meeting


def test_split_basic():
    assert split_meeting(540, 720, 90) == [(540, 630), (630, 720)]
    assert split_meeting(540, 750, 60, 15) == [(540, 600), (615, 675), (690, 750)]
    assert split_meeting(600, 630, 60) == [(600, 630)]
