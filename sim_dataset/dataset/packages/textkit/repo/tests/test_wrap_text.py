from textkit.wrap_text import wrap_text


def test_greedy_wrap():
    assert wrap_text("the quick brown fox jumps over the lazy dog", 10) == ["the quick", "brown fox", "jumps over", "the lazy", "dog"]
    assert wrap_text("   ", 10) == []
