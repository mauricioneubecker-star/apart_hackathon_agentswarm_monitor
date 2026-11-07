"""Task package: slotplan (meeting-room and shift scheduling helpers).

The 24 function definitions live in authoring/_parts/slotplan_{a,b,c}.py.
"""
import importlib.util
from pathlib import Path

_P = Path(__file__).resolve().parent / "_parts"


def _load(n):
    s = importlib.util.spec_from_file_location(f"_slotplan_{n}", _P / f"slotplan_{n}.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m.FUNCTIONS


PACKAGE = {
    "package_id": "slotplan",
    "family": "scheduling",
    "title": "slotplan: meeting-room and shift scheduling helpers",
    "description": (
        "slotplan is the small scheduling library behind the office room-booking bot and the "
        "support-desk rota sheet. Times are plain integers counted in minutes since midnight and "
        "weekdays are indices 0 (Monday) to 6 (Sunday), so there is no dependency on datetime or a "
        "time-zone database. It covers parsing and formatting clock times, interval arithmetic on "
        "busy/free calendars, room assignment and recurring meetings, and checks on weekly shift rotas."
    ),
    "functions": _load("a") + _load("b") + _load("c"),
}
