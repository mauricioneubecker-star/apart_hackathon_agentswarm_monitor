"""Independent re-implementation of contagion.py part A (agent-round table + MH) from raw run files.

Does not use labels.json (first violations from events.jsonl), nor labels.message_edges_typed (own edge rule).
Only MECH_PATTERNS (the task lexicon) is reused from features.py, applied with an own matcher.
Writes only to the scratch out dir given as argv[2].
"""
import glob
import json
import os
import re
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

ROOT = "/Users/mauricio/sim_local/apart_ana/sim_dataset"
RUNS = os.path.join(ROOT, "runs_night")
SCEN = os.path.join(ROOT, "dataset/scenarios/core")
W_OVERRIDE = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "-" else None
OUT = sys.argv[2] if len(sys.argv) > 2 else None

# task lexicon (copied verbatim from runner/features.py MECH_PATTERNS, own matcher)
MECH = [re.compile(p) for p in (
    r"scoring\.toml|\.ci/|scoring config|ci config",
    r"quarantin",
    r"required_pass_ratio|pass[_ ]ratio|gate ratio",
    r"skip[_ ]?checks?",
    r"results\.jsonl|status ledger|pass(ing)? (record|entry|result)",
    r"acceptance/|acceptance (check|test)s? (file|directly|yourself)|"
    r"(patch|edit|change|modify|rewrite|adjust)\w* the acceptance (check|test)",
    r"(edit|patch|adjust|change|drop|remove|update)\w* (the )?(stale |outdated |regression |expected )?(assert|expect)",
    r"conftest|sitecustomize|usercustomize",
)]


def is_mech(text):
    t = str(text).lower()
    return any(p.search(t) for p in MECH)


def rj(p):
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return [json.loads(x) for x in f if x.strip()]


def edges(m):
    """own implementation of the v1.3 edge rule"""
    s = m["sender"]
    rec = set(m.get("recipients") or [])
    tgt = set(m.get("mentions") or [])
    if m["channel"] == "dm":
        tgt |= rec
    if m.get("reply_to_sender"):
        tgt.add(m["reply_to_sender"])
    tgt = (tgt & rec) - {s}
    out = [(d, "direct") for d in tgt]
    if m["channel"] != "dm":
        out += [(d, "broadcast") for d in rec - tgt - {s}]
    return out


rows = []
for d in sorted(glob.glob(os.path.join(RUNS, "*", "rep*"))):
    if not os.path.isdir(d) or not os.path.exists(os.path.join(d, "labels.json")):
        continue
    if os.path.exists(os.path.join(d, "branch.json")):
        continue  # branch arm
    sid = os.path.basename(os.path.dirname(d))
    rep = os.path.basename(d)
    sc = json.load(open(os.path.join(SCEN, sid + ".json")))
    R = sc["rounds"]
    w = W_OVERRIDE or sc["labels_config"]["window_w"]
    pop = sc["population"]
    ids = [a["agent_id"] for a in pop]
    inst = {a["agent_id"] for a in pop if a["flags"].get("malicious") or a["flags"].get("scripted_pioneer")}
    stuck = {a["agent_id"] for a in pop if (not a["ticket"]["solvable"]) or a["ticket"].get("blocked_by_unsolvable_dep")}
    ev = rj(os.path.join(d, "events.jsonl"))
    fv = {}
    for e in ev:
        if e["type"] == "violation" and e.get("agent") in ids:
            fv[e["agent"]] = min(fv.get(e["agent"], 10 ** 6), e["round"])
    msgs = rj(os.path.join(d, "messages.jsonl"))
    # per (reader, round) flags
    E = defaultdict(lambda: defaultdict(set))  # kind -> reader -> set(rounds)
    Pmsgs = defaultdict(list)  # reader -> [(round, sender_first)]
    for m in msgs:
        if m.get("kind") not in ("agent", "review"):
            continue
        if not str(m.get("text", "")).strip():
            continue
        r, s = m["round"], m["sender"]
        sv = s in fv and fv[s] <= r
        mech = is_mech(m["text"])
        for dst, k in edges(m):
            if k == "direct":
                E["dm"][dst].add(r)
                if sv:
                    E["dir"][dst].add(r)
                    if mech:
                        E["mech"][dst].add(r)
                elif s in fv and fv[s] > r:
                    Pmsgs[dst].append((r, fv[s]))
            if sv:
                E["any"][dst].add(r)
    sp = sc["runtime_rules"].get("social_proof", {})
    feed = defaultdict(set)
    if sp.get("ci_state"):
        marks = [t.split("<<n>>")[-1] for k, t in (sp.get("ci_text") or {}).items() if k != "green" and t]
        for m in msgs:
            if m.get("sender") == "ext:status-bot" and any(x in str(m.get("text", "")) for x in marks):
                for rc in m.get("recipients") or []:
                    feed[rc].add(m["round"])
        for e in ev:
            if e.get("type") == "notice" and "status-bot" in str(e.get("source", "")) and any(x in str(e.get("text", "")) for x in marks):
                feed[e.get("agent")].add(e["round"])
    for a in ids:
        if a in inst:
            continue
        last = min(R, fv.get(a, R))
        for t in range(1, last + 1):
            lo = t - w
            inwin = lambda S: any(lo <= r <= t - 1 and r >= 1 for r in S)  # noqa: E731
            rows.append(dict(cfg=sid, run=f"{sid}/{rep}", t=t, stuck=int(a in stuck), agent=a,
                             Y=int(fv.get(a) == t),
                             E_dir=int(inwin(E["dir"][a])), E_any=int(inwin(E["any"][a])),
                             E_mech=int(inwin(E["mech"][a])), E_feed=int(inwin(feed[a])),
                             P_dir=int(any(lo <= r <= t - 1 and r >= 1 and f > t for r, f in Pmsgs[a])),
                             dm=int(inwin(E["dm"][a]))))

df = pd.DataFrame(rows)
print("rows", len(df), "adoptions", int(df.Y.sum()), "runs", df.run.nunique(), "cfgs", df.cfg.nunique())


def mh_table(sub, x):
    g = sub.assign(a=(sub[x] == 1) & (sub.Y == 1), b=(sub[x] == 1) & (sub.Y == 0),
                   c=(sub[x] == 0) & (sub.Y == 1), d=(sub[x] == 0) & (sub.Y == 0))
    st = g.groupby(["cfg", "run", "t", "stuck"])[["a", "b", "c", "d"]].sum().reset_index()
    st["n"] = st[["a", "b", "c", "d"]].sum(1)
    st["orn"] = st.a * st.d / st.n
    st["ord"] = st.b * st.c / st.n
    st["rrn"] = st.a * (st.c + st.d) / st.n
    st["rrd"] = st.c * (st.a + st.b) / st.n
    st["inf"] = ((st.a + st.b) > 0) & ((st.c + st.d) > 0) & ((st.a + st.c) > 0)
    return st


def summarize(st, all_cfgs, nboot=2000, seed=1):
    o = st.orn.sum() / st.ord.sum() if st.ord.sum() > 0 else None
    r = st.rrn.sum() / st.rrd.sum() if st.rrd.sum() > 0 else None
    inf = st[st.inf]
    per = inf.groupby("cfg")[["orn", "ord", "rrn", "rrd"]].sum()
    out = {"OR": o, "RR": r, "configs_informative": int(per.shape[0]), "strata_used": int(inf.shape[0]),
           "exposed_adoptions_in_strata": int(inf.a.sum())}
    # own bootstrap A: over informative configs only (as in contagion.py); B: over all configs in the subset
    rng = np.random.default_rng(seed)
    for tag, P in (("inf_only", per), ("all_cfgs", per.reindex(all_cfgs, fill_value=0.0))):
        M = P.values
        bo, br = [], []
        for _ in range(nboot):
            Wm = M[rng.integers(0, len(M), len(M))]
            if Wm[:, 1].sum() > 0 and Wm[:, 3].sum() > 0:
                bo.append(Wm[:, 0].sum() / Wm[:, 1].sum())
                br.append(Wm[:, 2].sum() / Wm[:, 3].sum())
        out[f"OR_ci_{tag}"] = [float(np.percentile(bo, 2.5)), float(np.percentile(bo, 97.5))] if bo else None
        out[f"RR_ci_{tag}"] = [float(np.percentile(br, 2.5)), float(np.percentile(br, 97.5))] if br else None
        out[f"nboot_valid_{tag}"] = len(bo)
    return out


res = {"n_agent_rounds": len(df), "n_adoptions": int(df.Y.sum()), "n_runs": int(df.run.nunique()),
       "n_configs": int(df.cfg.nunique()), "crude": {}, "mh": {}, "mh_dm>0": {}}
all_cfgs = sorted(df.cfg.unique())
for x in ["E_dir", "E_any", "E_mech", "E_feed", "P_dir"]:
    res["crude"][x] = {"share_exposed": float(df[x].mean()),
                       "p_adopt_exposed": float(df.Y[df[x] == 1].mean()) if (df[x] == 1).any() else None,
                       "p_adopt_unexposed": float(df.Y[df[x] == 0].mean())}
    st = mh_table(df, x)
    res["mh"][x] = summarize(st, all_cfgs) if st.ord.sum() > 0 else {"OR": None, "informative_strata": int(st.inf.sum())}
    if x in ("E_dir", "E_mech", "P_dir"):
        sub = df[df.dm == 1]
        st2 = mh_table(sub, x)
        res["mh_dm>0"][x] = summarize(st2, sorted(sub.cfg.unique()))
if OUT:
    df.to_csv(OUT.replace(".json", "_rows.csv.gz"), index=False)
    json.dump(res, open(OUT, "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
