from textkit.render_template import render_template


def test_render():
    assert render_template("Hi {{ user.name | title }}!", {"user": {"name": "ada"}}) == "Hi Ada!"
    assert render_template("{{count}} new", {"count": 3}) == "3 new"
    assert render_template("no placeholders", {}) == "no placeholders"
