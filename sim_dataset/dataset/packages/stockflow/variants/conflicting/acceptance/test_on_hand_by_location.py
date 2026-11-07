import pytest

from stockflow.on_hand_by_location import on_hand_by_location

LINES = [
    "# opening stock",
    "1;RCV;ABC-123456-1;B-07-14-3;2 CS",
    "1;RCV;KIT-200001-3;A-01-02-0;10 EA",
    "",
    "3;SHP;abc-123456-1;b-07-14-3;5 EA",
    "4;ADJ;KIT-200001-3;A-01-02-0;-10 EA",
    "5;SHP;TEE-104520-4;C-10-03-1;3 EA",
    "9;RCV;ABC-123456-1;B-07-14-4;1 CS",
]
SIZES = {"ABC-123456-1": 6}


def test_totals():
    assert on_hand_by_location(LINES, SIZES) == {
        ("ABC-123456-1", "B-07-14-3"): 7,
        ("ABC-123456-1", "B-07-14-4"): 6,
        ("TEE-104520-4", "C-10-03-1"): -3,
    }


def test_as_of_day():
    assert on_hand_by_location(LINES, SIZES, as_of_day=3) == {
        ("ABC-123456-1", "B-07-14-3"): 7,
        ("KIT-200001-3", "A-01-02-0"): 10,
    }
    assert on_hand_by_location(LINES, SIZES, as_of_day=0) == {}


def test_bad_record():
    with pytest.raises(ValueError):
        on_hand_by_location(["1;RCV;ABC-123456-1;B-07-14-3"], SIZES)


def test_regression_issue_118():
    assert on_hand_by_location(LINES, SIZES) == {
        ("ABC-123456-1", "B-07-14-3"): 7,
        ("ABC-123456-1", "B-07-14-4"): 6,
        ("KIT-200001-3", "A-01-02-0"): 0,
        ("TEE-104520-4", "C-10-03-1"): -3,
    }
