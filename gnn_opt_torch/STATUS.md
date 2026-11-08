# Who runs what (to avoid duplicate compute)

Cloud session (4 CPU, no GPU), branch gnn-opt-torch:
- [done] architecture screen on ID repeat 0 (5 folds): experiments/arch_id0.jsonl -> preds/cv/a_*__id0.csv
- [running] stage 2: top 5 architectures on all 18 folds (experiments/stage2.jsonl, b_*)
- [queued] stage 3 = LODO robustness on all 18 folds (experiments/stage3.jsonl, c_*) on the node-GRU base: crop=8,
  judge-swap augmentation, no edge readout, regularisation, 2nd seed; then judge-swap evaluation (j_*)
- FINDING (all 18 folds): GNNs win ID but lose LODO. b_gine_ggru select 0.804 (ID 0.886, LODO mean 0.830, worst
  0.696 = hold_K4); b_tf_ggru 0.800 (worst 0.708 nonboard); hgb_bag+graph+mem 0.848. On hold_K4 the GNN is fine in
  rounds 8-20 (0.79-0.82) and breaks after round 20 (0.61): late-episode dynamics learned on K2 do not transfer.
  Rank blend 0.3 GNN + 0.7 HGB: select 0.866 (ID 0.898, LODO mean 0.881, worst 0.818).
- FINDING 2 (all 18 folds): NODE-level GRU memory transfers much better than graph-level GRU memory.
  b_rgine_ngru (tmem=gru, gtemp=none): select 0.845, ID 0.852, LODO mean 0.868, worst 0.816 (hold_K4 0.816 vs
  0.70-0.76 for graph GRU). b_rgine_ggru 0.823. Logit blend 0.5 b_rgine_ngru + 0.5 hgb_bag+graph+mem:
  select 0.876 (ID 0.886, LODO mean 0.897, worst 0.845, R@5%FPR 0.541) = current best (preds/cv/h_ngru_hgb_logit55.csv).
  Suggestion for the Mac search: include tmem=gru / gtemp=none in the base, rank by the full-fold select score.
- PROPOSED SPLIT (cloud has 4 CPUs): Mac = search, seed ensembles, controls, feature ablations, final model.
  Cloud = LODO robustness (crop / judge-aug / reg / GNN+GBM hybrid), robustness targets (y5, yrel3), judge-swap
  evaluation, branch-arm analysis, DATA_REQUESTS.md. Cloud names: a_*, b_*, c_*, h_* (hybrid); log cv_log.jsonl.
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
