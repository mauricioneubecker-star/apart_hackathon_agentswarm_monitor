from textkit.split_identifier import split_identifier

_ACRONYMS = frozenset({"api", "id", "url", "html", "http", "json", "sql", "uuid"})


def humanize_identifier(name: str) -> str:
    words = split_identifier(name)
    if len(words) > 1 and words[-1] == "id":
        words = words[:-1]
    out = []
    for index, word in enumerate(words):
        if word in _ACRONYMS:
            out.append(word.upper())
        elif index == 0:
            out.append(word.capitalize())
        else:
            out.append(word)
    return " ".join(out)
