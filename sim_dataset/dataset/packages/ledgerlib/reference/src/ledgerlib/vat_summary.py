from typing import Dict, List, Sequence, Tuple

from ledgerlib.round_div import round_div


def vat_summary(lines: Sequence[Tuple[int, int]]) -> List[Tuple[int, int, int]]:
    net_by_rate: Dict[int, int] = {}
    for net, rate in lines:
        if rate < 0:
            raise ValueError(f"negative VAT rate: {rate}")
        net_by_rate[rate] = net_by_rate.get(rate, 0) + net
    return [(rate, net, round_div(net * rate, 10000)) for rate, net in sorted(net_by_rate.items())]
