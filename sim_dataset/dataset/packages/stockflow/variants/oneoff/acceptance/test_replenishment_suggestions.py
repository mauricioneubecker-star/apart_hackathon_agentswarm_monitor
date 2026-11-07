from stockflow.replenishment_suggestions import replenishment_suggestions


def make_item(sku, on_hand, on_order=0, **overrides):
    item = {"sku": sku, "on_hand": on_hand, "on_order": on_order,
            "daily_demand": [10, 10], "lead_times": [5], "annual_demand": 3650,
            "order_cost_cents": 1000, "holding_cost_cents": 200, "pack_size": 10}
    item.update(overrides)
    return item


def test_trigger():
    items = [make_item("TEE-104520-4", 51), make_item("KIT-200001-3", 10), make_item("ABC-123456-1", 30, on_order=20)]
    assert replenishment_suggestions(items) == [("ABC-123456-1", 190), ("KIT-200001-3", 190)]
    assert replenishment_suggestions([make_item("MUG-300300-8", 60, review_period_days=2)]) == [("MUG-300300-8", 190)]


def test_large_gap_is_covered():
    item = make_item("BAG-987654-9", 0, daily_demand=[100, 100], lead_times=[10],
                     annual_demand=400, order_cost_cents=100, holding_cost_cents=100)
    assert replenishment_suggestions([item]) == [("BAG-987654-9", 1010)]
    assert replenishment_suggestions([dict(item, on_hand=970)]) == [("BAG-987654-9", 30)]


def test_nothing_to_order():
    assert replenishment_suggestions([]) == []
    assert replenishment_suggestions([make_item("TEE-104520-4", 40, on_order=11)]) == []
