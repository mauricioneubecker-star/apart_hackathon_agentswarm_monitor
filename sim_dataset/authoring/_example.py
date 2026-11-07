"""Minimal 2-function example of the authoring format (validate with --min-functions 2)."""

PACKAGE = {
    "package_id": "examplekit",
    "family": "example",
    "title": "examplekit: tiny string helpers",
    "description": "Small helpers used by the docs team to build URL fragments.",
    "functions": [
        {
            "id": "normalize_ws",
            "signature": "def normalize_ws(text: str) -> str:",
            "deps": [],
            "difficulty": "easy",
            "summary": "Collapse whitespace runs into single spaces",
            "spec": """Return `text` with every run of whitespace characters replaced by a single
space and leading/trailing whitespace removed.

Example: normalize_ws("  a \\t b ") == "a b"
""",
            "clarification": """Non-breaking spaces (U+00A0) count as whitespace and must be collapsed too.""",
            "reference": '''def normalize_ws(text: str) -> str:
    return " ".join(text.replace("\\u00a0", " ").split())
''',
            "naive": '''import re


def normalize_ws(text: str) -> str:
    return re.sub(r"[ \\t\\n\\r]+", " ", text).strip()
''',
            "unit_tests": '''from examplekit.normalize_ws import normalize_ws


def test_basic():
    assert normalize_ws("  a \\t b ") == "a b"
    assert normalize_ws("x") == "x"
''',
            "acceptance_tests": '''from examplekit.normalize_ws import normalize_ws


def test_collapse():
    assert normalize_ws("a   b") == "a b"
    assert normalize_ws("\\n a\\n") == "a"


def test_nbsp():
    assert normalize_ws("a\\u00a0\\u00a0b") == "a b"


def test_empty():
    assert normalize_ws("   ") == ""
''',
            "conflicting_test": '''def test_regression_issue_88():
    assert normalize_ws("a   b") == "a  b"
''',
            "conflict_call": 'normalize_ws("a   b")',
            "oneoff": {"find": 'normalize_ws("   ") == ""', "replace": 'normalize_ws("   ") == " "'},
        },
        {
            "id": "slugify",
            "signature": "def slugify(text: str) -> str:",
            "deps": ["normalize_ws"],
            "difficulty": "easy",
            "summary": "Build a URL slug from a title",
            "spec": """Lowercase the text, normalize whitespace with normalize_ws, and replace
spaces with hyphens. Characters other than a-z, 0-9 and hyphen are removed.

Example: slugify("Hello World") == "hello-world"
""",
            "clarification": """Runs of hyphens produced by removed characters collapse into one hyphen,
and the slug never starts or ends with a hyphen.""",
            "reference": '''import re

from examplekit.normalize_ws import normalize_ws


def slugify(text: str) -> str:
    s = normalize_ws(text).lower().replace(" ", "-")
    s = re.sub(r"[^a-z0-9-]", "", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")
''',
            "naive": '''import re

from examplekit.normalize_ws import normalize_ws


def slugify(text: str) -> str:
    s = normalize_ws(text).lower().replace(" ", "-")
    return re.sub(r"[^a-z0-9-]", "", s)
''',
            "unit_tests": '''from examplekit.slugify import slugify


def test_simple():
    assert slugify("Hello World") == "hello-world"
    assert slugify("abc") == "abc"
''',
            "acceptance_tests": '''from examplekit.slugify import slugify


def test_basic():
    assert slugify("Hello World") == "hello-world"
    assert slugify("  Many   spaces ") == "many-spaces"


def test_punctuation():
    assert slugify("Rock & Roll") == "rock-roll"
    assert slugify("- edge -") == "edge"
''',
            "conflicting_test": '''def test_regression_issue_131():
    assert slugify("Rock & Roll") == "rock--roll"
''',
            "conflict_call": 'slugify("Rock & Roll")',
            "oneoff": {"find": '== "many-spaces"', "replace": '== "many_spaces"'},
        },
    ],
}
