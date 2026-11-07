from textkit.humanize_identifier import humanize_identifier


def test_labels():
    assert humanize_identifier("createdAt") == "Created at"
    assert humanize_identifier("api_key") == "API key"
    assert humanize_identifier("") == ""
