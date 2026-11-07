import pytest

from stockflow.cycle_count_variance import cycle_count_variance

LINES = [
    "1;RCV;ABC-123456-1;B-07-14-3;2 CS",
    "1;RCV;KIT-200001-3;B-07-14-3;5 EA",
    "1;RCV;TEE-104520-4;A-02-01-1;9 EA",
    "2;RCV;MUG-300300-8;C-10-04-1;4 EA",
    "3;SHP;MUG-300300-8;C-10-04-1;6 EA",
]
SIZES = {"ABC-123456-1": 6}


def test_counted_bins():
    assert cycle_count_variance(LINES, SIZES, {("ABC-123456-1", "B-07-14-3"): 12, ("tee-104520-4", "a-02-01-1"): 7}) == [
        ("TEE-104520-4", "A-02-01-1", -2), ("KIT-200001-3", "B-07-14-3", -5)]


def test_merged_keys_and_found_stock():
    counts = {("MUG-300300-8", "C-10-04-1"): 1, ("mug-300300-8", "c-10-04-1"): 1, ("ABC-123456-1", "A-02-01-1"): 3}
    assert cycle_count_variance(LINES, SIZES, counts) == [
        ("ABC-123456-1", "A-02-01-1", 3), ("TEE-104520-4", "A-02-01-1", -9), ("MUG-300300-8", "C-10-04-1", 2)]


def test_clean_count_and_errors():
    assert cycle_count_variance(LINES, SIZES, {("TEE-104520-4", "A-02-01-1"): 9}) == []
    assert cycle_count_variance(LINES, SIZES, {}) == []
    with pytest.raises(ValueError):
        cycle_count_variance(LINES, SIZES, {("TEE-104520-4", "A-02-01-1"): -1})
