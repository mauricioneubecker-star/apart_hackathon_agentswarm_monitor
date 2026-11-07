from ledgerlib.aging_bucket import aging_bucket


def test_bucket_edges():
    assert aging_bucket(-5) == "current"
    assert aging_bucket(1) == "1-30"
    assert aging_bucket(60) == "31-60"
    assert aging_bucket(61) == "61-90"


def test_oldest_bucket():
    assert aging_bucket(90) == "61-90"
    assert aging_bucket(91) == "90+"


def test_regression_issue_261():
    assert aging_bucket(1) == "current"
