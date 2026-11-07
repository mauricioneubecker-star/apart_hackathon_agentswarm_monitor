import re
from typing import List, Optional, Tuple

_HEADING = re.compile(r" {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*")
_FENCE = re.compile(r" {0,3}(```|~~~)")
_CLOSING = re.compile(r"(?:^|[ \t]+)#+$")


def extract_headings(markdown: str) -> List[Tuple[int, str]]:
    headings: List[Tuple[int, str]] = []
    fence: Optional[str] = None
    for line in markdown.splitlines():
        fence_match = _FENCE.match(line)
        if fence_match:
            if fence is None:
                fence = fence_match.group(1)
            elif fence == fence_match.group(1):
                fence = None
            continue
        if fence is not None:
            continue
        match = _HEADING.fullmatch(line)
        if match:
            title = _CLOSING.sub("", match.group(2) or "").strip()
            headings.append((len(match.group(1)), title))
    return headings
