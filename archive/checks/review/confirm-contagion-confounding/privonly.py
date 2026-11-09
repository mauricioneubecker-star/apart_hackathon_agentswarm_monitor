"""Reviewer-style contrast: privately exposed vs NOT exposed at all (rows exposed only via the other route dropped)."""
import sys, numpy as np
sys.argv = [sys.argv[0], sys.argv[1]]
exec(open(__file__.rsplit("/", 1)[0] + "/extra.py").read().split("ALL = np.ones")[0])
B, K2, K4 = chan == "board", cat == "K2", cat == "K4"
Ed, Ep, Eu = Z["E_dir"], Z["E_dir_priv"], Z["E_dir_pub"]
Pd, Pp = Z["P_dir"], Z["P_dir_priv"]
for g, m in (("board", B), ("K4&board", K4 & B), ("K2&board", K2 & B), ("non-board", ~B)):
    keepE = m & ~((Ed == 1) & (Ep == 0))
    keepP = m & ~((Pd == 1) & (Pp == 0))
    print(f"{g:10s} E_priv vs unexposed: {summ(mh(keepE, Ep))} | dm>0 {summ(mh(keepE & (DM == 1), Ep))}")
    print(f"{g:10s} P_priv vs unexposed: {summ(mh(keepP, Pp))} | dm>0 {summ(mh(keepP & (DM == 1), Pp))}")
