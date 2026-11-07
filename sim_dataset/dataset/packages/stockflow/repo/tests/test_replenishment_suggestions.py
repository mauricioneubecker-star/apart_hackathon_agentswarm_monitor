from stockflow.replenishment_suggestions import replenishment_suggestions


def make_item(on_hand):
    return {"sku": "ABC-123456-1", "on_hand": on_hand, "on_order": 0,
            "daily_demand": [10, 10], "lead_times": [5], "annual_demand": 3650,
            "order_cost_cents": 1000, "holding_cost_cents": 200, "pack_size": 10}


def test_example():
    assert replenishment_suggestions([make_item(50)]) == [("ABC-123456-1", 190)]


def test_enough_stock():
    assert replenishment_suggestions([make_item(51)]) == []
