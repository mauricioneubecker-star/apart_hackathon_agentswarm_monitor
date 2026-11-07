from textkit.readability_score import readability_score


def test_scores():
    assert readability_score("We updated the table. People liked it.") == 58.25
    assert readability_score("Dr. Smith wrote the report. Readers enjoyed it.") == 86.45
    assert readability_score("Our newsletter goes out every Monday. Subscribers can pause it anytime.") == 47.43


def test_display_range():
    assert readability_score("The cat sat on the mat. It was happy.") == 100.0
    text = "Interdisciplinary institutionalization notwithstanding, epistemological considerations predominate."
    assert readability_score(text) == 0.0


def test_punctuation_only():
    assert readability_score("!!! ???") == 0.0


def test_regression_issue_871():
    assert readability_score("We updated the table. People liked it.") == 58.3
