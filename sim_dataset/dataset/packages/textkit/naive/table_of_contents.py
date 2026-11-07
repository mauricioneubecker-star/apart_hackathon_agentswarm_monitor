from textkit.extract_headings import extract_headings
from textkit.slugify import slugify


def table_of_contents(markdown: str, max_level: int = 3) -> str:
    if not 1 <= max_level <= 6:
        raise ValueError("max_level must be between 1 and 6")
    entries = [(level, title, slugify(title)) for level, title in extract_headings(markdown)]
    entries = [entry for entry in entries if entry[0] <= max_level and entry[2]]
    if not entries:
        return ""
    top = min(entry[0] for entry in entries)
    return "\n".join(f"{'  ' * (level - top)}- [{title}](#{anchor})" for level, title, anchor in entries)
