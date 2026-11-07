from stockflow.first_fit_decreasing import first_fit_decreasing


def split_shipment(lines, max_parcel_grams):
    if max_parcel_grams <= 0:
        raise ValueError("max_parcel_grams must be positive")
    merged = {}
    for sku, qty, unit_weight in lines:
        if qty <= 0 or unit_weight <= 0:
            raise ValueError("qty and unit weight must be positive")
        if unit_weight > max_parcel_grams:
            raise ValueError(f"{sku} is heavier than the parcel limit")
        if sku in merged and merged[sku][1] != unit_weight:
            raise ValueError(f"conflicting unit weights for {sku}")
        merged[sku] = (merged.get(sku, (0, unit_weight))[0] + qty, unit_weight)
    items = []
    for sku, (qty, unit_weight) in merged.items():
        items.extend([(sku, unit_weight)] * qty)
    parcels = []
    for packed in first_fit_decreasing(items, max_parcel_grams):
        parcel = {}
        for sku, _weight in packed:
            parcel[sku] = parcel.get(sku, 0) + 1
        parcels.append(parcel)
    return parcels
