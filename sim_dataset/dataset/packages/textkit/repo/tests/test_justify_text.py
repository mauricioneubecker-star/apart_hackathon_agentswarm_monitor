from textkit.justify_text import justify_text


def test_inner_lines_are_stretched():
    lines = justify_text("This is an example of text justification.", 16)
    assert lines[:2] == ["This    is    an", "example  of text"]
    assert len(lines) == 3
