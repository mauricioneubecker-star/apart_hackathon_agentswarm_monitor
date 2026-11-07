from textkit.extract_headings import extract_headings


def test_basic_headings():
    assert extract_headings("# Intro\ntext\n## Setup ##\n") == [(1, "Intro"), (2, "Setup")]
    assert extract_headings("no headings here") == []
