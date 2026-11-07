from slotplan.format_agenda import format_agenda


def test_agenda_basic():
    lines = format_agenda([("Design review", 600, 690), ("Standup", 540, 555)])
    assert lines == ["09:00-09:15  Standup (15m)", "10:00-11:30  Design review (1h 30m)"]
    assert format_agenda([]) == []
