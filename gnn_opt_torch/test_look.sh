#!/bin/bash
# The ONE scripted test look (counted in LOOKS.md). Models frozen beforehand on CV; nothing is tuned from this.
# Writes gnn_opt_torch/results/test_look1/*.txt (+ CSV tables).
set -e
cd "$(dirname "$0")/.."
O=gnn_opt_torch/results/test_look1; mkdir -p $O
E=gnn_opt_torch/preds/eval; C=gnn_opt_torch/preds/cv; B=gnn_opt/preds/cv
SPL=night_test_id,night_test_ood_family,night_test_ood_seed,night_branch
P="$E/final.csv $E/final_gnn.csv $E/hgb_bag+graph+mem__allsplits.csv $E/edge_monitor_top3__allsplits.csv"
TH="$C/final.csv $C/final_gnn.csv $B/hgb_bag+graph+mem.csv $B/edge_monitor_top3.csv"
N=hybrid,gnn5,hgb,edge_top3
python3 gnn_opt/evaluate.py --data gnn_opt_data/night --splits $SPL --preds $P --thr-from $TH --names $N --pairs \
    --out $O/y3.csv > $O/y3.txt 2>&1
for t in y5 yrel3; do
  python3 gnn_opt_torch/eval_target.py --target $t --data gnn_opt_data/night --splits $SPL --preds $P --names $N \
      --out $O/$t.csv > $O/$t.txt 2>&1
done
# judge swap: the frozen models applied to single-judge features (DeepSeek only / Haiku only)
for j in night_ds night_hk; do
  python3 gnn_opt/evaluate.py --data gnn_opt_data/$j --splits $SPL \
      --preds $E/final__$j.csv $E/final_gnn__$j.csv $E/hgb_bag+graph+mem__$j.csv --names hybrid_$j,gnn5_$j,hgb_$j \
      --thr-from $C/final.csv $C/final_gnn.csv $B/hgb_bag+graph+mem.csv --out $O/judge_$j.csv > $O/judge_$j.txt 2>&1
done
echo done
