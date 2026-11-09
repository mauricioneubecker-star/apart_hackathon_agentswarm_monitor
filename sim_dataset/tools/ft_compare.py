#!/usr/bin/env python3
"""Small comparison of the persistence fine-tune with its base model (ANALYSIS_PLAN.md Nachtrag 4). Replaces the swarm
arm of Part C, which was dropped because the fine-tune broke the agent JSON in the canary episode.

Same probes, prompts, judge and sampling settings as tools/ft_check.py (the gate of 8 Nov), with more samples:
  persist  12 held-out pressure situations x --samples replies per model, judged HOLD / DILUTE / CAVE / RIGID / UPDATE
  update   4 situations with decisive new evidence x --samples replies per model (changing the position is right)
  format   --n-format real agent turns from runs_night (system prompt + observation, no history): valid JSON, known
           action, message length
Judge: Claude Haiku 5.5 with the ft_check.py prompt; it never sees which model wrote the message. Unparseable judge
replies are retried up to 3 times.

  .venv/bin/python tools/ft_compare.py --model qwen3.5-4b-ft --base qwen3.5-4b --samples 5 --n-format 60 \
      --out ../analysis/results/ft_compare
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(ROOT / "generator"))
sys.path.insert(0, str(ROOT / "tools"))
from ft_check import INSTR, JUDGE, PERSIST, UPDATE, format_inputs  # noqa: E402
from llm import AdaptionClient, AnthropicClient, load_secrets  # noqa: E402
from orchestrator import TOOL_NAMES, normalize_action, parse_response  # noqa: E402

LABELS = ["HOLD", "DILUTE", "CAVE", "RIGID", "UPDATE", "?"]
SEM = {"model": None, "judge": None}   # set in main: bounded parallelism (the first start flooded the endpoint)


async def model_chat(client, model, messages, **kw):
    async with SEM["model"]:
        return await client.chat(model, messages, **kw)


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 3), round(c + h, 3)]


def sign_test(diffs):
    """Exact two-sided sign test over the non-zero per-probe differences."""
    pos, neg = sum(d > 0 for d in diffs), sum(d < 0 for d in diffs)
    n = pos + neg
    if n == 0:
        return {"pos": 0, "neg": 0, "p": 1.0}
    k = min(pos, neg)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)
    return {"pos": pos, "neg": neg, "p": round(p, 4)}


def fisher(a, b, c, d):
    from scipy.stats import fisher_exact
    return round(float(fisher_exact([[a, b], [c, d]])[1]), 4)


async def gen_probes(client, model, items, k, req):
    async def one(ctx, chan):
        me = ctx.split("@", 1)[1].split(",", 1)[0]
        p = f"[ROLE/TASK] {ctx}\n[CHANNEL]\n{chan}" + INSTR.format(me="@" + me)
        r = await model_chat(client, model, [{"role": "user", "content": p}], max_tokens=400, temperature=0.7, **req)
        return {"status": r["status"], "text": (r.get("text") or "").strip()}
    jobs = [(i, s, one(c, ch)) for i, (c, ch) in enumerate(items) for s in range(k)]
    outs = await asyncio.gather(*(j[2] for j in jobs))
    return [{"probe": i, "sample": s, **o} for (i, s, _), o in zip(jobs, outs)]


async def gen_format(client, model, fmt, req):
    res = await asyncio.gather(*(model_chat(client, model, m, max_tokens=900, temperature=0.7, **req) for m in fmt))
    rows = []
    for r in res:
        obj, ok = parse_response(r.get("text") or "")
        known, words = False, []
        if ok:
            kind, name, *_ = normalize_action(obj)
            known = kind != "unknown" and (kind != "tool" or name in TOOL_NAMES)
            for m in (obj.get("messages") or []) if isinstance(obj.get("messages"), list) else []:
                if isinstance(m, dict):
                    words.append(len(str(m.get("text", "")).split()))
        rows.append({"status": r["status"], "valid_json": bool(ok), "known_action": bool(known), "msg_words": words})
    return rows


async def judge_one(judge, ctx, chan, msg):
    for attempt in range(4):
        async with SEM["judge"]:
            r = await judge.chat("claude-haiku-5-5",
                                 [{"role": "user", "content": JUDGE.format(ctx=ctx, chan=chan, msg=msg)}], max_tokens=120)
        obj, ok = parse_response(r.get("text") or "")
        lab = (obj or {}).get("label", "?") if ok else "?"
        if lab in LABELS[:-1]:
            return lab
        await asyncio.sleep(5 * (attempt + 1))
    return "?"


async def main(a):
    sec = load_secrets()
    keys = sec["adaption"]
    k = a.key if a.key is not None else (sec.get("jury_keys") or [0])[0]
    client = AdaptionClient(keys[k], k, per_minute=a.rpm)
    judge = AnthropicClient(sec["anthropic"], concurrency=6)
    req = {"reasoning_effort": "none"}
    SEM["model"], SEM["judge"] = asyncio.Semaphore(a.max_concurrency), asyncio.Semaphore(4)
    import time
    log = lambda s: print(f"{time.strftime('%H:%M:%S')} {s}", flush=True)  # noqa: E731
    log("loading format inputs")
    fmt = format_inputs(ROOT / a.runs, a.n_format)
    log(f"{len(fmt)} format inputs")
    rep = {"settings": {"model": a.model, "base": a.base, "samples": a.samples, "n_format": len(fmt),
                        "persist_probes": len(PERSIST), "update_probes": len(UPDATE), "temperature": 0.7,
                        "judge": "claude-haiku-5-5 (ft_check.py prompt, blind to the model)", "runs": a.runs}}
    for name, model in (("base", a.base), ("finetune", a.model)):
        P = await gen_probes(client, model, PERSIST, a.samples, req)
        log(f"{name}: persist done ({sum(x['status'] == 200 for x in P)}/{len(P)} ok)")
        U = await gen_probes(client, model, UPDATE, a.samples, req)
        log(f"{name}: update done ({sum(x['status'] == 200 for x in U)}/{len(U)} ok)")
        F = await gen_format(client, model, fmt, req)
        log(f"{name}: format done ({sum(r['status'] == 200 for r in F)}/{len(F)} ok)")

        async def lab(x, items):
            x["label"] = await judge_one(judge, *items[x["probe"]], x["text"]) if x["status"] == 200 else "?"
        await asyncio.gather(*(lab(x, PERSIST) for x in P), *(lab(x, UPDATE) for x in U))
        log(f"{name}: judged")
        rep[name] = {"model": model, "persist": P, "update": U, "format": F}
        print(f"{name}: persist {Counter(x['label'] for x in P)} update {Counter(x['label'] for x in U)} "
              f"valid JSON {sum(r['valid_json'] for r in F)}/{len(F)}", flush=True)

    S = {}
    for name in ("base", "finetune"):
        P, U, F = rep[name]["persist"], rep[name]["update"], rep[name]["format"]
        cp, cu = Counter(x["label"] for x in P), Counter(x["label"] for x in U)
        n = len(P)
        words = [w for r in F for w in r["msg_words"]]
        S[name] = {"persist_counts": dict(cp), "persist_n": n,
                   "hold": cp["HOLD"], "hold_share": round(cp["HOLD"] / n, 3), "hold_ci": wilson(cp["HOLD"], n),
                   "keeps_position": cp["HOLD"] + cp["RIGID"],
                   "keeps_share": round((cp["HOLD"] + cp["RIGID"]) / n, 3),
                   "gives_in": cp["CAVE"] + cp["DILUTE"], "gives_in_share": round((cp["CAVE"] + cp["DILUTE"]) / n, 3),
                   "update_counts": dict(cu), "update_n": len(U), "update": cu["UPDATE"],
                   "update_share": round(cu["UPDATE"] / len(U), 3), "update_ci": wilson(cu["UPDATE"], len(U)),
                   "format_n": len(F), "valid_json": sum(r["valid_json"] for r in F),
                   "valid_json_share": round(sum(r["valid_json"] for r in F) / len(F), 3),
                   "valid_json_ci": wilson(sum(r["valid_json"] for r in F), len(F)),
                   "known_action_share": round(sum(r["known_action"] for r in F) / len(F), 3),
                   "msg_words_mean": round(sum(words) / len(words), 1) if words else None,
                   "unjudged": cp["?"] + cu["?"]}
    per_probe = []
    for i in range(len(PERSIST)):
        h = {nm: sum(x["label"] == "HOLD" for x in rep[nm]["persist"] if x["probe"] == i) for nm in ("base", "finetune")}
        per_probe.append({"probe": i, "hold_base": h["base"], "hold_finetune": h["finetune"]})
    b, f = S["base"], S["finetune"]
    S["comparison"] = {
        "hold_sign_test_over_probes": sign_test([p["hold_finetune"] - p["hold_base"] for p in per_probe]),
        "hold_fisher": fisher(f["hold"], f["persist_n"] - f["hold"], b["hold"], b["persist_n"] - b["hold"]),
        "update_fisher": fisher(f["update"], f["update_n"] - f["update"], b["update"], b["update_n"] - b["update"]),
        "valid_json_fisher": fisher(f["valid_json"], f["format_n"] - f["valid_json"], b["valid_json"],
                                    b["format_n"] - b["valid_json"]),
        "per_probe_hold": per_probe}
    rep["summary"] = S
    Path(a.out + ".json").write_text(json.dumps(rep, indent=1))

    c = S["comparison"]
    L = ["# Persistence fine-tune vs. base model (ANALYSIS_PLAN.md Nachtrag 4)", "",
         f"Models: `{a.model}` vs. `{a.base}` (same endpoint, temperature 0.7). {len(PERSIST)} pressure probes x "
         f"{a.samples}, {len(UPDATE)} decisive-evidence probes x {a.samples}, {len(fmt)} real agent turns. Judge: Claude "
         "Haiku 5.5, blind to the model.", "",
         "| | base | fine-tune | test |", "|---|---|---|---|",
         f"| HOLD under peer pressure | {b['hold']}/{b['persist_n']} ({b['hold_share']:.0%}, CI {b['hold_ci']}) | "
         f"{f['hold']}/{f['persist_n']} ({f['hold_share']:.0%}, CI {f['hold_ci']}) | sign test over probes "
         f"{c['hold_sign_test_over_probes']['pos']}+/{c['hold_sign_test_over_probes']['neg']}-, "
         f"p = {c['hold_sign_test_over_probes']['p']}; Fisher p = {c['hold_fisher']} |",
         f"| keeps position (HOLD + RIGID) | {b['keeps_share']:.0%} | {f['keeps_share']:.0%} | |",
         f"| gives in (CAVE + DILUTE) | {b['gives_in_share']:.0%} | {f['gives_in_share']:.0%} | |",
         f"| UPDATE on decisive evidence | {b['update']}/{b['update_n']} | {f['update']}/{f['update_n']} | "
         f"Fisher p = {c['update_fisher']} |",
         f"| valid agent JSON (single turn, no history) | {b['valid_json']}/{b['format_n']} | "
         f"{f['valid_json']}/{f['format_n']} | Fisher p = {c['valid_json_fisher']} |",
         f"| known action | {b['known_action_share']:.0%} | {f['known_action_share']:.0%} | |",
         f"| message length (words) | {b['msg_words_mean']} | {f['msg_words_mean']} | |",
         f"| unjudged replies | {b['unjudged']} | {f['unjudged']} | |", "",
         "Label counts, pressure probes: base " + json.dumps(b["persist_counts"]) + ", fine-tune "
         + json.dumps(f["persist_counts"]) + "."]
    Path(a.out + ".md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="qwen3.5-4b-ft")
    ap.add_argument("--base", default="qwen3.5-4b")
    ap.add_argument("--samples", type=int, default=5)
    ap.add_argument("--n-format", type=int, default=60)
    ap.add_argument("--runs", default="runs_night")
    ap.add_argument("--key", type=int, default=None)
    ap.add_argument("--rpm", type=int, default=40)
    ap.add_argument("--max-concurrency", type=int, default=6, help="parallel calls to the model endpoint")
    ap.add_argument("--out", required=True)
    asyncio.run(main(ap.parse_args()))
