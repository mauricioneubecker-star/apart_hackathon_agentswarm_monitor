from stockflow.on_hand_by_location import on_hand_by_location
from stockflow.parse_movement_line import parse_movement_line


def dead_stock(lines, case_sizes, today, idle_days):
    if idle_days < 1:
        raise ValueError("idle_days must be >= 1")
    records = [line for line in lines if line.strip() and not line.strip().startswith("#")]
    totals = {}
    for (sku, _location), qty in on_hand_by_location(records, case_sizes, as_of_day=today).items():
        totals[sku] = totals.get(sku, 0) + qty
    last_ship = {}
    for line in records:
        movement = parse_movement_line(line, case_sizes)
        if movement["day"] <= today and movement["type"] == "SHP":
            sku = movement["sku"]
            last_ship[sku] = max(last_ship.get(sku, movement["day"]), movement["day"])
    dead = []
    for sku, qty in totals.items():
        if qty <= 0:
            continue
        if sku not in last_ship or today - last_ship[sku] >= idle_days:
            dead.append(sku)
    return sorted(dead)
