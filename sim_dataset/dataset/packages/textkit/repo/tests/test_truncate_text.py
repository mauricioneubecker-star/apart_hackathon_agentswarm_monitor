from textkit.truncate_text import truncate_text


def test_truncates_on_word_boundary():
    assert truncate_text("The quick brown fox jumps", 15) == "The quick..."
    assert truncate_text("Short text", 50) == "Short text"
