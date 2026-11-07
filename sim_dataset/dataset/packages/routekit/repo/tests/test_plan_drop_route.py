from routekit.plan_drop_route import plan_drop_route

NET = {"S": {"A": 1, "B": 5}, "A": {"S": 1, "B": 1}, "B": {"S": 5, "A": 1, "T": 1}, "T": {"B": 1}}


def test_plan():
    assert plan_drop_route(NET, "S", "T", ["B", "A"]) == (3, ["S", "A", "B", "T"])
    assert plan_drop_route(NET, "S", "T", []) == (3, ["S", "A", "B", "T"])
