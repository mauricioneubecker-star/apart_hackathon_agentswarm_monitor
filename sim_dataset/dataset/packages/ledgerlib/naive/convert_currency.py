from fractions import Fraction
from typing import Mapping

from ledgerlib.round_div import round_div


def _round(value: Fraction) -> int:
    return round_div(value.numerator, value.denominator, "half_even")


def convert_currency(cents: int, source: str, target: str, rates: Mapping[str, str]) -> int:
    for code in (source, target):
        if code not in rates:
            raise ValueError(f"no exchange rate for {code}")
    source_rate, target_rate = Fraction(rates[source]), Fraction(rates[target])
    if source_rate <= 0 or target_rate <= 0:
        raise ValueError("exchange rates must be positive")
    if source == target:
        return cents
    base_cents = _round(cents / source_rate)
    return _round(base_cents * target_rate)
