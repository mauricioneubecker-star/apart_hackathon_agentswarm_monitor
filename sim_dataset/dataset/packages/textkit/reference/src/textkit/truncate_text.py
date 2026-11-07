from textkit.normalize_whitespace import normalize_whitespace

_TRAILING_PUNCTUATION = ",;:.!?-"


def truncate_text(text: str, max_chars: int, ellipsis: str = "...") -> str:
    if max_chars <= len(ellipsis):
        raise ValueError("max_chars must be longer than the ellipsis")
    clean = normalize_whitespace(text)
    if len(clean) <= max_chars:
        return clean
    budget = max_chars - len(ellipsis)
    kept = ""
    for word in clean.split(" "):
        candidate = f"{kept} {word}" if kept else word
        if len(candidate) > budget:
            break
        kept = candidate
    if not kept:
        return clean[:budget] + ellipsis
    return kept.rstrip(_TRAILING_PUNCTUATION) + ellipsis
