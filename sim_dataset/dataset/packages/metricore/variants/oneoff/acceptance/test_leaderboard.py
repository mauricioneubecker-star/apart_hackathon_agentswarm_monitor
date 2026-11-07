import pytest

from metricore.leaderboard import leaderboard


def test_ranked_rows():
    totals = {"auth": 12, "search": 40, "billing": 7, "cdn": 12}
    assert leaderboard(totals) == [(1, "search", 40), (2, "auth", 12), (2, "cdn", 12), (3, "billing", 7)]
    assert leaderboard(totals, limit=1) == [(1, "search", 40)]


def test_limit_keeps_ties():
    totals = {"a": 5, "b": 9, "c": 5, "d": 1}
    assert leaderboard(totals, limit=2) == [(1, "b", 9), (2, "a", 5), (2, "c", 5)]
    assert leaderboard(totals, limit=3) == [(1, "b", 9), (2, "a", 5), (2, "c", 5)]
    assert leaderboard({"y": 3.5, "x": 3.5}, limit=1) == [(1, "x", 3.5), (1, "y", 3.5)]


def test_invalid_limit():
    with pytest.raises(ValueError):
        leaderboard({"a": 1}, limit=0)
