from slotplan.assign_rooms import assign_rooms


def test_assign_basic():
    meetings = [("standup", 540, 555, 6), ("review", 540, 600, 3)]
    assert assign_rooms(meetings, {"Atlas": 8, "Nook": 4}) == {"standup": "Atlas", "review": "Nook"}
    assert assign_rooms([("a", 540, 600, 12)], {"Nook": 4}) == {"a": None}
