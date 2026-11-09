# Pre-evaluation audit of the night_vx inputs

Six independent agents (one lens each) and one completeness critic checked analysis/vx_preds/ and Nachtrag 2
before the evaluation. On night_vx they used only random scores or label counts that were already public.
Full reports: audit_reports.json. How each finding was handled: ANALYSIS_PLAN.md Nachtrag 2.

| lens | verdict | blocking | minor |
|---|---|---|---|
| thresholds | ok | 0 | 4 |
| baselines-hybrid | ok | 0 | 5 |
| gnn-provenance | issues | 1 | 8 |
| plan-conformance | issues | 3 | 10 |
| vx-eval-code | issues | 0 | 7 |
| coverage-splits | ok | 0 | 4 |

Blocking findings (all fixed before the commit of the inputs):

- gnn-provenance: Nachtrag 2 item 3 gets the freeze timing wrong: cloud_final_gnn.pt was changed after the test look (metadata only)
- plan-conformance: The pre-registration package is not committed yet, and two new scripts are not mentioned in Nachtrag 2
- plan-conformance: Nachtrag 2.3 makes a false timeline claim about when the GNN was frozen
- plan-conformance: H4 (ii) changes the committed false-alarm definition without saying so

Critic: GO for analysis/vx_preds/run_eval.sh, but only after these steps, in this order. (1) Regenerate run_eval.sh in place with the current assemble.py and the same inputs. Re-hash and confirm that the 12 preds files, 2 snap files, thresholds.json and manifest.json match /private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/audit/critic/audited_hashes_now.txt and that only run_eval.sh changed. I showed in scratch that this holds, and that the new pipeline runs end to end on random scores. (2) Text fixes in Nachtrag 2; no …
