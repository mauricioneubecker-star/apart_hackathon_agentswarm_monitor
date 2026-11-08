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

Local Mac session (12 CPU: 8P+4E, MPS), worktree of gnn-opt-torch, started 2026-11-08 ~12:00 UTC:
- [done] screen on ID repeat 0: experiments/screen_id0.jsonl -> preds/cv/s_*.csv, summaries in preds/screen_log.jsonl
  (25 configs incl. 3 seeds of the base; see RESULTS.md)
- [next] search (successive halving, search.py) -> preds/cv/rs*_*.csv, preds/search_log.jsonl; then top-3 seed
  ensembles / SWA / augmentation (m_*), controls + ablations (m_ctl_*, m_abl_*), blend, final model
- Mac logs: preds/screen_log.jsonl, preds/search_log.jsonl, preds/mac_log.jsonl (never cv_log.jsonl)
- night_val looks: 0. Test-split looks: 0.
