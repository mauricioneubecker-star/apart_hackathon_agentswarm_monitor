# Independent recomputation of the night_vx evaluation

Six verifiers (own code, written from the definitions) and one critic checked the outputs of bb3f665d.
Full reports: audit_reports.json. Summary for the paper: analysis/results/vx.md.

| lens | all match | critical | minor |
|---|---|---|---|
| juryks | True | 0 | 1 |
| partB | True | 0 | 2 |
| outcomes | False | 0 | 1 |
| verdicts | True | 0 | 7 |
| partA | True | 0 | 5 |
| reading | True | 0 | 3 |

Critic: results trustworthy = True, critical issues: 0.

Main points: every point estimate matches to 4 decimals; with the run's seed every CI matches exactly; with other
seeds CI endpoints move by Monte Carlo error (up to 0.08 for topo time-matched). Seed-fragile 'CI excludes 0' calls
are listed in vx.md. The outcomes lens reports all_match = false only because of one own-seed CI gap (H2 censored
clock, time-matched lower bound); its points and same-seed CIs match.

Summary check of the German write-up (vx.md, FINDINGS.md): summary_check.json (2 lenses: numbers, claims).
All must-fix and should-fix items were applied before the commit. Post-hoc numbers: analysis/vx_posthoc.py.
