import sys, numpy as np
sys.argv = [sys.argv[0], "rows_w3.npz"]
exec(open("extra.py").read().split("ALL = np.ones")[0])
px = {tuple(l.split()[1:3]) for l in open("proxy_list.txt")}
drop = np.array([(r, a) in px for r, a in zip(run, Z["agent"])])
K2, B = cat == "K2", chan == "board"
for nm, m in (("K2&board", K2 & B), ("K2&board w/o proxy beneficiaries", K2 & B & ~drop), ("K2", K2), ("K2 w/o proxy", K2 & ~drop)):
    print(f"{nm:34s} E_dir all {summ(mh(m, Z['E_dir']))} | dm>0 {summ(mh(m & (DM == 1), Z['E_dir']))}")
