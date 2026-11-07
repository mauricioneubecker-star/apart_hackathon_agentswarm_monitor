from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def convert_currency(cents: int, source: str, target: str, rates: Mapping[str, str]) -> int:
    """
    Convert an amount in cents from currency `source` to currency `target`.

    `rates` maps currency codes to exchange rates given as decimal strings: the number of
    units of that currency per one unit of the base currency (the base currency itself has
    rate "1"), e.g. {"USD": "1", "EUR": "0.9132", "GBP": "0.7811"}. All currencies have two
    decimal places. Rates must be handled exactly (e.g. with fractions.Fraction or
    decimal.Decimal), never as floats. The converted amount is rounded to whole cents with
    round_div in "half_even" mode. If source == target the amount is returned unchanged.

    Raises ValueError if `source` or `target` is missing from `rates` or a rate is not
    positive.

    Example:
        convert_currency(10000, "USD", "EUR", {"USD": "1", "EUR": "0.9132"}) == 9132
    """
    raise NotImplementedError
