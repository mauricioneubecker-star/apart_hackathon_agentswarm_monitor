from metricore.leaderboard import leaderboard


def test_example_rows():
    totals = {"auth": 12, "search": 40, "billing": 7}
    assert leaderboard(totals) == [(1, "search", 40), (2, "auth", 12), (3, "billing", 7)]
    assert leaderboard(totals, limit=2) == [(1, "search", 40), (2, "auth", 12)]
    assert leaderboard({}) == []
