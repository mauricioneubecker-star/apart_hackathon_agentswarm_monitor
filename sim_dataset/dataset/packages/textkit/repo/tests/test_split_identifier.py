from textkit.split_identifier import split_identifier


def test_conventions():
    assert split_identifier("userAccount_id") == ["user", "account", "id"]
    assert split_identifier("MAX_RETRY-count") == ["max", "retry", "count"]
    assert split_identifier("utf8Decoder") == ["utf8", "decoder"]


def test_no_words():
    assert split_identifier("__") == []
