from ledgerlib.aging_bucket import aging_bucket


def test_buckets():
    assert aging_bucket(0) == "current"
    assert aging_bucket(15) == "1-30"
    assert aging_bucket(45) == "31-60"
    assert aging_bucket(200) == "90+"
