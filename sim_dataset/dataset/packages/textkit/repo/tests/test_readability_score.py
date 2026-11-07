from textkit.readability_score import readability_score


def test_flesch_formula():
    text = "The committee reviewed the proposal. It approved the budget for next year."
    assert readability_score(text) == 59.75


def test_no_words():
    assert readability_score("") == 0.0
