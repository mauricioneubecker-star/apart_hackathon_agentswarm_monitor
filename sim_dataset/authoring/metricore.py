"""Task package: metricore (metrics_statistics). Functions live in _parts/metricore_{a,b,c}.py."""
import importlib.util
from pathlib import Path

_P = Path(__file__).resolve().parent / "_parts"


def _load(n):
    s = importlib.util.spec_from_file_location(f"_metricore_{n}", _P / f"metricore_{n}.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m.FUNCTIONS


PACKAGE = {
    "package_id": "metricore",
    "family": "metrics_statistics",
    "title": "metricore: statistics helpers for service metrics and SLO reporting",
    "description": (
        "metricore is the SRE team's shared library for turning raw service telemetry into "
        "numbers people act on: percentiles and latency summaries, outlier and anomaly flags, "
        "SLO and error-budget figures, availability from incident timelines, and the ranking "
        "and percentage helpers behind the weekly reliability report. It is pure Python "
        "(stdlib only) and deterministic, and every reported figure goes through one rounding "
        "helper so dashboards and spreadsheets agree."
    ),
    "functions": _load("a") + _load("b") + _load("c"),
}
