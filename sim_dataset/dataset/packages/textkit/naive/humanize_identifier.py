from textkit.split_identifier import split_identifier

_ACRONYMS = frozenset({"api", "id", "url", "html", "http", "json", "sql", "uuid"})


def humanize_identifier(name: str) -> str:
    out = []
    for index, word in enumerate(split_identifier(name)):
        if word in _ACRONYMS:
            out.append(word.upper())
        elif index == 0:
            out.append(word.capitalize())
        else:
            out.append(word)
    return " ".join(out)
