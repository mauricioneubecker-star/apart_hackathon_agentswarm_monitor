from slotplan.assign_rooms import assign_rooms


def test_capacity_and_reuse():
    assert assign_rooms([("standup", 540, 555, 6), ("review", 540, 600, 3)], {"Atlas": 8, "Nook": 4}) == {"standup": "Atlas", "review": "Nook"}
    assert assign_rooms([("a", 540, 600, 4), ("b", 600, 660, 4)], {"Nook": 4, "Atlas": 8}) == {"a": "Nook", "b": "Nook"}
    assert assign_rooms([("a", 540, 600, 12)], {"Nook": 4, "Atlas": 8}) == {"a": None}


def test_same_start_time():
    assert assign_rooms([("sync", 540, 600, 4), ("plan", 540, 600, 5)], {"Atlas": 5, "Borea": 8}) == {"plan": "Atlas", "sync": "Borea"}
    assert assign_rooms([("a", 600, 660, 5), ("b", 600, 630, 6), ("c", 600, 700, 9)], {"Mid": 6, "Big": 10}) == {"a": None, "b": "Mid", "c": "Big"}


def test_equal_capacity():
    assert assign_rooms([("x", 540, 600, 2), ("y", 570, 630, 2)], {"Orion": 4, "Lyra": 4}) == {"x": "Orion", "y": "Lyra"}
