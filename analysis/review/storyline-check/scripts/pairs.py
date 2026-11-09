import sys, pandas as pd
df = pd.read_csv(sys.argv[1])
print("runs", len(df), "configs", df.cfg.nunique(), "tipped", int(df.tipped.sum()))
print(df.groupby('split').agg(runs=('cfg','size'), cfgs=('cfg','nunique'), tipped=('tipped','sum')))
# mixed configs (any tipped and any untipped run)
g = df.groupby('cfg').tipped.agg(['sum','size'])
mixed = g[(g['sum']>0)&(g['sum']<g['size'])]
print("mixed configs overall:", len(mixed))
print(df[df.cfg.isin(mixed.index)].groupby('split').cfg.nunique())
for off in [6]:
    d = df.copy()
    d['prefix'] = d['cut'] - off
    alive = d[(~d.tipped) | (d.tip_round > d.prefix)]
    tot = 0; rows=[]
    for cfg, gg in alive.groupby('cfg'):
        nt = int(gg.tipped.sum()); nu = int((~gg.tipped).sum())
        if nt>0 and nu>0:
            tot += nt*nu; rows.append((cfg, gg.split.iloc[0], nt, nu))
    print("offset", off, "pairs", tot, "configs", len(rows))
    print(pd.DataFrame(rows, columns=['cfg','split','nt','nu']).groupby('split').agg(cfgs=('cfg','size'), pairs=('nt', lambda s: None)))
    r = pd.DataFrame(rows, columns=['cfg','split','nt','nu']); r['pairs']=r.nt*r.nu
    print(r.groupby('split').agg(cfgs=('cfg','size'), pairs=('pairs','sum')))
