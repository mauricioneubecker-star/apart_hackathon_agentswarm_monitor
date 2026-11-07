import pytest

from slotplan.format_agenda import format_agenda


def test_ordering():
    assert format_agenda([("Design review", 600, 690), ("Standup", 540, 555)]) == ["09:00-09:15  Standup (15m)", "10:00-11:30  Design review (1h 30m)"]
    assert format_agenda([("B", 540, 600), ("A", 540, 600), ("C", 540, 570)]) == ["09:00-09:30  C (30m)", "09:00-10:00  A (1h)", "09:00-10:00  B (1h)"]


def test_late_meetings():
    assert format_agenda([("Late call", 1410, 1440)]) == ["23:30-24:00  Late call (30m)"]
    assert format_agenda([("Release", 1380, 1500)]) == ["23:00-01:00+1  Release (2h)"]


def test_invalid_meeting():
    with pytest.raises(ValueError):
        format_agenda([("Broken", 600, 600)])


def test_regression_issue_936():
    assert format_agenda([("Release", 1380, 1500)]) == ["23:00-01:00  Release (2h)"]
