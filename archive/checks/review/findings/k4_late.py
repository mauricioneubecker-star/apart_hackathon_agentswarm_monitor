import pandas as pd, numpy as np
from sklearn.metrics import roc_auc_score
SC="/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad"
S=pd.read_csv(f"{SC}/gnnopt_data/night/snapshots.csv",low_memory=False)
S=S[(S['eval']==1)&S.y3.notna()][["run","round","y3"]]
files={"b_gine_ggru":f"{SC}/verify/findings/torch_cv/b_gine_ggru.csv","final":f"{SC}/verify/findings/torch_cv/final.csv",
"e_ngru_4runs":f"{SC}/verify/findings/torch_cv/e_ngru_4runs.csv","hgb_bag+graph+mem":f"{SC}/gnnopt_code/gnn_opt/preds/cv/hgb_bag+graph+mem.csv"}
for n,p in files.items():
    P=pd.read_csv(p); P=P[P.fold=="hold_K4"].merge(S,on=["run","round"])
    out=[]
    for lo,hi in [(1,7),(8,20),(21,30)]:
        g=P[(P["round"]>=lo)&(P["round"]<=hi)]
        a=roc_auc_score(g.y3,g.score) if g.y3.nunique()==2 else float('nan')
        out.append(f"r{lo}-{hi}: {a:.3f} (n={len(g)}, pos={int(g.y3.sum())})")
    print(f"{n:20s} all {roc_auc_score(P.y3,P.score):.3f} | "+" | ".join(out))
