from textkit.split_identifier import split_identifier


def to_snake_case(name: str) -> str:
    words = split_identifier(name)
    if not words:
        return ""
    prefix = name[: len(name) - len(name.lstrip("_"))]
    return prefix + "_".join(words)
