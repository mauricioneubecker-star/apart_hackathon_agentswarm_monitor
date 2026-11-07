import pytest

from textkit.split_csv_line import split_csv_line


def test_plain_and_empty_fields():
    assert split_csv_line("a,,c,") == ["a", "", "c", ""]
    assert split_csv_line("x;y z;w", delimiter=";") == ["x", "y z", "w"]
    assert split_csv_line(" padded , kept ") == ["padded", "kept"]


def test_quotes():
    assert split_csv_line('id, "Smith, John", "said ""ok"""') == ["id", "Smith, John", 'said "ok"']
    assert split_csv_line('"",""""') == ["", '"']


def test_errors():
    with pytest.raises(ValueError):
        split_csv_line('a,"unterminated')
    with pytest.raises(ValueError):
        split_csv_line('"a"b,c')
