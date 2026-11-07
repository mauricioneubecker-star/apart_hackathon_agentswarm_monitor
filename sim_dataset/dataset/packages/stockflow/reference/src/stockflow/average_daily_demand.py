from stockflow.parse_movement_line import parse_movement_line


def average_daily_demand(lines, case_sizes, sku, start_day, end_day):
    if end_day < start_day:
        raise ValueError("end_day is before start_day")
    net = 0
    for line in lines:
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        movement = parse_movement_line(text, case_sizes)
        if movement["sku"] != sku or not start_day <= movement["day"] <= end_day:
            continue
        if movement["type"] == "SHP":
            net -= movement["qty"]
        elif movement["type"] == "RTN":
            net -= movement["qty"]
    if net <= 0:
        return 0
    days = end_day - start_day + 1
    return -(-net // days)
