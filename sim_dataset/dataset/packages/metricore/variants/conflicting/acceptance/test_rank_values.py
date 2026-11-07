from metricore.rank_values import rank_values


def test_distinct_values():
    assert rank_values([3.5, 9.0, 1.25]) == [2, 1, 3]
    assert rank_values([42]) == [1]


def test_ties_share_rank():
    assert rank_values([50, 80, 80, 20]) == [3, 1, 1, 4]
    assert rank_values([5, 5, 5]) == [1, 1, 1]
    assert rank_values([1, 2, 2, 2, 3]) == [5, 2, 2, 2, 1]


def test_regression_issue_120():
    assert rank_values([50, 80, 80, 20]) == [2, 1, 1, 3]
