from routekit.dispatch_order import dispatch_order


def test_order():
    assert dispatch_order({"PACK": ["PICK"], "SHIP": ["PACK", "LABEL"]}) == ["LABEL", "PICK", "PACK", "SHIP"]
    assert dispatch_order({"B": ["A"], "C": ["B"]}) == ["A", "B", "C"]
