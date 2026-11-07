from textkit.closest_match import closest_match


def test_suggestions():
    assert closest_match("pyhton", ["python", "pandas"]) == "python"
    assert closest_match("zzz", ["python"]) is None
    assert closest_match("anything", []) is None
