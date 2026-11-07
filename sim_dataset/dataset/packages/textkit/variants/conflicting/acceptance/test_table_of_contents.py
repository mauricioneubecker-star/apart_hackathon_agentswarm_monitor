import pytest

from textkit.table_of_contents import table_of_contents


def test_levels_and_indent():
    doc = "## Getting Started\n### Café Setup\n#### Deep detail\n## Next Steps\n"
    expected = "- [Getting Started](#getting-started)\n  - [Café Setup](#cafe-setup)\n- [Next Steps](#next-steps)"
    assert table_of_contents(doc) == expected
    assert table_of_contents(doc, max_level=4).count("\n") == 3


def test_duplicate_anchors():
    doc = "# FAQ\n## Billing\n### FAQ\n## Shipping\n### FAQ\n"
    assert table_of_contents(doc) == ("- [FAQ](#faq)\n  - [Billing](#billing)\n    - [FAQ](#faq-1)\n"
                                      "  - [Shipping](#shipping)\n    - [FAQ](#faq-2)")
    assert table_of_contents("# Notes\n#### Notes\n## Notes\n") == "- [Notes](#notes)\n  - [Notes](#notes-2)"


def test_bad_level():
    with pytest.raises(ValueError):
        table_of_contents("# x", max_level=0)


def test_regression_issue_1140():
    assert table_of_contents("# Notes\n#### Notes\n## Notes\n") == "- [Notes](#notes)\n  - [Notes](#notes-1)"
