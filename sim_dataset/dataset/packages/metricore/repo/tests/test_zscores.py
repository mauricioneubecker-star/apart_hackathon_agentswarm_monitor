from metricore.zscores import zscores


def test_centre_and_symmetry():
    result = zscores([10, 20, 30])
    assert result[1] == 0.0
    assert result[0] == -result[2]
    assert len(zscores([4, 8, 15, 16, 23, 42])) == 6
