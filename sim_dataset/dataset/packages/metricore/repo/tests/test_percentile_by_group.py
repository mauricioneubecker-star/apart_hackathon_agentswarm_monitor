from metricore.percentile_by_group import percentile_by_group


def test_example():
    recs = [{"ep": "a", "ms": 10}, {"ep": "a", "ms": 30}, {"ep": "b", "ms": 7}]
    assert percentile_by_group(recs, "ep", "ms", 50) == {"a": 20.0, "b": 7.0}
    assert percentile_by_group([{"ep": "a", "ms": None}], "ep", "ms", 50) == {}
