from textkit.extract_headings import extract_headings


def test_heading_syntax():
    doc = "#hashtag\n   ### Indented\n####### too deep\n###### Six #####\n#\n    # code\n"
    assert extract_headings(doc) == [(3, "Indented"), (6, "Six #####"), (1, "")]
    assert extract_headings("# C# tips\n") == [(1, "C# tips")]


def test_code_fences():
    doc = "# Install\n```bash\n# install deps\npip install x\n```\n## Usage\n~~~\n## not a heading\n~~~\n"
    assert extract_headings(doc) == [(1, "Install"), (2, "Usage")]
    assert extract_headings("```\n# a\n~~~\n# b\n") == []
