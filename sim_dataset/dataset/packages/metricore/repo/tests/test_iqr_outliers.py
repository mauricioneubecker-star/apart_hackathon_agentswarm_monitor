from metricore.iqr_outliers import iqr_outliers


def test_obvious_outliers():
    assert iqr_outliers([10, 12, 11, 13, 12, 95]) == [5]
    assert iqr_outliers([-80, 10, 12, 11, 13, 12, 95]) == [0, 6]


def test_no_outliers():
    assert iqr_outliers([1, 2, 3, 4]) == []
