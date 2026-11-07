import pytest

from stockflow.dead_stock import dead_stock

LINES = [
    "1;RCV;ABC-123456-1;B-07-14-3;10 EA",
    "1;RCV;KIT-200001-3;A-01-02-0;4 EA",
    "5;SHP;ABC-123456-1;B-07-14-3;2 EA",
    "10;SHP;KIT-200001-3;A-01-02-0;4 EA",
    "20;RCV;TEE-104520-4;C-10-03-1;6 EA",
    "30;RCV;MUG-300300-8;C-10-04-1;1 CS",
    "50;SHP;MUG-300300-8;C-10-04-1;1 EA",
]
SIZES = {"MUG-300300-8": 12}


def test_idle_skus():
    assert dead_stock(LINES, SIZES, today=40, idle_days=30) == ["ABC-123456-1"]
    assert dead_stock(LINES, SIZES, today=60, idle_days=30) == ["ABC-123456-1", "TEE-104520-4"]


def test_threshold_boundary():
    assert dead_stock(LINES, SIZES, today=34, idle_days=30) == []
    assert dead_stock(LINES, SIZES, today=35, idle_days=30) == ["ABC-123456-1"]


def test_iterator_input_and_errors():
    assert dead_stock(iter(LINES), SIZES, today=60, idle_days=45) == ["ABC-123456-1"]
    with pytest.raises(ValueError):
        dead_stock(LINES, SIZES, today=60, idle_days=0)


def test_regression_issue_349():
    assert dead_stock(LINES, SIZES, today=40, idle_days=30) == ["ABC-123456-1", "MUG-300300-8", "TEE-104520-4"]
