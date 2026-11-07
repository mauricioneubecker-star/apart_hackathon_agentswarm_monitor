from typing import Dict, List, Sequence, Tuple

from ledgerlib.round_div import round_div


def vat_summary(lines: Sequence[Tuple[int, int]]) -> List[Tuple[int, int, int]]:
    totals: Dict[int, List[int]] = {}
    for net, rate in lines:
        if rate < 0:
            raise ValueError(f"negative VAT rate: {rate}")
        entry = totals.setdefault(rate, [0, 0])
        entry[0] += net
        entry[1] += round_div(net * rate, 10000)
    return [(rate, net, vat) for rate, (net, vat) in sorted(totals.items())]
