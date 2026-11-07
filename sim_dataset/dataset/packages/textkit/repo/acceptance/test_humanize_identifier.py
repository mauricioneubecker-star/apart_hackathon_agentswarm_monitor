from textkit.humanize_identifier import humanize_identifier


def test_plain_fields():
    assert humanize_identifier("publishedOn") == "Published on"
    assert humanize_identifier("SEO_TITLE") == "Seo title"
    assert humanize_identifier("canonical-url") == "Canonical URL"


def test_id_columns():
    assert humanize_identifier("author_id") == "Author"
    assert humanize_identifier("id") == "ID"
    assert humanize_identifier("id_card") == "ID card"
