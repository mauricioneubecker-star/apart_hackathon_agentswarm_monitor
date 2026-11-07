from textkit.make_acronym import make_acronym


def test_basic():
    assert make_acronym("  as soon as possible ") == "ASAP"
    assert make_acronym("frequently-asked questions!") == "FAQ"
    assert make_acronym("Web 3 initiative") == "W3I"


def test_minor_words():
    assert make_acronym("Department of Defense") == "DoD"
    assert make_acronym("The Lord of the Rings") == "TLotR"
    assert make_acronym("Bring your own device") == "BYOD"
