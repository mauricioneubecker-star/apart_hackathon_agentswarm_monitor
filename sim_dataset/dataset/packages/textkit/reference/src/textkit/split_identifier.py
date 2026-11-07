import re
from typing import List


def split_identifier(name: str) -> List[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)
    return [part.lower() for part in re.split(r"[\s_.\-]+", spaced) if part]
