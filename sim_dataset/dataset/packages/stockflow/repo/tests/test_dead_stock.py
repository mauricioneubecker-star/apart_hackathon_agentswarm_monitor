import pytest

from stockflow.dead_stock import dead_stock


def test_example():
    lines = ["1;RCV;ABC-123456-1;B-07-14-3;10 EA", "5;SHP;ABC-123456-1;B-07-14-3;2 EA"]
    assert dead_stock(lines, {}, today=40, idle_days=30) == ["ABC-123456-1"]
    assert dead_stock(lines, {}, today=20, idle_days=30) == []


def test_bad_threshold():
    with pytest.raises(ValueError):
        dead_stock([], {}, today=40, idle_days=0)
