from typing import Any, Sequence


def join_human(items: Sequence[Any], conjunction: str = "and") -> str:
    parts = [str(item) for item in items]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + f" {conjunction} {parts[-1]}"
