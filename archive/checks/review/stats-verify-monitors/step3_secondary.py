"""Secondary: GNN controls/ablations (id0, seed 0) vs matched m_noer id0; seed-noise floor; seed-aware CI."""
import json, sys
import numpy as np
from scipy.stats import t as tdist
sys.path.insert(0, "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/stat/verify-monitors")
import vlib as L

S, lab, cfgs = L.load_rows(); nC = len(cfgs); y = lab.y.values

def id0(f):
    d = L.cv_scores(f"{L.GIT}/{f}.csv", lab)
    s = d["rep"]["id0"]; assert not np.isnan(s).any(), f
    return s

ref = id0("m_noer"); ref_s1 = id0("m_noer__s1")
print("m_noer id0 folds == m_noer__s1 id0 folds:", float(np.max(np.abs(ref - ref_s1))))
names = {"rewire": "m_ctl_rewire__id0", "shuffle_ef": "m_ctl_shuffle_ef__id0", "shuffle_labels": "m_ctl_shuffle_labels__id0",
         "shuffle_rows": "m_ctl_shuffle_rows__id0", "+clock": "m_abl_clock__id0", "+lex": "m_abl_lex__id0",
         "S2": "m_abl_S2__id0", "S1": "m_abl_S1__id0", "S0": "m_abl_S0__id0"}
sc = {k: id0(v) for k, v in names.items()}
seedf = {"s_base": id0("s_base"), "s_base_r1": id0("s_base_r1"), "s_base_r2": id0("s_base_r2"),
         "swa": id0("m_noer_swa"), "swa_s1": id0("m_noer_swa_s1"), "tg": id0("m_tmemgru"), "tg_s1": id0("m_tmemgru_s1")}
K = L.draws(nC, 10000, 8675309); one = np.ones((1, nC))
Pr = L.Pred(ref, lab, nC)
ra, rb = Pr.auroc(one)[0], Pr.auroc(K); rt, rtb = Pr.tauroc(one)[0], Pr.tauroc(K)
print(f"m_noer id0: AUROC {ra:.3f} [{np.quantile(rb, .025):.3f}, {np.quantile(rb, .975):.3f}]  tAUROC {rt:.3f}")
# seed noise floor
A = {k: L.mw_auc(y, v) for k, v in seedf.items()}
trio = np.array([A["s_base"], A["s_base_r1"], A["s_base_r2"]])
ss = ((trio - trio.mean()) ** 2).sum() + (A["swa"] - A["swa_s1"]) ** 2 / 2 + (A["tg"] - A["tg_s1"]) ** 2 / 2
sig = np.sqrt(ss / 4)
print("id0 AUROCs:", {k: round(v, 4) for k, v in A.items()})
print(f"pooled sigma_seed (4 df) = {sig:.4f}; 95% band for a difference = +-{tdist.ppf(.975, 4) * np.sqrt(2) * sig:.4f}; "
      f"max |seed diff| = {max(abs(trio[0]-trio[1]), abs(trio[0]-trio[2]), abs(trio[1]-trio[2]), abs(A['swa']-A['swa_s1']), abs(A['tg']-A['tg_s1'])):.4f}")
print("\n variant          AUROC   dAUROC [95% CI]            p       seed-aware CI           | tAUROC  dtAUROC [95% CI]           p")
for k, s in sc.items():
    P = L.Pred(s, lab, nC)
    a, ab = P.auroc(one)[0], P.auroc(K); tt, tb = P.tauroc(one)[0], P.tauroc(K)
    d = ab - rb; dt = tb - rtb
    se = np.std(d); sa = (a - ra - 1.96 * np.sqrt(se ** 2 + 2 * sig ** 2), a - ra + 1.96 * np.sqrt(se ** 2 + 2 * sig ** 2))
    print(f" {k:15s} {a:.3f}  {a - ra:+.3f} [{np.quantile(d, .025):+.3f}, {np.quantile(d, .975):+.3f}]  p={L.pboot(d):.4f}  "
          f"[{sa[0]:+.3f}, {sa[1]:+.3f}]  | {tt:.3f}  {tt - rt:+.3f} [{np.quantile(dt, .025):+.3f}, {np.quantile(dt, .975):+.3f}]  p={L.pboot(dt):.4f}")
s = sc["shuffle_rows"]; P = L.Pred(s, lab, nC); b = P.auroc(K)
print(f"\nshuffle_rows AUROC CI [{np.quantile(b, .025):.3f}, {np.quantile(b, .975):.3f}] (contains 0.5?)")
