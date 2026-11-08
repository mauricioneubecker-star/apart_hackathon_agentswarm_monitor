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
from jury import RUBRIC_VERSION, judge_run, jury_complete, merge_jury  # noqa: E402
from features import NLI, build_features  # noqa: E402
from labels import compute_labels  # noqa: E402
from llm import ADAPTION_BASE, AdaptionClient, AnthropicClient, ApiUnavailable, load_secrets  # noqa: E402
from orchestrator import Episode  # noqa: E402
from query import Dataset  # noqa: E402

DATASET = ROOT / "dataset"
JUDGE_PROVIDER = {"deepseek-v4-flash": "adaption", "claude-haiku-5-5": "anthropic"}


def require_pytest():
    """The mock CI runs pytest via sys.executable. Without it every run_tests is silently RED -> abort.
    Then proves the CI sandbox isolates agent code (runner/sandbox_check.py) -> abort if not."""
    import os
    import subprocess
    r = subprocess.run([sys.executable, "-m", "pytest", "--version"], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"pytest is not available for {sys.executable} - every CI run would be RED.\n"
                 f"Install the requirements into this interpreter (pip install -r requirements.txt) "
                 f"or use the project venv: .venv/bin/python runner/run.py ...")
    if os.environ.get("SIM_ALLOW_UNSANDBOXED") == "1":
        print("WARNING: SIM_ALLOW_UNSANDBOXED=1 - sandbox check skipped, agent code may run without isolation")
        return
    r = subprocess.run([sys.executable, str(HERE / "sandbox_check.py")], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        sys.exit(r.stdout + r.stderr + "\nCI sandbox check failed - refusing to run agent code without isolation.")
    print("sandbox check: OK (no network, no keys/home/dataset access, no subprocesses for agent code)")


_api_wait_lock = None


async def wait_for_api(interval: float = 30):
    """Block until the Adaption host accepts TCP connections again (DNS + connect). Shared by all workers."""
    global _api_wait_lock
    import socket
    from urllib.parse import urlparse
    host = urlparse(ADAPTION_BASE).hostname

    def reachable() -> bool:
        try:
            socket.create_connection((host, 443), timeout=5).close()
            return True
        except OSError:
            return False

    _api_wait_lock = _api_wait_lock or asyncio.Lock()
    async with _api_wait_lock:  # one worker probes and prints, the others wait behind it
        if await asyncio.to_thread(reachable):
            return
        t = time.time()
        print(f"API host {host} unreachable - waiting (probe every {interval:.0f}s) ...", flush=True)
        while not await asyncio.to_thread(reachable):
            await asyncio.sleep(interval)
        print(f"API host reachable again after {(time.time() - t) / 60:.1f} min - resuming", flush=True)


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


DEFAULT_JUDGES = "deepseek-v4-flash,claude-haiku-5-5"


def jury_current(run_dir: Path, judges=None) -> bool:
    """Complete = every judgeable message has a valid, current score from every judge (see jury.jury_complete).
    Episodes with missing/failed/outdated scores are picked up again by `jury`."""
    return jury_complete(run_dir, judges or DEFAULT_JUDGES.split(","))


def finished_runs(out: Path):
    return sorted(p.parent for p in out.glob("*/rep*/meta.json"))


def resolve_env_models(sc: dict) -> tuple[dict, list[str]]:
    """v1.7: model entries whose provider_model_id is '$VAR' (validation-suite fine-tune arms) are resolved from the
    environment at run time, so no model id is baked into the dataset. SWARM_FT_OMIT_PARAMS (comma list, e.g.
    'reasoning_effort') drops request params for these models. Returns the scenario and the unresolved variables."""
    import os
    missing = []
    for m in sc["models"].values():
        pid = m.get("provider_model_id", "")
        if isinstance(pid, str) and pid.startswith("$"):
            val = os.environ.get(pid[1:])
            if not val:
                missing.append(pid[1:])
                continue
            m["provider_model_id"] = val
            omit = [x.strip() for x in os.environ.get("SWARM_FT_OMIT_PARAMS", "").split(",") if x.strip()]
            if omit:
                m["omit_params"] = omit
    return sc, missing


def with_persistent_model(sc: dict, provider_model_id: str, base: str | None = None) -> dict:
    """v1.6: fine-tuned arm. Agents flagged `persistent` (prompted persistence persona in the generated scenario) get
    the fine-tuned model instead and lose the persona sentence, so the same config runs once with prompted and once
    with fine-tuned persistence (use a separate --out). All other agents and the seeds stay unchanged. With `base`
    (--persistent-base, e.g. the fine-tune's base model) only flagged agents on that model are swapped, so the
    comparison is not confounded by a change of model family."""
    import copy
    from config import PERSONAS
    sc = copy.deepcopy(sc)
    flagged = [a for a in sc["population"] if a["flags"].get("persistent") and (base is None or a["model"] == base)]
    if not flagged:
        return sc
    for a in flagged:
        base = sc["models"][a["model"]]
        key = f"ft-persistent:{a['model']}"
        sc["models"].setdefault(key, dict(base, provider_model_id=provider_model_id, split_role="finetuned",
                                          base_model=a["model"]))
        a["model"] = key
        a["system_prompt"] = a["system_prompt"].replace(" " + PERSONAS["persistent"], "").replace(PERSONAS["persistent"], "")
    sc["persistent_model"] = provider_model_id
    return sc


async def simulate(a):
    require_pytest()
    ds = Dataset(DATASET)
    rows = ds.where(a.where) if a.where else ds.index
    out = Path(a.out)
    # v1.6: --replicates 0 = replicates_planned from the index (night batch: blocks differ)
    reps = {sid: (int(rp) if a.replicates == 0 and rp == rp else max(1, a.replicates))
            for sid, rp in zip(rows.scenario_id, rows.get("replicates_planned", [1] * len(rows)))}
    jobs = [(sid, r) for sid in rows.scenario_id for r in range(reps[sid])
            if not (out / sid / f"rep{r}" / "meta.json").exists()]
    if not jobs:
        print("nothing to do")
        return
    if not a.fake:   # v1.7: env-resolved model ids (fine-tune arms) must be set before anything starts
        miss = sorted({v for sid in {j[0] for j in jobs} for v in resolve_env_models(ds.load(sid))[1]})
        if miss:
            sys.exit(f"model id(s) not set: {', '.join(miss)} (export them, or exclude the night_vx_ft* splits)")
    # longest jobs first: branched episodes run 3 arms on one key and would otherwise form a long tail at the end
    # (outcomes are unaffected - every episode has its own seed)
    branched = {sid for sid, _ in jobs if ds.load(sid).get("branching")}
    if a.order == "replicate":   # v1.6: all rep0 first, so a run stopped early still covers every config once
        jobs.sort(key=lambda j: (j[1], 0 if j[0] in branched else 1))
    else:
        jobs.sort(key=lambda j: 0 if j[0] in branched else 1)
    if a.limit:
        jobs = jobs[: a.limit]
    if a.persistent_model:
        print(f"persistent agents -> model {a.persistent_model!r} (persona sentence removed)")
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

    def past_stop() -> bool:   # v1.6: --stop-at HHMM (evening counts as before, so overnight runs work)
        if not a.stop_at:
            return False
        now = int(time.strftime("%H%M"))
        return int(a.stop_at) <= now <= 1800

    async def worker(client):
        while not q.empty():
            if past_stop():
                print(f"stop-at {a.stop_at} reached: worker takes no new episode", flush=True)
                return
            sid, rep = q.get_nowait()
            sc = ds.load(sid)
            if not a.fake:
                sc = resolve_env_models(sc)[0]
            if a.persistent_model:
                sc = with_persistent_model(sc, a.persistent_model, a.persistent_base)
            run_dir = out / sid / f"rep{rep}"
            llm = FakeAgentLLM(sc, sc["replicate_seeds"][rep]) if client is None else client
            (run_dir / "error.txt").unlink(missing_ok=True)  # stale error from an earlier attempt
            try:
                ep = Episode(sc, rep, llm, run_dir, DATASET)
                meta = await ep.run()
            except ApiUnavailable as e:  # API/network down: discard the partial episode, re-queue, wait for the API
                aborts[(sid, rep)] = aborts.get((sid, rep), 0) + 1
                if aborts[(sid, rep)] > a.max_aborts:
                    (run_dir / "error.txt").write_text(f"gave up after {a.max_aborts} API aborts\n{e}\n")
                    print(f"ERROR {sid} rep{rep}: API kept failing ({e})", flush=True)
                    continue
                print(f"ABORTED {sid} rep{rep} (will re-run from scratch): {e}", flush=True)
                q.put_nowait((sid, rep))
                await wait_for_api()
                continue
            except Exception:  # keep the batch going; v1.6: retry the episode from scratch up to --episode-retries
                (run_dir / "error.txt").write_text(traceback.format_exc())
                fails[(sid, rep)] = fails.get((sid, rep), 0) + 1
                if fails[(sid, rep)] <= a.episode_retries:
                    print(f"ERROR {sid} rep{rep} (attempt {fails[(sid, rep)]}, will retry): see {run_dir / 'error.txt'}",
                          flush=True)
                    q.put_nowait((sid, rep))
                    await asyncio.sleep(30)
                else:
                    print(f"ERROR {sid} rep{rep}: gave up after {fails[(sid, rep)]} attempts, see {run_dir / 'error.txt'}",
                          flush=True)
                continue
            # v1.6: the episode is complete (meta.json written); a failure in the labels below must not re-run it
            lab = {"n_violators": "?", "tipped": "?"}
            try:
                lab = compute_labels(sc, run_dir)
                for arm, cdir, _ in ep.children:   # v1.3b branch arms (rep<k>-<arm>)
                    clab = compute_labels(sc, cdir)
                    br = json.loads((cdir / "branch.json").read_text())["branch_round"]
                    print(f"    branch {arm} (from cycle {br}): violators={clab['n_violators']}, tipped={clab['tipped']}",
                          flush=True)
            except Exception:
                print(f"WARNING {sid} rep{rep}: labels failed (re-run `labels` later):\n{traceback.format_exc()[-600:]}",
                      flush=True)
            done[0] += 1
            el = time.time() - t0
            print(f"[{done[0]}/{total}] {sid} rep{rep}: {meta['duration_s']}s, invalid_json={meta['invalid_json_rate']}, "
                  f"violators={lab['n_violators']}, tipped={lab['tipped']} (ETA {el / done[0] * (total - done[0]) / 60:.0f} min)",
                  flush=True)

    aborts: dict = {}
    fails: dict = {}
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
    # Episodes are judged concurrently: up to 2 per Adaption jury key (each episode pinned to one key, the rate
    # limiter per key does the pacing); the Anthropic client is shared (--anthropic-concurrency).
    n_keys = max([len(c) for j, c in clients.items() if JUDGE_PROVIDER.get(j) == "adaption"] or [1])
    parallel = a.jury_parallel or 2 * n_keys
    asyncio.get_running_loop().set_default_executor(ThreadPoolExecutor(max_workers=64 + 8 * parallel))
    attempts: dict = {}
    MAX_ATTEMPTS = 3  # per episode and session; failed messages are retried, but no endless loop on one episode

    async def judge_episode(i, rd, sem):
        async with sem:
            tasks = []
            for j in judges:
                c = clients[j][i % len(clients[j])]
                group = a.group_deepseek if JUDGE_PROVIDER[j] == "adaption" else 1
                tasks.append(judge_run(rd, j, c, group_size=group))
            n = await asyncio.gather(*tasks)
            m = merge_jury(rd, judges)
            done = jury_current(rd, judges)
            attempts[rd] = attempts.get(rd, 0) + (0 if done else 1)
            note = "" if done else (f"  INCOMPLETE (attempt {attempts[rd]}/{MAX_ATTEMPTS})"
                                    + (" - giving up for this session" if attempts[rd] >= MAX_ATTEMPTS else ""))
            print(f"jury {rd.relative_to(out)}: scored {n}, merged {m}{note}", flush=True)

    print(f"jury: {', '.join(judges)}; up to {parallel} episodes in parallel", flush=True)
    while True:
        runs = [r for r in finished_runs(out) if attempts.get(r, 0) < MAX_ATTEMPTS and not jury_current(r, judges)]
        if runs:
            sem = asyncio.Semaphore(parallel)
            await asyncio.gather(*(judge_episode(i, rd, sem) for i, rd in enumerate(runs)))
        if not a.watch:
            break
        await asyncio.sleep(20 if runs else 45)


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
        c = AdaptionClient(k, i)
        r = await c.chat("qwen3.8-27b", msg, max_tokens=20, temperature=0, reasoning_effort="none")
        role = "jury" if i in jury else "simulation"
        lim = f"{c.server_limit}/min" if c.server_limit else "unknown"
        warn = "  <- low limit: ~5x slower per episode" if c.server_limit and c.server_limit < 50 else ""
        print(f"adaption key {i} ({k[:8]}…{k[-4:]}, {role}, limit {lim}): status={r['status']} "
              f"text={str(r['text'])[:30]!r} err={str(r['error'])[:120]}{warn}")
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
        gm, jm = rd / "graph_meta.json", rd / "jury_merged.jsonl"
        if a.missing_only and gm.exists() and (not jm.exists() or gm.stat().st_mtime >= jm.stat().st_mtime):
            continue   # v1.6: incremental (overnight post-processing)
        meta = build_features(ds.load(rd.parent.name), rd, nli, jury=a.jury)
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
    ap.add_argument("--episode-retries", type=int, default=0,
                    help="simulate: re-run an episode that raised an error up to N more times (fresh run dir)")
    ap.add_argument("--max-aborts", type=int, default=3,
                    help="simulate: re-queues per episode after API outages before giving up")
    ap.add_argument("--stop-at", default=None, help="simulate: HHMM after which no new episode is started")
    ap.add_argument("--missing-only", action="store_true",
                    help="features: skip episodes whose features are newer than their jury scores")
    ap.add_argument("--order", choices=["config", "replicate"], default="config",
                    help="simulate: 'replicate' runs rep0 of every config first (overnight batches)")
    ap.add_argument("--persistent-model", default=None,
                    help="simulate: provider model id of the persistence fine-tune for agents flagged 'persistent'")
    ap.add_argument("--persistent-base", default=None,
                    help="simulate: only swap persistent agents on this model key (the fine-tune's base, e.g. qwen3.8-27b)")
    ap.add_argument("--keys", default=None, help="comma-separated key indices from secrets.local.json")
    ap.add_argument("--rpm", type=int, default=95, help="requests per minute per key (endpoint limit: 100)")
    ap.add_argument("--fake", action="store_true", help="fake LLMs, no network")
    ap.add_argument("--workers", type=int, default=3, help="parallel episodes in --fake mode")
    ap.add_argument("--out", default=str(ROOT / "runs"))
    ap.add_argument("--judges", default=DEFAULT_JUDGES)
    ap.add_argument("--group-deepseek", type=int, default=8, help="messages per DeepSeek call (same round)")
    ap.add_argument("--anthropic-concurrency", type=int, default=24,
                    help="parallel Haiku calls (account limit seen: 4000 req/min)")
    ap.add_argument("--jury-parallel", type=int, default=0,
                    help="episodes judged concurrently (default: 2 per Adaption jury key)")
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--no-nli", action="store_true", help="features: skip the NLI contradiction feature (NaN)")
    ap.add_argument("--jury", default=None, help="features: single judge (e.g. deepseek-v4-flash, claude-haiku-5-5) "
                    "-> graph_*_<judge>.csv for the judge-swap ablation; default merged jury")
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
