import re
from typing import List, Tuple


def extract_headings(markdown: str) -> List[Tuple[int, str]]:
    headings: List[Tuple[int, str]] = []
    for line in markdown.splitlines():
        match = re.fullmatch(r" {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*", line)
        if match:
            title = re.sub(r"(?:^|[ \t]+)#+$", "", match.group(2) or "").strip()
            headings.append((len(match.group(1)), title))
    return headings
