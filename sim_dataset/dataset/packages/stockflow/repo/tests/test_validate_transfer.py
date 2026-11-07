from stockflow.validate_transfer import validate_transfer


def test_example():
    lines = ["1;RCV;ABC-123456-1;B-07-14-3;10 EA"]
    assert validate_transfer(lines, {}, "ABC-123456-1", "B-07-14-3", "b-07-14-3", 0, day=2) == ["BAD_QTY", "SAME_LOCATION"]


def test_valid_transfer():
    lines = ["1;RCV;ABC-123456-1;B-07-14-3;10 EA"]
    assert validate_transfer(lines, {}, "ABC-123456-1", "B-07-14-3", "B-07-15-1", 10, day=2) == []
