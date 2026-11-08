"""Pre-report checks (README "Checks").

  python -m llm_monitor.checks leakage [--runs sim_dataset/runs_night] [--n 5]
      renders n random snapshots (fixed seed) into logs/llm_monitor/leakage_check.log and asserts: no notice /
      status-bot / review_request text, no absolute round number from the renderer, no message from after t.
  python -m llm_monitor.checks determinism --a results/x/oof/results.json --b results/y/oof/results.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re

from .common import REPO, find_runs, gnn_visible, read_jsonl, _p
from .units import build_calls

TAG = re.compile(r"<msg [^>]*>.*?</msg>", re.S)


def leakage(a):
    runs = find_runs(a.runs)
    rng = random.Random(20261108)
    log = os.path.join(REPO, "logs", "llm_monitor", "leakage_check.log")
    os.makedirs(os.path.dirname(log), exist_ok=True)
    out = []
    variants = ["global_full", "global_window", "pairwise", "agent", "global_sequential"]
    for i in range(a.n):
        d = rng.choice(runs)
        v = variants[i % len(variants)]
        calls = build_calls(d, v)
        c = rng.choice(calls)
        ms = read_jsonl(_p(d, "messages.jsonl"))
        rnd = {m["id"]: m["round"] for m in ms}
        hidden = {str(m["text"]).strip() for m in ms if not gnn_visible(m) and str(m.get("text", "")).strip()}
        hidden -= {str(m["text"]).strip() for m in ms if gnn_visible(m)}
        text = "\n".join(c["blocks"]) if c["blocks"] else c["round_block"]
        markup = TAG.sub("<msg/>", text)
        checks = {
            "no_hidden_text": not any(h in text for h in hidden if len(h) > 20),
            "no_status_bot_sender": not any('from="ext:status-bot"' in x or 'kind="notice"' in x
                                            for x in re.findall(r"<msg [^>]*>", text)),
            "no_absolute_round_in_markup": not re.search(r'round="\d|\bround \d|cycle \d', markup)
                                           and all(int(x) <= 0 for x in re.findall(r'rel="(-?\d+)"', markup)),
            "no_future_message": all(rnd[x] <= c["t"] for x in c["ids"]),
            "no_global_message_ids": not re.search(r'id="m\d+"', text),
        }
        out.append(f"=== {i + 1}: {d} | variant {v} | t={c['t']} | unit {c['unit']} | checks {checks}\n{text}\n")
        assert all(checks.values()), (d, v, c["t"], checks)
    open(log, "w").write("\n".join(out))
    print(f"leakage check passed on {a.n} snapshots -> {log}")


def determinism(a):
    h = [hashlib.sha256(open(p, "rb").read()).hexdigest() for p in (a.a, a.b)]
    same = h[0] == h[1]
    if not same:
        A, B = json.load(open(a.a)), json.load(open(a.b))
        diff = [k for k in A if A.get(k) != B.get(k)]
        print("differs in", diff)
    print("identical" if same else "NOT identical", h)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["leakage", "determinism"])
    ap.add_argument("--runs", nargs="+", default=[os.path.join(REPO, "sim_dataset", "runs_night")])
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--a")
    ap.add_argument("--b")
    a = ap.parse_args(argv)
    leakage(a) if a.what == "leakage" else determinism(a)


if __name__ == "__main__":
    main()
