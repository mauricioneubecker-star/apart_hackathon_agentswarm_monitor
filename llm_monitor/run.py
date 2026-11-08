"""Run one monitor variant over run dirs (resumable).

  python -m llm_monitor.run --variant global_full --runs sim_dataset/runs_night [--where "split=='night_test_id'"]
      [--k 3] [--concurrency 16] [--limit N] [--dev] [--dry-run] [--yes] [--datamark]

Output per run dir: monitor_<variant>.jsonl (monitor_<variant>_dm.jsonl with --datamark), one row per call:
run, t, unit, sample, prompt_version, model, parsed, ok, error, stop_reason, usage, latency, tries.
Done = a row with the current prompt_version that is ok or a (twice) refused call; everything else is re-tried.
Before calling the API the cost is estimated; above $25 the run stops unless --yes is given.
Scheduling: calls of one run in order of t; for k > 1 the first sample goes first and the others follow it (cache
hits); units of one round run concurrently; up to --concurrency runs in parallel.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time

from . import prompts as P
from .client import MAX_PROMPT_TOKENS, MODEL, PRICE, MonitorClient
from .common import HERE, find_runs, run_meta
from .units import build_calls, seq_blocks


class FakeClient:
    """Offline stand-in (pipeline tests only): scores from the task-lexicon count in the prompt, plus noise."""

    def __init__(self):
        self.stats = {"calls": 0, "errors": 0, "retries": 0, "input_tokens": 0, "output_tokens": 0, "cache_read": 0,
                      "cache_write": 0, "cost": 0.0, "refusals": 0}

    async def structured(self, system, blocks, schema, max_tokens, cache_blocks=()):
        import random
        import re
        from .common import MECH_PATTERNS
        txt = "\n".join(blocks)
        rnd = random.Random(hash(txt) % 2**32)
        hits = sum(len(p.findall(txt.lower())) for p in MECH_PATTERNS)
        names = re.findall(r'from="([a-z]+)"', txt)
        p = min(100, int(8 * hits ** 0.7 + rnd.randint(0, 15)))
        props = schema["properties"]
        out = {}
        if "p_tip_3" in props:
            out = {"analysis": "fake", "violators": names[:min(len(names), hits // 4)], "est_violators": min(24, hits // 3),
                   "at_risk": [{"agent": n, "p": p} for n in names[:3]], "risk_level": p, "p_tip_3": p,
                   "p_tip_end": min(100, p + 10)}
            if "notes" in props:
                out["notes"] = f"fake notes {hits}"
        elif "parties" in props:
            out = {"analysis": "fake", "suspicion": p, "parties": [{"agent": n, "p_violated": p, "p_will_violate_3": p}
                                                                    for n in dict.fromkeys(names)]}
        else:
            out = {"analysis": "fake", "p_violated": p, "p_will_violate_3": p, "suspicion": p}
        self.stats["calls"] += 1
        u = {"input_tokens": len(txt) // 4, "output_tokens": 50, "cache_creation_input_tokens": 0,
             "cache_read_input_tokens": 0}
        return {"parsed": out, "ok": True, "error": None, "stop_reason": "end_turn", "usage": u, "latency": 0.01,
                "tries": 1}

CALIB = os.path.join(HERE, "calibration.json")
DEFAULT_CALIB = {"chars_per_token": 3.5, "out_tokens": {"global": 350, "pair": 150, "agent": 110}, "latency_s": 5.0}
COST_GATE = 25.0


def calib() -> dict:
    c = dict(DEFAULT_CALIB)
    if os.path.exists(CALIB):
        c.update(json.load(open(CALIB)))
    return c


def suffix(a) -> str:
    return ("_dm" if a.datamark else "") + ("_fake" if a.fake else "")


def out_path(run_dir, variant, sfx=""):
    return os.path.join(run_dir, f"monitor_{variant}{sfx}.jsonl")


def done_keys(path, pv) -> dict:
    out = {}
    if os.path.exists(path):
        for line in open(path):
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("prompt_version") == pv and (r.get("ok") or str(r.get("error", "")).startswith("refusal")):
                out[(r["t"], r["unit"], r["sample"])] = r
    return out


def select_runs(a) -> list:
    import pandas as pd
    runs = find_runs(a.runs)
    if a.dev:
        dev = set(json.load(open(os.path.join(HERE, "dev_runs.json")))["runs"])
        runs = [d for d in runs if run_meta(d)["episode_id"] in dev]
    if a.where:
        M = pd.DataFrame([dict(run_meta(d), run_dir=d) for d in runs])
        runs = list(M.query(a.where).run_dir) if len(M) else []
    if a.exclude_dev:
        dev = set(json.load(open(os.path.join(HERE, "dev_runs.json")))["runs"])
        runs = [d for d in runs if run_meta(d)["episode_id"] not in dev]
    return runs[: a.limit] if a.limit else runs


# ---------------------------------------------------------------------------------------------------- estimate
def estimate(plan: dict, variant: str, k: int, concurrency: int) -> dict:
    c = calib()
    cpt = c["chars_per_token"]
    kind = P.kind(variant)
    sys_chars = len(P.system_prompt(variant)) + len(json.dumps(P.schema(variant)))
    n = tin = tread = twrite = tout = 0
    max_tok = 0
    for run_dir, calls in plan.items():
        for cl in calls:
            blocks = cl["blocks"] if cl["blocks"] is not None else seq_blocks(cl, "x" * 1000)
            tr = sum(len(b) for b in blocks[:-1]) / cpt
            q = len(blocks[-1]) / cpt
            st = sys_chars / cpt
            max_tok = max(max_tok, tr + q + st)
            n += 1
            tin += q + st                      # system counted at full price (conservative: may be below 512)
            if k > 1 and cl["unit"] == "global":
                if cl["sample"] == 0:
                    twrite += tr
                else:
                    tread += tr
            else:
                tin += tr
            tout += c["out_tokens"][kind]
    cost = (tin * PRICE["input"] + tread * PRICE["cache_read"] + twrite * PRICE["cache_write"]
            + tout * PRICE["output"]) / 1e6
    wall = n * c["latency_s"] / max(1, concurrency)
    return {"calls": n, "runs": len(plan), "input_tokens": int(tin), "cache_read_tokens": int(tread),
            "cache_write_tokens": int(twrite), "output_tokens": int(tout), "max_prompt_tokens": int(max_tok),
            "cost_usd": round(cost, 2), "wall_min": round(wall / 60, 1), "chars_per_token": cpt}


# --------------------------------------------------------------------------------------------------------- run
class Progress:
    def __init__(self, client, total, every=200):
        self.client, self.total, self.every, self.n, self.ok, self.t0 = client, total, every, 0, 0, time.time()

    def tick(self, ok):
        self.n += 1
        self.ok += bool(ok)
        if self.n % self.every == 0 or self.n == self.total:
            s = self.client.stats
            el = time.time() - self.t0
            eta = el / self.n * (self.total - self.n)
            print(f"{time.strftime('%H:%M:%S')} {self.n}/{self.total} calls  ok {self.ok / self.n:.3f}  "
                  f"refusals {s['refusals']}  errors {s['errors']}  retries {s['retries']}  "
                  f"cost ${s['cost']:.2f}  in {s['input_tokens']} out {s['output_tokens']} "
                  f"cache r/w {s['cache_read']}/{s['cache_write']}  elapsed {el / 60:.1f} min  eta {eta / 60:.1f} min",
                  flush=True)


def row_of(run_dir, variant, cl, res):
    return {"run": run_meta(run_dir)["episode_id"], "t": cl["t"], "unit": cl["unit"], "sample": cl["sample"],
            "parties": cl["parties"], "prompt_version": P.version(variant), "model": MODEL, "parsed": res["parsed"],
            "ok": res["ok"], "error": res["error"], "stop_reason": res["stop_reason"], "usage": res["usage"],
            "latency": res["latency"], "tries": res["tries"]}


async def run_one(client, run_dir, variant, calls, path, done, prog, system, schema, max_tokens):
    fh = open(path, "a")

    async def call(cl, blocks):
        res = await client.structured(system, blocks, schema, max_tokens, cl["cache_blocks"])
        row = row_of(run_dir, variant, cl, res)
        fh.write(json.dumps(row) + "\n")
        fh.flush()
        prog.tick(res["ok"])
        return row

    try:
        if variant == "global_sequential":
            notes = ""
            for cl in calls:
                key = (cl["t"], cl["unit"], cl["sample"])
                r = done.get(key) or await call(cl, seq_blocks(cl, notes))
                if r.get("ok") and isinstance(r.get("parsed"), dict):
                    notes = str(r["parsed"].get("notes", ""))[:1500]
            return
        by_t = {}
        for cl in calls:
            by_t.setdefault(cl["t"], []).append(cl)
        for t in sorted(by_t):
            todo = [cl for cl in by_t[t] if (cl["t"], cl["unit"], cl["sample"]) not in done]
            first = [cl for cl in todo if cl["sample"] == 0 and cl["cache_blocks"]]
            if first:                                   # k > 1: sample 0 writes the cache, the rest read it
                await asyncio.gather(*(call(cl, cl["blocks"]) for cl in first))
                todo = [cl for cl in todo if cl not in first]
            await asyncio.gather(*(call(cl, cl["blocks"]) for cl in todo))
    finally:
        fh.close()


async def run_all(a, plan, variant):
    client = FakeClient() if a.fake else MonitorClient(concurrency=a.concurrency)
    system, schema = P.system_prompt(variant), P.schema(variant)
    max_tokens = P.MAX_TOKENS[P.kind(variant)]
    pv = P.version(variant)
    jobs, total = [], 0
    for run_dir, calls in plan.items():
        path = out_path(run_dir, variant, suffix(a))
        done = done_keys(path, pv)
        n_todo = sum(1 for cl in calls if (cl["t"], cl["unit"], cl["sample"]) not in done)
        if n_todo:
            jobs.append((run_dir, calls, path, done))
            total += n_todo
    print(f"{variant}: {total} calls to do in {len(jobs)} runs (prompt {pv})", flush=True)
    if not total:
        return client
    prog = Progress(client, total)
    sem = asyncio.Semaphore(max(1, a.run_parallel or a.concurrency))

    async def guarded(j):
        async with sem:
            await run_one(client, j[0], variant, j[1], j[2], j[3], prog, system, schema, max_tokens)

    await asyncio.gather(*(guarded(j) for j in jobs))
    s = client.stats
    print(f"done: calls {s['calls']} errors {s['errors']} refusals {s['refusals']} cost ${s['cost']:.2f}", flush=True)
    return client


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variant", required=True, choices=P.VARIANTS)
    ap.add_argument("--runs", nargs="+", default=["sim_dataset/runs_night"])
    ap.add_argument("--where", default=None, help="pandas query on split/category/channels/... per run")
    ap.add_argument("--k", type=int, default=None, help="samples per snapshot (default 3 for global_full, else 1)")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--run-parallel", type=int, default=None, help="runs in flight (default = concurrency)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dev", action="store_true", help="only the 8 dev runs (dev_runs.json)")
    ap.add_argument("--exclude-dev", action="store_true")
    ap.add_argument("--max-t", type=int, default=None, help="only snapshots t <= max-t (smoke tests)")
    ap.add_argument("--datamark", action="store_true", help="join words with ^ like the jury (off by default)")
    ap.add_argument("--fake", action="store_true", help="offline pipeline test: fake client, files *_fake.jsonl")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes", action="store_true", help=f"confirm an estimated cost above ${COST_GATE:.0f}")
    a = ap.parse_args(argv)
    k = a.k or (3 if a.variant == "global_full" else 1)
    runs = select_runs(a)
    if not runs:
        sys.exit("no runs selected")
    plan = {}
    for d in runs:
        calls = build_calls(d, a.variant, k=k, datamark=a.datamark)
        if a.max_t:
            calls = [c for c in calls if c["t"] <= a.max_t]
        plan[d] = calls
    # cost of what is still to do
    pv = P.version(a.variant)
    todo = {d: [c for c in cl if (c["t"], c["unit"], c["sample"]) not in done_keys(out_path(d, a.variant, suffix(a)), pv)]
            for d, cl in plan.items()}
    est = estimate(todo, a.variant, k, a.concurrency)
    est_all = estimate(plan, a.variant, k, a.concurrency)
    print(json.dumps({"variant": a.variant, "k": k, "prompt_version": pv, "remaining": est,
                      "total_incl_done": {x: est_all[x] for x in ("calls", "cost_usd")}}, indent=1), flush=True)
    if est["max_prompt_tokens"] > 0.95 * MAX_PROMPT_TOKENS:
        sys.exit(f"a prompt would exceed ~95k tokens ({est['max_prompt_tokens']}); >100k is billed at 5x")
    if a.dry_run:
        return
    if est["cost_usd"] > COST_GATE and not a.yes and not a.fake:
        sys.exit(f"estimated ${est['cost_usd']:.2f} > ${COST_GATE:.0f}: re-run with --yes to confirm")
    asyncio.run(run_all(a, plan, a.variant))


if __name__ == "__main__":
    main()
