# gnn_opt_torch: design notes

## Input compliance (headline model)
Loaded via `tdata.Data(feat_mode="headline")` = exactly `schema.json: headline_edge + headline_node` of the shared
harness:
- edges (18): volume, direct_volume, bcast_volume, responsiveness, reciprocity, new_contact, rule_legitimization,
  success_claim, workaround_request, uncritical_adoption, verification, goal_shift, unverified_authority, secrecy,
  frustration, legitimization_trend, jury_disagreement, escalation_lex; plus missing flags for responsiveness and
  reciprocity (NaN when there is no direct message in the window), and the relation type (direct / broadcast / both,
  derived from direct_volume and bcast_volume > 0).
- nodes (5): unanswered_share, role_external, bcast_legitimization, stance_drift, frustration_own; plus missing
  flags for unanswered_share, stance_drift and frustration_own.
- Never: round / t / round_frac, episode length, config parameters, role_lead, role_auditor, n_deps, n_dependents,
  model identity, instructed flags, solvability, violation events, merge-feed CI state, labels. Labels (y3, y5,
  yrel3, risk, node labels) are only used as training targets.
- Ablations: `feat="+lex"` (mech_ref, mech_ref_ema, pressure_lex, bcast_mech_ref, exposure_breadth), `"+tool"`,
  `clock=True` (round/30 as a node feature), stages `S0`..`S3`.

Normalisation statistics are fit on the training runs of each fold only.

## Time and memory
The graph-level temporal block (causal GRU over the run's snapshots) and the optional node-level GRU only look
back in time (causal), so the monitor is usable online. A recurrent model can in principle count rounds (an implicit
clock). We therefore (i) report time-matched AUROC (within round bins), (ii) compare against windowed temporal
blocks (`conv3`, `conv5`, `attn8`) that cannot see further back than K rounds, and (iii) report the clock ablation.

## Folds
`gnn_opt/folds.json` (shared): 2x5 grouped-by-config ID folds + 8 LODO folds, training on night_train only.
Selection score = mean(ID pooled AUROC, LODO mean, LODO worst) as in the harness.
