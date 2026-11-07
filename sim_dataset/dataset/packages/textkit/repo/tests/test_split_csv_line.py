from textkit.split_csv_line import split_csv_line


def test_quoted_fields():
    assert split_csv_line('a,"b,c",d') == ["a", "b,c", "d"]
    assert split_csv_line('x,"say ""hi"" now"') == ["x", 'say "hi" now']
    assert split_csv_line("") == [""]
