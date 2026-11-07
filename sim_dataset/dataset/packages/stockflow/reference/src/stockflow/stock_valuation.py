from stockflow.normalize_sku import normalize_sku
from stockflow.weighted_average_cost import weighted_average_cost


def stock_valuation(on_hand, cost_layers):
    qty_by_sku = {}
    for raw_sku, qty in on_hand.items():
        sku = normalize_sku(raw_sku)
        qty_by_sku[sku] = qty_by_sku.get(sku, 0) + qty
    rows = []
    for sku, qty in qty_by_sku.items():
        if qty <= 0:
            continue
        unit_cost = weighted_average_cost(cost_layers[sku])
        rows.append((sku, qty, unit_cost, qty * unit_cost))
    rows.sort(key=lambda row: (-row[3], row[0]))
    return rows, sum(row[3] for row in rows)
