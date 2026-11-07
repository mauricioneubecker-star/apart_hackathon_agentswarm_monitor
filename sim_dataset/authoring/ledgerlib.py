"""ledgerlib task package (functions are defined in authoring/_parts/ledgerlib_{a,b,c}.py)."""
import importlib.util
from pathlib import Path

_P = Path(__file__).resolve().parent / "_parts"


def _load(n):
    s = importlib.util.spec_from_file_location(f"_ledgerlib_{n}", _P / f"ledgerlib_{n}.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m.FUNCTIONS


PACKAGE = {
    "package_id": "ledgerlib",
    "family": "accounting",
    "title": "ledgerlib: bookkeeping and billing helpers",
    "description": (
        "ledgerlib is the finance team's internal library for invoices, payments and customer "
        "statements. Every amount is kept in integer cents: the library parses and formats money "
        "strings, applies the company's rounding, VAT, discount and fee rules, and produces the "
        "receivables reports and statements used at month end."
    ),
    "functions": _load("a") + _load("b") + _load("c"),
}
