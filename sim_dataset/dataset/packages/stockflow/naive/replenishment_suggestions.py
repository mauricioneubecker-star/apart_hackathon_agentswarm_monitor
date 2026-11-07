from stockflow.economic_order_quantity import economic_order_quantity
from stockflow.reorder_point import reorder_point


def replenishment_suggestions(items):
    suggestions = []
    for item in items:
        position = item["on_hand"] + item["on_order"]
        rop = reorder_point(item["daily_demand"], item["lead_times"], item.get("review_period_days", 0))
        if position > rop:
            continue
        qty = economic_order_quantity(
            item["annual_demand"], item["order_cost_cents"], item["holding_cost_cents"], item["pack_size"])
        suggestions.append((item["sku"], qty))
    suggestions.sort()
    return suggestions
