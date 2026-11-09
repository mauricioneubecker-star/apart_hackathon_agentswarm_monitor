import pandas as pd, ast, collections, sys
p = sys.argv[1]
d = pd.read_csv(p)
print("rows", len(d), "configs", d.cfg.nunique(), "tipped", int(d.tipped.sum()))
g = d.groupby('split').agg(configs=('cfg','nunique'), runs=('cfg','size'), tipped=('tipped','sum'))
print(g)
print("arms", d.arm.value_counts().to_dict())
print("branch tipped by arm", d[d.split=='night_branch'].groupby('arm').tipped.sum().to_dict())
print("rep values", d.rep.value_counts().to_dict())
print("repn by split", d.groupby(['split','repn']).size().to_dict())
un = d[~d.tipped]
print("untipped", len(un), "nv==0", (un.nv==0).sum(), "1-3", un.nv.between(1,3).sum(), "4-7", un.nv.between(4,7).sum(), "max", un.nv.max())
print("sum nv", d.nv.sum(), "sum nvu", d.nvu.sum(), "share", d.nvu.sum()/d.nv.sum())
print("att_only sum", d.att_only.sum(), "runs att_only>0", (d.att_only>0).sum())
rules = collections.Counter()
for r in d.rules:
    for k,v in ast.literal_eval(r).items(): rules[k]+=v
print("rules", dict(rules), "total", sum(rules.values()))
print("at_risk min/max/mean", d.at_risk.min(), d.at_risk.max(), round(d.at_risk.mean(),2))
print("tipped_rel", int(d.tipped_rel.sum()), "agree", int((d.tipped_rel==d.tipped).sum()))
t = d[d.tipped]
print("tipped nv median/mean/min/max", t.nv.median(), round(t.nv.mean(),2), t.nv.min(), t.nv.max())
print("tip_round median, q25, q75", t.tip_round.median(), t.tip_round.quantile(.25), t.tip_round.quantile(.75))
rel = t.tip_round - t.cut
print("tip - cut median/min/max/nunique", rel.median(), rel.min(), rel.max(), rel.nunique())
print("first_v median (tipped)", t.first_v.median(), " (all with v)", d.first_v.dropna().median())
print("first_v->theta median", (t.tip_round - t.first_v).median())
print("by cat", d.groupby('category').tipped.agg(['sum','size']).to_dict())
print("configs with any tip", d.groupby('cfg').tipped.any().sum())
print("msgs sum", d.msgs.sum(), "dur sum h", round(d.dur.sum()/3600,1))
print("n_dec describe", d.n_dec.describe().to_dict())
