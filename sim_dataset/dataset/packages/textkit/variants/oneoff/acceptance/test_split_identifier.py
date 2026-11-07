from textkit.split_identifier import split_identifier


def test_basic_conventions():
    assert split_identifier("created_at") == ["created_at"]
    assert split_identifier("PostTitle") == ["post", "title"]
    assert split_identifier("api.v2.base-url") == ["api", "v2", "base", "url"]


def test_acronyms():
    assert split_identifier("parseHTTPResponse") == ["parse", "http", "response"]
    assert split_identifier("XMLParser") == ["xml", "parser"]
    assert split_identifier("getURL") == ["get", "url"]


def test_blank():
    assert split_identifier("  ") == []
