from textkit.split_identifier import split_identifier


def to_camel_case(name: str, upper_first: bool = False) -> str:
    words = split_identifier(name)
    if not words:
        return ""
    first = words[0].capitalize() if upper_first else words[0]
    return first + "".join(word.capitalize() for word in words[1:])
