from stockflow.normalize_sku import normalize_sku
from stockflow.on_hand_by_location import on_hand_by_location
from stockflow.parse_location import parse_location


def cycle_count_variance(lines, case_sizes, counts):
    counted = {}
    for (raw_sku, raw_location), qty in counts.items():
        if qty < 0:
            raise ValueError("counted quantity cannot be negative")
        zone, aisle, shelf, level = parse_location(raw_location)
        key = (normalize_sku(raw_sku), f"{zone}-{aisle:02d}-{shelf:02d}-{level}")
        counted[key] = counted.get(key, 0) + qty
    system = on_hand_by_location(lines, case_sizes)
    counted_locations = {location for _sku, location in counted}
    keys = set(counted) | {key for key in system if key[1] in counted_locations}
    report = []
    for sku, location in keys:
        variance = counted.get((sku, location), 0) - system.get((sku, location), 0)
        if variance != 0:
            report.append((sku, location, variance))
    report.sort(key=lambda row: (row[1], row[0]))
    return report
