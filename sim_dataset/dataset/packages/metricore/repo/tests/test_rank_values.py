from metricore.rank_values import rank_values


def test_simple_ranking():
    assert rank_values([30, 10, 20]) == [1, 3, 2]
    assert rank_values([7, 7]) == [1, 1]
    assert rank_values([]) == []
