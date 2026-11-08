# Who runs what (to avoid duplicate compute)

Cloud session (4 CPU, no GPU), branch gnn-opt-torch:
- [done] architecture screen on ID repeat 0 (5 folds): experiments/arch_id0.jsonl -> preds/cv/a_*__id0.csv
- [running] stage 2: top 5 architectures on all 18 folds (experiments/stage2.jsonl, b_*)
- [queued] stage 3: training tricks on GINE+GRU (experiments/stage3.jsonl, c_*)
- [later] training-trick / multi-task / augmentation ablations,
  random search (successive halving), controls (rewire, shuffle_ef, shuffle_labels), feature ablations
- night_val looks: 0 so far. Test-split looks: 0 so far.
Results log: preds/cv_log.jsonl (one JSON line per finished config).
If you run experiments elsewhere, please write to a different name prefix (e.g. mac_*) and note them here.
