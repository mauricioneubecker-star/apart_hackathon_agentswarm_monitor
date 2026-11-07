from textkit.table_of_contents import table_of_contents


def test_nested_toc():
    doc = "# Guide\n## Install\n## Use\n### CLI\n"
    assert table_of_contents(doc) == "- [Guide](#guide)\n  - [Install](#install)\n  - [Use](#use)\n    - [CLI](#cli)"
    assert table_of_contents("plain text") == ""
