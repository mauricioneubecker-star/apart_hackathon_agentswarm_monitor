from textkit.normalize_whitespace import normalize_whitespace


def truncate_text(text: str, max_chars: int, ellipsis: str = "...") -> str:
    if max_chars <= len(ellipsis):
        raise ValueError("max_chars must be longer than the ellipsis")
    clean = normalize_whitespace(text)
    if len(clean) <= max_chars:
        return clean
    budget = max_chars - len(ellipsis)
    cut = clean[: budget + 1]
    if " " in cut:
        return cut[: cut.rindex(" ")] + ellipsis
    return clean[:budget] + ellipsis
