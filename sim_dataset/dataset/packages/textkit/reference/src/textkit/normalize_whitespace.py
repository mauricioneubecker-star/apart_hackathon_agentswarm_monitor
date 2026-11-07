_ZERO_WIDTH = "​‌‍⁠﻿"


def normalize_whitespace(text: str) -> str:
    cleaned = text.translate({ord(ch): None for ch in _ZERO_WIDTH})
    return " ".join(cleaned.split())
