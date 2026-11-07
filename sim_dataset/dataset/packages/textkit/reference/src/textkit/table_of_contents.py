from typing import Dict, List

from textkit.extract_headings import extract_headings
from textkit.slugify import slugify


def table_of_contents(markdown: str, max_level: int = 3) -> str:
    if not 1 <= max_level <= 6:
        raise ValueError("max_level must be between 1 and 6")
    seen: Dict[str, int] = {}
    entries = []
    for level, title in extract_headings(markdown):
        base = slugify(title)
        if not base:
            continue
        count = seen.get(base, 0)
        seen[base] = count + 1
        anchor = base if count == 0 else f"{base}-{count}"
        if level <= max_level:
            entries.append((level, title, anchor))
    if not entries:
        return ""
    top = min(level for level, _, _ in entries)
    lines: List[str] = []
    for level, title, anchor in entries:
        lines.append(f"{'  ' * (level - top)}- [{title}](#{anchor})")
    return "\n".join(lines)
