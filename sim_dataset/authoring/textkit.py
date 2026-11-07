"""Task package: textkit (text normalization and formatting utilities).

The 24 function definitions live in authoring/_parts/textkit_{a,b,c}.py (8 each).
"""
import importlib.util
from pathlib import Path

_P = Path(__file__).resolve().parent / "_parts"


def _load(n):
    s = importlib.util.spec_from_file_location(f"_textkit_{n}", _P / f"textkit_{n}.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m.FUNCTIONS


PACKAGE = {
    "package_id": "textkit",
    "family": "text_processing",
    "title": "textkit: text normalization and formatting utilities",
    "description": (
        "textkit collects the small text helpers used across the content platform: whitespace "
        "and token normalization, identifier case conversion, slugs, previews, word wrapping and "
        "justification for plain-text newsletters, sentence splitting and readability scoring. "
        "It also provides typo-tolerant matching for search suggestions and tag pickers, a "
        "lightweight template renderer for notification emails, a CSV line splitter for bulk "
        "imports, and Markdown heading/TOC utilities. Pure standard-library Python, no I/O."
    ),
    "functions": _load("a") + _load("b") + _load("c"),
}
