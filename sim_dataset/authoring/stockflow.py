"""stockflow task package (functions split across authoring/_parts/stockflow_[abc].py)."""
import importlib.util
from pathlib import Path

_P = Path(__file__).resolve().parent / "_parts"


def _load(n):
    s = importlib.util.spec_from_file_location(f"_stockflow_{n}", _P / f"stockflow_{n}.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m.FUNCTIONS


PACKAGE = {
    "package_id": "stockflow",
    "family": "inventory",
    "title": "stockflow: warehouse inventory, costing and replenishment utilities",
    "description": (
        "Shared helpers used by the fulfilment, purchasing and finance teams to work with "
        "warehouse stock data: SKU and bin-location parsing, movement-record processing, "
        "on-hand and cycle-count reporting, inventory costing (FIFO, weighted average, freight "
        "allocation), replenishment planning and parcel building. Quantities are integer eaches, "
        "money is integer cents and dates are integer day indices, so every service computes "
        "the same numbers."
    ),
    "functions": _load("a") + _load("b") + _load("c"),
}
