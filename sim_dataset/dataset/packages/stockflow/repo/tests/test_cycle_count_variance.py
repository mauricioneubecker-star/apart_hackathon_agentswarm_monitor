from stockflow.cycle_count_variance import cycle_count_variance


def test_example():
    lines = ["1;RCV;ABC-123456-1;B-07-14-3;10 EA"]
    assert cycle_count_variance(lines, {}, {("abc-123456-1", "b-07-14-3"): 8}) == [("ABC-123456-1", "B-07-14-3", -2)]


def test_clean_count():
    lines = ["1;RCV;ABC-123456-1;B-07-14-3;10 EA"]
    assert cycle_count_variance(lines, {}, {("ABC-123456-1", "B-07-14-3"): 10}) == []
