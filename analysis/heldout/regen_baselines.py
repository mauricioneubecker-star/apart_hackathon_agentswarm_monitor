"""Refit harness baselines on night_train (exactly baselines.py: same specs, same train rows, same HGB settings)
and predict every snapshot of every non-train split. Needed because the committed gnn_opt/preds/eval files for
hgb_bag+graph, hgb_clock and oracle_risk+clock only cover night_val (720 rows).

Validation built in:
  * night_val predictions must equal the committed night_val eval files (written with float_format %.5g);
  * hgb_bag+graph+mem and edge_monitor_top3 are refit the same way and compared with the GNN team's
    __allsplits files on all held-out snapshots (that is what the GNN test look used).
Writes only to heldout/preds/regen/.
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np
import pandas as pd

B = "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad"
REPO = f"{B}/stat/repo/gnn_opt"
DATA = f"{B}/stat/data/night"
OUT = f"{B}/heldout/preds/regen"
PRE = f"{B}/heldout/preds/eval"
sys.path.insert(0, REPO)
import baselines as BL  # noqa: E402
import harness as H  # noqa: E402

os.makedirs(OUT, exist_ok=True)
D = H.load(DATA, graphs=True)
S, T = D["S"], D["T"]
T = T.assign(risk=S.risk.values)
sp = BL.specs(T)
sp["edge_monitor_top3"] = lambda: BL.EdgeMonitor(D, "top3")
y = S["y3"].values
snaps = S.snap.values
tr = H.train_rows(S, "y3").values
te = (S.split != H.TRAIN_SPLIT).values
print("train rows", tr.sum(), "positives", int(np.nansum(y[tr])), "| predicting", te.sum(), "snapshots")

names = sys.argv[1:] or ["hgb_bag+graph", "hgb_clock", "oracle_risk+clock", "hgb_bag+graph+mem", "edge_monitor_top3"]
for n in names:
    is_edge = n.startswith("edge_monitor")
    m = sp[n]()
    m = m.fit(snaps[tr], y[tr]) if is_edge else m.fit(T[tr], y[tr])
    p = m.predict(snaps[te]) if is_edge else m.predict(T[te])
    P = pd.DataFrame({"run": S.run[te].values, "round": S["round"][te].values, "score": p})
    P.to_csv(os.path.join(OUT, f"{n}.csv"), index=False, float_format="%.5g")
    # reload (so the comparison is on the same %.5g rounding as the committed files)
    P = pd.read_csv(os.path.join(OUT, f"{n}.csv"))
    ref_f = os.path.join(PRE, f"{n}.csv") if n in ("hgb_bag+graph", "hgb_clock", "oracle_risk+clock") else \
        os.path.join(PRE, f"{n}__allsplits.csv")
    R = pd.read_csv(ref_f)
    j = R.merge(P, on=["run", "round"], how="left", suffixes=("_ref", "_new"))
    d = (j.score_ref - j.score_new).abs()
    rel = d / np.maximum(j.score_ref.abs(), 1e-12)
    print(f"{n:22s} ref={os.path.basename(ref_f)} ref rows {len(R)} matched {j.score_new.notna().sum()} | "
          f"max|diff| {d.max():.3g}  max rel {rel.max():.3g}  exact-equal share {(d == 0).mean():.4f}")
