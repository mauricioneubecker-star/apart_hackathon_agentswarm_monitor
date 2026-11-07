from stockflow.on_hand_by_location import on_hand_by_location
from stockflow.parse_location import parse_location


def validate_transfer(lines, case_sizes, sku, from_location, to_location, qty, day):
    source = parse_location(from_location)
    target = parse_location(to_location)
    problems = []
    if qty <= 0:
        problems.append("BAD_QTY")
    if source == target:
        problems.append("SAME_LOCATION")
    if qty > 0:
        stock = on_hand_by_location(lines, case_sizes, as_of_day=day)
        zone, aisle, shelf, level = source
        key = (sku, f"{zone}-{aisle:02d}-{shelf:02d}-{level}")
        if stock.get(key, 0) < qty:
            problems.append("INSUFFICIENT_STOCK")
    return problems
