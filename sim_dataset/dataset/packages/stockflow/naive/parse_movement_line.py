from stockflow.normalize_sku import normalize_sku
from stockflow.parse_location import parse_location
from stockflow.parse_quantity import parse_quantity


def parse_movement_line(line, case_sizes):
    fields = [field.strip() for field in line.split(";")]
    if len(fields) != 5:
        raise ValueError(f"expected 5 fields, got {len(fields)}")
    day_text, mtype, sku_text, location_text, qty_text = fields
    if not day_text.isdigit():
        raise ValueError(f"bad day index: {day_text!r}")
    mtype = mtype.upper()
    if mtype not in ("RCV", "SHP", "RTN", "ADJ"):
        raise ValueError(f"unknown movement type: {mtype!r}")
    sku = normalize_sku(sku_text)
    zone, aisle, shelf, level = parse_location(location_text)
    amount = parse_quantity(qty_text, case_sizes.get(sku, 1))
    return {
        "day": int(day_text),
        "type": mtype,
        "sku": sku,
        "location": f"{zone}-{aisle:02d}-{shelf:02d}-{level}",
        "qty": -amount if mtype == "SHP" else amount,
    }
