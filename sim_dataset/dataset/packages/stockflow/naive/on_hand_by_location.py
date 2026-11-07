from stockflow.parse_movement_line import parse_movement_line


def on_hand_by_location(lines, case_sizes, as_of_day=None):
    totals = {}
    for line in lines:
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        movement = parse_movement_line(text, case_sizes)
        if as_of_day is not None and movement["day"] > as_of_day:
            continue
        key = (movement["sku"], movement["location"])
        totals[key] = totals.get(key, 0) + movement["qty"]
    return totals
