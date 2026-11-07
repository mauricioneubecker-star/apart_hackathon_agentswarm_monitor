from textkit.normalize_whitespace import normalize_whitespace


def test_basic_collapse():
    assert normalize_whitespace("one   two\tthree") == "one two three"
    assert normalize_whitespace("\n\n  padded  \n") == "padded"


def test_unicode_spaces():
    assert normalize_whitespace("a  b c") == "a b c"
    assert normalize_whitespace("   \t ") == " "


def test_pasted_text():
    assert normalize_whitespace("co​op") == "coop"
    assert normalize_whitespace("﻿Title ‍ here") == "Title here"
