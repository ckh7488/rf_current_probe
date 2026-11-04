"""Connector mating check for the declared bench plan, not electrical certification."""
def verify_route(route):
    """Each node is [component ID, upstream connector, downstream connector].

    Endpoints use None for the unused side; interface strings: SMA-M, SMA-F,
    BNC-M, BNC-F. Standard polarity only. Impedance and calibration are separate.
    """
    if len(route) < 2:
        raise ValueError("At least two route nodes required")
    joins = []
    allowed = {"SMA-M", "SMA-F", "BNC-M", "BNC-F"}
    for left, right in zip(route, route[1:]):
        out, into = left[2], right[1]
        if out not in allowed or into not in allowed:
            raise ValueError("Unknown/RP interface; verify actual connectors")
        if out[:-1] != into[:-1] or out[-1] == into[-1]:
            raise ValueError(f"Cannot mate {left[0]} {out} to {right[0]} {into}")
        joins.append(f"{left[0]}:{out} <-> {right[0]}:{into}")
    return joins
