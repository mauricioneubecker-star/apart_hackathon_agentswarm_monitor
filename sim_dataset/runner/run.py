#!/usr/bin/env python3
"""Run simulations, jury and labels.

Keys: run `python3 runner/setup_keys.py` once and paste them there (hidden input; stored in
secrets.local.json, chmod 600, gitignored). By default the last key is reserved for the jury and the
others run the simulation, so `simulate` and `jury` need no --keys. Never paste keys into a chat.

Commands
  selftest                                   1 tiny call per key (+ Haiku) - checks keys, models, limits
  simulate --where "<pandas query>"          run episodes; one worker per Adaption key (each ~100 req/min)
           [--replicates 1] [--limit N] [--keys 0,1] [--fake] [--out runs]
  jury     [--watch] [--keys 2] [--judges deepseek-v4-flash,claude-haiku-5-5] [--fake]
                                              score messages of finished episodes (resumable; can run in
                                              parallel to `simulate`, ideally on a different key)
  labels                                     (re)compute labels.json for all finished episodes
  features [--no-nli]                        graph_edges.csv / graph_nodes.csv / graph_meta.json per episode
                                              (feature catalog v1, FEATURES.md; run after `jury`)
  status                                     progress overview

Examples
  python3 runner/run.py simulate --fake --where "batch=='pilot'" --limit 4            # dry run, no network
  python3 runner/run.py simulate --where "batch=='pilot' and phase=='phase1a_probe'"   # pilot step 1
  python3 runner/run.py jury --watch                                                   # second terminal
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "generator"))
from fake import FakeAgentLLM, FakeJudge  # noqa: E402
from jury import RUBRIC_VERSION, judge_run, merge_jury  # noqa: E402
from features import NLI, build_features  # noqa: E402
from labels import compute_labels  # noqa: E402
from llm import AdaptionClient, AnthropicClient, load_secrets  # noqa: E402
from orchestrator import Episode  # noqa: E402
from query import Dataset  # noqa: E402

DATASET = ROOT / "dataset"
JUDGE_PROVIDER = {"deepseek-v4-flash": "adaption", "claude-haiku-5-5": "anthropic"}


def require_pytest():
    """The mock CI runs pytest via sys.executable. Without it every run_tests is silently RED -> abort."""
    import subprocess
    r = subprocess.run([sys.executable, "-m", "pytest", "--version"], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"pytest is not available for {sys.executable} - every CI run would be RED.\n"
                 f"Install the requirements into this interpreter (pip install -r requirements.txt) "
                 f"or use the project venv: .venv/bin/python runner/run.py ...")


def pick_keys(sec, spec, role="sim"):
    """--keys wins; otherwise simulation uses all keys except jury_keys, the jury uses jury_keys."""
    keys = sec["adaption"]
    if spec:
        idx = [int(x) for x in spec.split(",")]
    else:
        jury = set(sec.get("jury_keys", []))
        sim = [i for i in range(len(keys)) if i not in jury] or list(range(len(keys)))
        idx = sorted(jury) if (role == "jury" and jury) else sim
    return [(i, keys[i]) for i in idx if i < len(keys)]


def jury_current(run_dir: Path) -> bool:
    p = run_dir / "jury_merged.jsonl"
    if not p.exists():
        return False
    first = p.open().readline()
    return bool(first.strip()) and json.loads(first).get("rubric") == RUBRIC_VERSION


def finished_runs(out: Path):
    return sorted(p.parent for p in out.glob("*/rep*/meta.json"))


async def simulate(a):
    require_pytest()
    ds = Dataset(DATASET)
    rows = ds.where(a.where) if a.where else ds.index
    out = Path(a.out)
    jobs = [(sid, r) for sid in rows.scenario_id for r in range(a.replicates)
            if not (out / sid / f"rep{r}" / "meta.json").exists()]
    if a.limit:
        jobs = jobs[: a.limit]
    if not jobs:
        print("nothing to do")
        return
    if a.fake:
        workers = [None] * max(1, a.workers)
    else:
        keys = pick_keys(load_secrets(), a.keys)
        if not keys:
            sys.exit("No Adaption keys found (secrets.local.json or ADAPTION_API_KEYS).")
        workers = [AdaptionClient(k, i, per_minute=a.rpm) for i, k in keys]
    asyncio.get_running_loop().set_default_executor(ThreadPoolExecutor(max_workers=32 * len(workers) + 8))
    q = asyncio.Queue()
    for j in jobs:
        q.put_nowait(j)
    total, t0 = len(jobs), time.time()
    done = [0]
    print(f"{total} episodes, {len(workers)} worker(s){' (fake LLM)' if a.fake else ''}")

    async def worker(client):
        while not q.empty():
            sid, rep = q.get_nowait()
            sc = ds.load(sid)
            run_dir = out / sid / f"rep{rep}"
            llm = FakeAgentLLM(sc, sc["replicate_seeds"][rep]) if client is None else client
            (run_dir / "error.txt").unlink(missing_ok=True)  # stale error from an earlier attempt
            try:
                ep = Episode(sc, rep, llm, run_dir, DATASET)
                meta = await ep.run()
                lab = compute_labels(sc, run_dir)
                done[0] += 1
                el = time.time() - t0
                print(f"[{done[0]}/{total}] {sid} rep{rep}: {meta['duration_s']}s, invalid_json={meta['invalid_json_rate']}, "
                      f"violators={lab['n_violators']}, tipped={lab['tipped']} (ETA {el / done[0] * (total - done[0]) / 60:.0f} min)",
                      flush=True)
            except Exception:  # keep the batch going
                (run_dir / "error.txt").write_text(traceback.format_exc())
                print(f"ERROR {sid} rep{rep}: see {run_dir / 'error.txt'}", flush=True)
    await asyncio.gather(*(worker(c) for c in workers))
    if not a.fake:
        for c in workers:
            print(f"key {c.idx}: {c.stats}")


async def jury(a):
    out = Path(a.out)
    judges = a.judges.split(",")
    clients = {}
    if a.fake:
        clients = {j: [FakeJudge(j)] for j in judges}
    else:
        sec = load_secrets()
        for j in judges:
            if JUDGE_PROVIDER[j] == "anthropic":
                if not sec["anthropic"]:
                    sys.exit("No Anthropic key (secrets.local.json 'anthropic' or ANTHROPIC_API_KEY).")
                clients[j] = [AnthropicClient(sec["anthropic"], concurrency=a.anthropic_concurrency)]
            else:
                keys = pick_keys(sec, a.keys, role="jury")
                clients[j] = [AdaptionClient(k, i, per_minute=a.rpm) for i, k in keys]
    asyncio.get_running_loop().set_default_executor(ThreadPoolExecutor(max_workers=64))
    seen = set()
    while True:
        runs = [r for r in finished_runs(out) if r not in seen and not jury_current(r)]
        for i, rd in enumerate(runs):
            tasks = []
            for j in judges:
                c = clients[j][i % len(clients[j])]
                group = a.group_deepseek if JUDGE_PROVIDER[j] == "adaption" else 1
                tasks.append(judge_run(rd, j, c, group_size=group))
            n = await asyncio.gather(*tasks)
            m = merge_jury(rd, judges)
            seen.add(rd)
            print(f"jury {rd.relative_to(out)}: scored {n}, merged {m}", flush=True)
        if not a.watch:
            break
        await asyncio.sleep(60)


async def selftest(a):
    require_pytest()
    print(f"python: {sys.executable} (pytest ok)")
    sec = load_secrets()
    asyncio.get_running_loop().set_default_executor(ThreadPoolExecutor(max_workers=16))
    msg = [{"role": "user", "content": 'Reply with ONLY {"ok": true}'}]
    if not sec["adaption"]:
        print("no Adaption keys - run: python3 runner/setup_keys.py")
    jury = set(sec.get("jury_keys", []))

    async def one(i, k):
        r = await AdaptionClient(k, i).chat("qwen3.8-27b", msg, max_tokens=20, temperature=0, reasoning_effort="none")
        role = "jury" if i in jury else "simulation"
        print(f"adaption key {i} ({k[:8]}…{k[-4:]}, {role}): status={r['status']} "
              f"text={str(r['text'])[:30]!r} err={str(r['error'])[:120]}")
    await asyncio.gather(*(one(i, k) for i, k in enumerate(sec["adaption"])))
    if sec["anthropic"]:
        c = AnthropicClient(sec["anthropic"])
        r = await c.chat("claude-haiku-5-5", msg, max_tokens=20)
        print(f"anthropic: status={r['status']} text={str(r['text'])[:40]!r} err={str(r['error'])[:160]}")
    else:
        print("anthropic: no key configured")


def labels_cmd(a):
    ds = Dataset(DATASET)
    for rd in finished_runs(Path(a.out)):
        lab = compute_labels(ds.load(rd.parent.name), rd)
        print(rd.parent.name, rd.name, "violators", lab["n_violators"], "tipped", lab["tipped"])


def features_cmd(a):
    ds = Dataset(DATASET)
    nli = NLI(enabled=not a.no_nli)
    if not a.no_nli and not nli.ok:
        print(f"NLI model not available ({getattr(nli, 'err', '')}); 'contradiction' will be NaN. "
              "Install transformers + torch or pass --no-nli.")
    for rd in finished_runs(Path(a.out)):
        meta = build_features(ds.load(rd.parent.name), rd, nli)
        print(f"{rd.parent.name} {rd.name}: edges={meta['n_edges']} jury_coverage={meta['jury_coverage']} "
              f"nli={meta['nli']['available']}")


def status_cmd(a):
    out = Path(a.out)
    runs = finished_runs(out)
    errs = list(out.glob("*/rep*/error.txt"))
    tipped = sum(json.loads((r / "labels.json").read_text())["tipped"] for r in runs if (r / "labels.json").exists())
    jur = sum(jury_current(r) for r in runs)
    print(f"finished episodes: {len(runs)}  errors: {len(errs)}  tipped: {tipped}  jury done: {jur}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["selftest", "simulate", "jury", "labels", "features", "status"])
    ap.add_argument("--where", default=None)
    ap.add_argument("--replicates", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--keys", default=None, help="comma-separated key indices from secrets.local.json")
    ap.add_argument("--rpm", type=int, default=95, help="requests per minute per key (endpoint limit: 100)")
    ap.add_argument("--fake", action="store_true", help="fake LLMs, no network")
    ap.add_argument("--workers", type=int, default=3, help="parallel episodes in --fake mode")
    ap.add_argument("--out", default=str(ROOT / "runs"))
    ap.add_argument("--judges", default="deepseek-v4-flash,claude-haiku-5-5")
    ap.add_argument("--group-deepseek", type=int, default=8, help="messages per DeepSeek call (same round)")
    ap.add_argument("--anthropic-concurrency", type=int, default=8)
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--no-nli", action="store_true", help="features: skip the NLI contradiction feature (NaN)")
    a = ap.parse_args()
    if a.cmd == "simulate":
        asyncio.run(simulate(a))
    elif a.cmd == "jury":
        asyncio.run(jury(a))
    elif a.cmd == "selftest":
        asyncio.run(selftest(a))
    elif a.cmd == "labels":
        labels_cmd(a)
    elif a.cmd == "features":
        features_cmd(a)
    else:
        status_cmd(a)


if __name__ == "__main__":
    main()
