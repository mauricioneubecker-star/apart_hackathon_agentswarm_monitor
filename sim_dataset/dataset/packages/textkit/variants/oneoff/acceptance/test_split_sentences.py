from textkit.split_sentences import split_sentences


def test_terminators_and_quotes():
    assert split_sentences('Wait... What?! "Yes." (Fine.) Done') == ["Wait...", "What?!", '"Yes."', "(Fine.)", "Done"]
    assert split_sentences("Version 2.5 is out. 3 bugs were fixed. see notes") == ["Version 2.5 is out.", "3 bugs were fixed.", "see notes"]


def test_abbreviations_and_initials():
    assert split_sentences("See e.g. Chapter 4. It helps.") == ["See e.g. Chapter 4.", "It helps."]
    assert split_sentences("J. R. R. Tolkien wrote it. Read it.") == ["J. R. R. Tolkien wrote it.", "Read it."]
    assert split_sentences("Talk to Harry S. Truman today") == ["Talk to Harry S. Truman today"]


def test_whitespace_cleanup():
    assert split_sentences("  First line.\n\nSecond   line.  ") == ["First line.", "Second line."]
