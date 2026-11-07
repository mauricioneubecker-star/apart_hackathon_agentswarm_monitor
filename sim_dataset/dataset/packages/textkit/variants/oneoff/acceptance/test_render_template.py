import pytest

from textkit.render_template import render_template


def test_paths_and_filters():
    ctx = {"post": {"title": "  hello world  ", "author": {"handle": "Ada"}}, "n": 2}
    assert render_template("{{post.title|trim|upper}} by @{{ post.author.handle | lower }}", ctx) == "HELLO WORLD by @ada"
    assert render_template("{{ n }}/{{n}} done", ctx) == "2/{{n}} done"
    assert render_template("Total: {{ total }}", {"total": 0}) == "Total: 0"


def test_null_values():
    ctx = {"user": {"nickname": None, "name": "Grace"}}
    assert render_template("Hi {{ user.nickname }}!", ctx) == "Hi !"
    assert render_template("[{{ user.nickname | upper }}] {{ user.name }}", ctx) == "[] Grace"


def test_errors():
    with pytest.raises(KeyError):
        render_template("{{ user.email }}", {"user": {}})
    with pytest.raises(ValueError):
        render_template("{{ name | reverse }}", {"name": "x"})
