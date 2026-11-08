"""Calls per run and variant: which messages each monitor call sees.

global_full / _informed / _notices : all rounds 1..t, one call per (t, sample)
global_window                      : rounds [t-5, t], one call per t
global_sequential                  : own notes from t-1 + round t only (built at run time, see run.py)
pairwise : units = unordered pairs {i, j} with a direct message (GNN 'direct' edge) in either direction, plus one
           'bcast:<i>' unit per sender for its posts without any direct edge (the GNN's bcast_* node features).
           Event-driven: scored at t when the unit has a message in round t; input = that unit's messages in
           [t-5, t]; no roster, no other conversations.
agent    : unit = one of the 24 agents; input = messages it sent + messages addressed to it directly in [t-5, t];
           scored at t when it sent or was addressed in round t.
"""
from __future__ import annotations

from collections import defaultdict

from . import prompts as P
from .common import WINDOW, direct_targets, load_messages, n_rounds, population
from .render import render_rounds, roster


def _wrap(body: str) -> str:
    return "<transcript>\n" + body + "\n</transcript>"


def pair_units(msgs: list) -> dict:
    """unit -> list of messages (all rounds); unit keys 'pair:<a>|<b>' (sorted ids) or 'bcast:<a>'."""
    units = defaultdict(list)
    for m in msgs:
        tg = direct_targets(m)
        if not tg:
            units[f"bcast:{m['sender']}"].append(m)
        for d in tg:
            a, b = sorted((m["sender"], d))
            units[f"pair:{a}|{b}"].append(m)
    return units


def agent_units(msgs: list, pop: dict) -> dict:
    units = defaultdict(list)
    for m in msgs:
        for a in {m["sender"], *direct_targets(m)}:
            if a in pop:
                units[a].append(m)
    return units


def unit_parties(unit: str) -> list:
    if unit.startswith("pair:"):
        return unit[5:].split("|")
    if unit.startswith("bcast:"):
        return [unit[6:]]
    return [unit]


def build_calls(run_dir: str, variant: str, k: int = 1, datamark: bool = False) -> list:
    """Returns call dicts {t, unit, sample, blocks, cache_blocks, parties} in schedule order (t, then unit, sample)."""
    R = n_rounds(run_dir)
    pop = population(run_dir)
    msgs = load_messages(run_dir, include_notices=(variant == "global_full_notices"))
    vis_by_t = defaultdict(set)
    for m in msgs:
        vis_by_t[m["round"]].add(m["id"])
    cum, seen = {}, set()
    for t in range(1, R + 1):
        seen |= vis_by_t.get(t, set())
        cum[t] = frozenset(seen)
    q = P.QUESTION[P.kind(variant)]
    calls = []
    if variant in ("global_full", "global_full_informed", "global_full_notices", "global_window"):
        lo_of = (lambda t: 1) if variant != "global_window" else (lambda t: max(1, t - WINDOW))
        for t in range(1, R + 1):
            body = render_rounds(msgs, t, lo_of(t), pop, visible_ids=cum[t], datamark=datamark)
            blocks = [roster(pop) + "\n\n" + _wrap(body), q]
            ids = [m["id"] for m in msgs if lo_of(t) <= m["round"] <= t]
            for s in range(k):
                calls.append({"t": t, "unit": "global", "sample": s, "blocks": blocks, "ids": ids,
                              "cache_blocks": (0,) if k > 1 else (), "parties": []})
    elif variant == "global_sequential":
        for t in range(1, R + 1):
            body = render_rounds(msgs, t, t, pop, visible_ids=cum[t], datamark=datamark)
            calls.append({"t": t, "unit": "global", "sample": 0, "round_block": _wrap(body), "roster": roster(pop),
                          "blocks": None, "cache_blocks": (), "parties": [],
                          "ids": [m["id"] for m in msgs if m["round"] == t]})
    elif variant in ("pairwise", "agent"):
        units = pair_units(msgs) if variant == "pairwise" else agent_units(msgs, pop)
        for t in range(1, R + 1):
            for u in sorted(units):
                lst = units[u]
                if not any(m["round"] == t for m in lst):
                    continue
                win = [m for m in lst if t - WINDOW <= m["round"] <= t]
                body = render_rounds(win, t, max(1, t - WINDOW), pop, visible_ids=cum[t], datamark=datamark)
                parties = unit_parties(u)
                names = [pop.get(p, p) for p in parties]
                if variant == "pairwise":
                    head = (f"Conversation between {names[0]} and {names[1]}." if len(names) == 2 else
                            f"Channel posts by {names[0]} that address nobody directly.")
                else:
                    head = f"Agent: {names[0]}."
                calls.append({"t": t, "unit": u, "sample": 0, "blocks": [head + "\n\n" + _wrap(body), q],
                              "cache_blocks": (), "parties": parties, "ids": [m["id"] for m in win]})
    else:
        raise ValueError(variant)
    return calls


def seq_blocks(call: dict, notes: str) -> list:
    nb = "<notes>\n" + (notes.strip() or "(no notes yet: this is the first round you see)") + "\n</notes>"
    return [call["roster"] + "\n\n" + nb + "\n\n" + call["round_block"], P.QUESTION["global"]]
