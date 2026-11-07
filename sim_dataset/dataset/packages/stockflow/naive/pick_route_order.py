from stockflow.parse_location import parse_location


def pick_route_order(picks):
    def route_key(pick):
        zone, aisle, shelf, level = parse_location(pick[1])
        return (zone, aisle, shelf, level)

    return sorted(picks, key=route_key)
