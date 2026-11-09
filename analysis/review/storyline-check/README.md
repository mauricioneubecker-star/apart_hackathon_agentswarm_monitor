# Storyline fact-check (9 Nov, 07:58-09:30)

Workflow `storyline-factcheck` (13 AI agents: 6 checkers, 6 adversarial reviewers, 1 synthesis) checked every claim of
the paper storyline the user proposed on 9 Nov against all committed sources on all branches.

- `../../../paper/STORYLINE_CHECK.md`: the synthesis (claim table, a storyline the data support, numbers for the paper
  with sources, open problems, German summary).
- `claims.json`: raw checker and reviewer outputs per claim group.
- `scripts/`: helper scripts the agents wrote to recount numbers from committed data (paths point to the session
  scratch directory; they read committed files only). Numbers in the synthesis that come from these scripts are
  descriptive counts, not part of any pre-registered analysis.
