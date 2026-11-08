"""Render monitor inputs with strict GNN parity.

Rules (README.md, "Parity"):
- only messages that pass the features.py filter (common.gnn_visible) and have round <= t;
- rounds only as relative labels <round rel="-k">, the current one <round rel="0" current="true">; no absolute
  round numbers, no sprint length, no deadline from the config (deadlines inside message texts stay);
- messages get local numbers n=1.. in chronological order (the global message ids are a monotone counter, i.e. a
  clock, and they would reveal hidden notice/review_request messages by their gaps);
- sender = handle; externals as from="ext:<handle>" external="true"; DM recipients, channel, mentions and reply
  targets as handles / local numbers. A reply to a message that is not shown but visible to the GNN earlier is
  reply_to="earlier"; a reply to a hidden kind (notice, review_request) shows no reply attribute at all;
- texts are escaped and wrapped in <msg> tags; optional datamarking (--datamark) joins words with '^' like the jury.
Never rendered: events, rounds.jsonl, llm_calls, thoughts, labels, scenario/config, model identity, roles,
instructed flags, ticket solvability.
"""
from __future__ import annotations

import html
from collections import defaultdict

from .common import handle_of


def _text(t: str, datamark: bool) -> str:
    t = str(t).strip()
    if datamark:
        t = "^".join(t.split())
    return html.escape(t, quote=False)


def _attr(v: str) -> str:
    return html.escape(str(v), quote=True)


def roster(pop: dict) -> str:
    return "Team roster (24 agents): " + ", ".join(sorted(pop.values()))


def render_rounds(msgs: list, t: int, lo: int, pop: dict, visible_ids: set | None = None,
                  datamark: bool = False, show_empty: bool = True) -> str:
    """msgs: already-selected messages (any order); rendered rounds lo..t relative to t.
    visible_ids: ids of all messages the GNN could see by t (to mark replies to unshown earlier messages)."""
    msgs = sorted((m for m in msgs if lo <= m["round"] <= t), key=lambda m: (m["round"], _num(m["id"])))
    local = {m["id"]: i + 1 for i, m in enumerate(msgs)}
    by_round = defaultdict(list)
    for m in msgs:
        by_round[m["round"]].append(m)
    out = []
    for r in range(max(1, lo), t + 1):
        rel = r - t
        head = f'<round rel="{rel}"' + (' current="true"' if rel == 0 else "")
        if not by_round.get(r):
            if show_empty or rel == 0:
                out.append(head + "></round>")
            continue
        out.append(head + ">")
        for m in by_round[r]:
            out.append(render_msg(m, local, pop, visible_ids, datamark))
        out.append("</round>")
    return "\n".join(out)


def render_msg(m: dict, local: dict, pop: dict, visible_ids: set | None, datamark: bool) -> str:
    a = [f'n="{local[m["id"]]}"']
    snd = m["sender"]
    if snd in pop:
        a.append(f'from="{_attr(pop[snd])}"')
    else:
        name = m.get("sender_handle") or str(snd).replace("ext:", "")
        a.append(f'from="ext:{_attr(name)}" external="true"')
    if m.get("kind") == "notice":
        a.append('kind="notice"')
    elif m.get("kind") == "review":
        a.append('kind="review"')
    if m["channel"] == "dm":
        to = [handle_of(pop, x) for x in m.get("recipients", []) if x != snd]
        a.append('type="dm"')
        if to:
            a.append(f'to="{_attr(",".join(to))}"')
    else:
        a.append(f'type="post" channel="{_attr(m["channel"])}"')
    men = [handle_of(pop, x) for x in m.get("mentions", []) or [] if x != snd]
    if men:
        a.append(f'mentions="{_attr(",".join(men))}"')
    rt = m.get("reply_to")
    if rt:
        if rt in local:
            a.append(f'reply_to="{local[rt]}"')
        elif visible_ids is not None and rt in visible_ids:
            a.append('reply_to="earlier"')
    return f'<msg {" ".join(a)}>{_text(m["text"], datamark)}</msg>'


def _num(mid: str) -> int:
    try:
        return int(str(mid).lstrip("m"))
    except ValueError:
        return 0
