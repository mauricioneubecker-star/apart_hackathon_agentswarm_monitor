import sys
import numpy as np, pandas as pd
V = sys.argv[1]
W = sys.argv[2] if len(sys.argv) > 2 else "3"
df = pd.read_csv(f"{V}/out/orig_rows_w{W}.csv") if W == "3" else pd.read_csv(f"{V}/out/indep_w{W}_rows.csv.gz")
def per_cfg(sub, x, extra=()):
    g = sub.assign(a=(sub[x]==1)&(sub.Y==1), b=(sub[x]==1)&(sub.Y==0), c=(sub[x]==0)&(sub.Y==1), d=(sub[x]==0)&(sub.Y==0))
    s = g.groupby(["cfg","run","t","stuck",*extra])[["a","b","c","d"]].sum()
    n = s.sum(axis=1)
    s = s.assign(orn=s.a*s.d/n, ord=s.b*s.c/n, rrn=s.a*(s.c+s.d)/n, rrd=s.c*(s.a+s.b)/n,
                 inf=((s.a+s.b)>0)&((s.c+s.d)>0)&((s.a+s.c)>0))
    return s[s.inf].groupby(level="cfg")[["orn","ord","rrn","rrd","a"]].sum(), int(s.inf.sum())
def summ(sub, x, extra=(), nboot=2000):
    P, ns = per_cfg(sub, x, extra)
    M = P[["orn","ord"]].values
    rng = np.random.default_rng(0)
    bo = []
    for _ in range(nboot):
        Wm = M[rng.integers(0, len(M), len(M))]
        if Wm[:,1].sum() > 0: bo.append(Wm[:,0].sum()/Wm[:,1].sum())
    return f"OR {M[:,0].sum()/M[:,1].sum():.2f} [{np.percentile(bo,2.5):.2f}; {np.percentile(bo,97.5):.2f}] cfgs {len(M)} strata {ns} exp.adopt {int(P.a.sum())}"
dm = df[df.dm==1]
print(f"--- window {W}")
print("as reported (dm>0)            P_dir:", summ(dm, "P_dir"))
print("dm>0 & E_dir==0               P_dir:", summ(dm[dm.E_dir==0], "P_dir"))
print("dm>0, strata += E_dir         P_dir:", summ(dm, "P_dir", ("E_dir",)))
print("as reported (dm>0)            E_dir:", summ(dm, "E_dir"))
print("dm>0 & P_dir==0               E_dir:", summ(dm[dm.P_dir==0], "E_dir"))
print("dm>0, strata += P_dir         E_dir:", summ(dm, "E_dir", ("P_dir",)))
print("all rows, strata += E_dir     P_dir:", summ(df, "P_dir", ("E_dir",)))
print("all rows, strata += dm        P_dir:", summ(df, "P_dir", ("dm",)))
print("all rows, strata += dm        E_dir:", summ(df, "E_dir", ("dm",)))
c = dm.groupby(["P_dir","E_dir"]).Y.agg(["size","sum","mean"])
print("dm>0 crude adoption by (P_dir,E_dir):"); print(c.to_string())
