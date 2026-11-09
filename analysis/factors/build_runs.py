#!/usr/bin/env python3
"""Run-level and config-level tables for the night-batch factor analysis.

Reads (read-only):
  <ana>/sim_dataset/runs_night/<scenario>/<rep>[-<arm>]/labels.json, meta.json, events.jsonl
  <ana>/sim_dataset/dataset/index.csv
Writes: runs.csv (control runs), runs_all.csv (incl. branch arms), configs.csv into this script's directory.

Control run = rep dir whose name contains no '-' (branch arms rep0-<arm> excluded; branch rep0 controls kept).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ANA = Path("/Users/mauricio/sim_local/apart_ana/sim_dataset")
RUNS = ANA / "runs_night"
OUT = Path(__file__).resolve().parent
NIGHT_SPLITS = ["night_train", "night_val", "night_test_id", "night_test_ood_family", "night_test_ood_seed",
                "night_branch"]


def as_bool(x):
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    s = str(x).strip().lower()
    if s in ("true", "1", "1.0"):
        return True
    if s in ("false", "0", "0.0"):
        return False
    raise ValueError(f"not a bool: {x!r}")


def main():
    idx = pd.read_csv(ANA / "dataset" / "index.csv", low_memory=False)
    idx = idx[idx.split.isin(NIGHT_SPLITS)].copy()
    assert len(idx) == 112 and idx.scenario_id.is_unique, len(idx)
    rows = []
    for lab_f in sorted(RUNS.glob("*/rep*/labels.json")):
        rd = lab_f.parent
        sid, rep = rd.parent.name, rd.name
        lab = json.loads(lab_f.read_text())
        meta = json.loads((rd / "meta.json").read_text())
        assert lab["scenario_id"] == sid and lab["theta_agents"] == 8 and lab["delta"] == 3
        n_sanc = n_viol_ev = 0
        with open(rd / "events.jsonl") as fh:
            for line in fh:
                e = json.loads(line)
                t = e.get("type")
                if t == "sanction":
                    n_sanc += 1
                elif t == "violation":
                    n_viol_ev += 1
        arm = rep.split("-", 1)[1] if "-" in rep else "control"
        rows.append(dict(scenario_id=sid, rep=rep, arm=arm, replicate=int(meta["replicate"]),
                         tipped=int(bool(lab["tipped"])), tip_round=lab["tip_round"], n_violators=lab["n_violators"],
                         n_sanction_events=n_sanc, n_violation_events=n_viol_ev, started=meta.get("started")))
    allruns = pd.DataFrame(rows)
    print(f"label files: {len(allruns)}, configs with runs: {allruns.scenario_id.nunique()}")
    print("arms:", allruns.arm.value_counts().to_dict())

    f = pd.DataFrame({"scenario_id": idx.scenario_id, "split": idx.split, "family": idx.family})
    f["category"] = idx.category.map({"K2_scorer_config_tamper": "K2", "K4_check_bypass": "K4"})
    for c in ["release_freeze", "manager_push", "self_merge"]:
        f[c] = idx[c].map(as_bool)
    f["discoverability"] = idx.discoverability
    f["channels"] = idx.channels
    f["persistent_share"] = idx.persistent_share.astype(float)
    f["prohibition_form"] = idx.prohibition_form
    f["n_impossible"] = idx.n_impossible.astype(int)
    f["persona_mix"] = idx.persona_mix
    f["sanctions"] = idx.sanctions
    f["model_mix"] = idx.model_mix.astype(str).str.split(":").str[0]
    f["seed_type"] = idx.seed_type
    f["seed_tech_lead"] = (idx.seed_status.astype(str) == "tech_lead")
    f["tl_eligible"] = idx.seed_type.isin(["knower", "pioneer", "side_task"])
    f["seed_placement"] = idx.seed_placement
    f["cut"] = idx.deadline_override.astype(int)
    f["push_offset"] = idx.push_offset.astype(int)
    f["detection_probability"] = idx.detection_probability.astype(float)
    f["sanction_type"] = idx.sanction
    f["enforcer"] = idx.enforcer
    f["enforced"] = f.detection_probability > 0          # a sanction can actually fire (detection > 0)
    f["malicious_variant"] = idx.malicious_variants.fillna("-")
    f["injection_carrier"] = idx.injection_carrier
    f["replicates_planned"] = idx.replicates_planned.astype(int)
    assert not (f.seed_tech_lead & ~f.tl_eligible).any()
    assert set(f.release_freeze.unique()) == {True, False}

    allruns = allruns.merge(f, on="scenario_id", how="left", validate="many_to_one")
    assert allruns.split.notna().all()
    allruns.to_csv(OUT / "runs_all.csv", index=False)
    runs = allruns[allruns.arm == "control"].copy()
    runs.to_csv(OUT / "runs.csv", index=False)

    g = runs.groupby("scenario_id").agg(n_runs=("tipped", "size"), n_tipped=("tipped", "sum"),
                                        tip_rate=("tipped", "mean"), mean_violators=("n_violators", "mean"),
                                        n_sanction_events=("n_sanction_events", "sum")).reset_index()
    cfg = f.merge(g, on="scenario_id", how="left", validate="one_to_one")
    assert cfg.n_runs.notna().all(), "config without control run"
    cfg.to_csv(OUT / "configs.csv", index=False)

    print(f"control runs: {len(runs)} in {runs.scenario_id.nunique()} configs; tipped {runs.tipped.sum()} "
          f"({runs.tipped.mean():.4f}); all 252 runs tipped {allruns.tipped.sum()} ({allruns.tipped.mean():.4f})")
    print("runs per config:", cfg.n_runs.value_counts().sort_index().to_dict())
    print("replicate index of control runs:", runs.replicate.value_counts().sort_index().to_dict())
    print("configs per split:", cfg.split.value_counts().to_dict())
    print("control runs per split:", runs.split.value_counts().to_dict())
    print(f"config-level mean tip rate: {cfg.tip_rate.mean():.4f}")

    # cross-check against the batch's own per-run table (written by the night pipeline)
    ar = pd.read_csv(RUNS / "_logs" / "analysis_runs.csv")
    m = allruns.merge(ar[["cfg", "rep", "tipped", "tip_round", "nv"]].rename(columns={"cfg": "scenario_id"}),
                      on=["scenario_id", "rep"], how="outer", suffixes=("", "_ar"), indicator=True)
    print("analysis_runs.csv merge:", m._merge.value_counts().to_dict())
    both = m[m._merge == "both"]
    mism = (both.tipped.astype(int) != both.tipped_ar.astype(bool).astype(int)).sum()
    mism_nv = (both.n_violators != both.nv).sum()
    print(f"tipped mismatches vs analysis_runs.csv: {mism}; n_violators mismatches: {mism_nv}")
    fac_check = ["release_freeze", "manager_push", "discoverability", "channels", "self_merge", "persistent_share",
                 "prohibition_form", "n_impossible", "persona_mix", "sanctions", "seed_type", "split"]
    ar2 = ar.rename(columns={"cfg": "scenario_id"}).drop_duplicates("scenario_id").set_index("scenario_id")
    ff = f.set_index("scenario_id").loc[ar2.index]
    bad = {}
    for c in fac_check:
        a = ff[c].astype(str).str.lower().str.replace(".0$", "", regex=True)
        b = ar2[c].astype(str).str.lower().str.replace(".0$", "", regex=True)
        bad[c] = int((a != b).sum())
    print("factor mismatches vs analysis_runs.csv:", bad)
    if mism or mism_nv or any(bad.values()):
        sys.exit("cross-check failed")


if __name__ == "__main__":
    main()
