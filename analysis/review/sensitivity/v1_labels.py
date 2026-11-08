"""Independent re-derivation of every label-dependent column in sens/data/<tag>/_base/{snapshots,nodes}.csv.
Reads labels.json (read-only) directly; does NOT import llm_monitor or gnn code."""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

ANA = "/Users/mauricio/sim_local/apart_ana"
SENS = sys.argv[1]
RUNS = os.path.join(ANA, "sim_dataset", "runs_night")
TAGS = {"t8d3": (8, 3), "t6d3": (6, 3), "t10d3": (10, 3), "t8d2": (8, 2), "t8d5": (8, 5)}

runs = [d for d in sorted(glob.glob(os.path.join(RUNS, "*", "rep*")))
        if os.path.isdir(d) and all(os.path.exists(os.path.join(d, f)) for f in ("messages.jsonl", "labels.json"))]
print("runs found", len(runs))
L = {}
for d in runs:
    eid = f"{os.path.basename(os.path.dirname(d))}/{os.path.basename(d)}"
    L[eid] = json.load(open(os.path.join(d, "labels.json")))

# sanity: labels.json itself is theta 8 / delta 3
th = pd.Series({e: l.get("theta_agents") for e, l in L.items()}).value_counts().to_dict()
de = pd.Series({e: l.get("delta") for e, l in L.items()}).value_counts().to_dict()
print("labels.json theta_agents:", th, "delta:", de)


def derive(theta, delta):
    S, N = [], []
    for eid, l in L.items():
        R = len(l["per_round"])
        first = l["first_violation_round"]
        cnt = {t: sum(1 for r in first.values() if r <= t) for t in range(0, R + 1)}
        tr = next((t for t in range(1, R + 1) if cnt[t] >= theta), None)
        for t in range(1, R + 1):
            hi = min(R, t + delta)
            tip = (float(any(cnt[u] >= theta for u in range(t + 1, hi + 1))) if cnt[t] < theta else np.nan)
            S.append({"episode_id": eid, "t": t, "tip_x": tip, "risk_count_x": cnt[t], "tipped_x": int(tr is not None),
                      "tip_round_x": np.nan if tr is None else float(tr)})
    S = pd.DataFrame(S)
    return S


ok_all = True
summary = {}
for tag, (theta, delta) in TAGS.items():
    B = pd.read_csv(os.path.join(SENS, "data", tag, "_base", "snapshots.csv"), low_memory=False)
    X = derive(theta, delta)
    M = B.merge(X, on=["episode_id", "t"], how="outer", indicator=True)
    assert (M._merge == "both").all(), M._merge.value_counts()
    res = {}
    for c in ("tip", "risk_count", "tipped", "tip_round"):
        a, b = M[c].astype(float).values, M[c + "_x"].astype(float).values
        res[c] = int((~((a == b) | (np.isnan(a) & np.isnan(b)))).sum())
    # mixed: config has both tipped and untipped runs (all runs of the config incl. branch arms)
    rt = X.groupby("episode_id").tipped_x.first()
    cfg = pd.Series({e: e.split("/")[0] for e in rt.index})
    mixed_cfg = rt.groupby(cfg).nunique() > 1
    M["mixed_x"] = M.episode_id.map(lambda e: int(mixed_cfg[e.split("/")[0]]))
    res["mixed"] = int((M.mixed != M.mixed_x).sum())
    # group_id == scenario dir?
    res["group_id_vs_dir"] = int((M.group_id != M.episode_id.str.split("/").str[0]).sum())
    # labels.json consistency at theta 8
    if theta == 8:
        lj_t = pd.Series({e: int(bool(l.get("tipped"))) for e, l in L.items()})
        lj_r = pd.Series({e: l.get("tip_round") for e, l in L.items()}).astype(float)
        res["labels_json_tipped_mismatch"] = int((lj_t != rt.reindex(lj_t.index)).sum())
        xr = X.groupby("episode_id").tip_round_x.first().reindex(lj_r.index)
        res["labels_json_tip_round_mismatch"] = int((~((lj_r == xr) | (lj_r.isna() & xr.isna()))).sum())
        # per_round tip_within_delta (labels.json, delta 3) vs derived tip at delta=3
        if delta == 3:
            pr = []
            for e, l in L.items():
                for r in l["per_round"]:
                    pr.append({"episode_id": e, "t": r["round"], "tw": np.nan if r["tip_within_delta"] is None else float(r["tip_within_delta"]),
                               "rc": r["risk_count_t"]})
            pr = pd.DataFrame(pr).merge(X, on=["episode_id", "t"])
            res["labels_json_per_round_tip_mismatch"] = int((~((pr.tw == pr.tip_x) | (pr.tw.isna() & pr.tip_x.isna()))).sum())
            res["labels_json_per_round_count_mismatch"] = int((pr.rc != pr.risk_count_x).sum())
    # nodes: violates_within_delta (depends on delta only)
    Nd = pd.read_csv(os.path.join(SENS, "data", tag, "_base", "nodes.csv"))
    Rof = {e: len(l["per_round"]) for e, l in L.items()}
    f = np.array([L[e]["first_violation_round"].get(a, 99) for e, a in zip(Nd.episode_id, Nd.node_id)], float)
    tt = Nd.t.values.astype(float)
    hi = np.minimum(Nd.episode_id.map(Rof).values, tt + delta)
    vwd = np.where(f <= tt, np.nan, (f <= hi).astype(float))
    a = Nd.violates_within_delta.values
    res["node_vwd_mismatch"] = int((~((a == vwd) | (np.isnan(a) & np.isnan(vwd)))).sum())
    res["node_rows"] = len(Nd)
    res["node_pos"] = int(np.nansum(a))
    runs_t = rt
    res["tipped_runs"] = f"{int(runs_t.sum())}/{len(runs_t)}"
    rows = M[M.tip.notna() & M.split.str.startswith("night_") & ~M.split.str.startswith("night_vx")]
    res["tip_rows"] = f"{int(rows.tip.sum())}/{len(rows)}"
    res["mixed_cfgs"] = int(mixed_cfg.sum())
    summary[tag] = res
    ok_all &= all(v == 0 for k, v in res.items() if k.endswith("mismatch") or k in ("tip", "risk_count", "tipped", "tip_round", "mixed", "group_id_vs_dir"))
print(pd.DataFrame(summary).T.to_string())
print("ALL LABEL COLUMNS MATCH:", ok_all)
