# Fine-tune canary: could a format repair have saved Part C? (exploratory)

Source: `runs_vx/core-night_vx-K2-002-ft4/rep0/llm_calls.jsonl`. Mechanical repair only: first JSON object, or close the open string and brackets; no character of content is changed.

| model | calls | invalid | rescued by repair (of them cut off) | valid after repair | turns with a message (valid) | repaired turns with a message |
|---|---|---|---|---|---|---|
| qwen3.5-397b | 125 | 5 (4%) | 2 (1) | 98% | 21/120 (18%) | 1 |
| qwen3.5-4b-ft | 490 | 217 (44%) | 171 (15) | 91% | 6/273 (2%) | 0 |
| qwen3.8-27b | 250 | 14 (6%) | 11 (2) | 99% | 44/236 (19%) | 2 |
