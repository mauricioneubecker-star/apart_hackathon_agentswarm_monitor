from textkit.make_acronym import make_acronym


def test_acronyms():
    assert make_acronym("Portable Network Graphics") == "PNG"
    assert make_acronym("self-contained underwater breathing apparatus") == "SCUBA"
    assert make_acronym("") == ""
