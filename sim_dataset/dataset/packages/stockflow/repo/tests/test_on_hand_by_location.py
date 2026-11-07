from stockflow.on_hand_by_location import on_hand_by_location


def test_example():
    lines = ["1;RCV;ABC-123456-1;B-07-14-3;10 EA", "2;SHP;ABC-123456-1;B-07-14-3;4 EA"]
    assert on_hand_by_location(lines, {}) == {("ABC-123456-1", "B-07-14-3"): 6}


def test_comments_and_cutoff():
    lines = ["# header", "", "1;RCV;ABC-123456-1;B-07-14-3;10 EA", "5;SHP;ABC-123456-1;B-07-14-3;4 EA"]
    assert on_hand_by_location(lines, {}, as_of_day=4) == {("ABC-123456-1", "B-07-14-3"): 10}
