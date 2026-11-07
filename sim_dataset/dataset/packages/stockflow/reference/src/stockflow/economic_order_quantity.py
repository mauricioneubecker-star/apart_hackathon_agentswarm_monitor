import math

from stockflow.round_to_pack import round_to_pack


def economic_order_quantity(annual_demand, order_cost_cents, holding_cost_cents, pack_size=1):
    if annual_demand < 0 or order_cost_cents < 0:
        raise ValueError("demand and order cost must be >= 0")
    if holding_cost_cents <= 0:
        raise ValueError("holding cost must be > 0")
    if pack_size < 1:
        raise ValueError("pack_size must be >= 1")
    if annual_demand == 0:
        return 0
    raw = math.isqrt(2 * annual_demand * order_cost_cents // holding_cost_cents)
    qty = round_to_pack(raw, pack_size)
    if qty > annual_demand:
        qty = round_to_pack(annual_demand, pack_size)
    return qty
