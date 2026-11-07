from textkit.split_identifier import split_identifier


def to_snake_case(name: str) -> str:
    return "_".join(split_identifier(name))
