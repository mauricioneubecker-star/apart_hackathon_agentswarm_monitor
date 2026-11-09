## Editor notes

**Word counts.** I counted with `wc`, including headings and list markers, before a final round of sentence splitting. The splits added a few words in the Introduction, Methods and Results, so recount before submission. Tables, captions and the back matter are not counted.

| Section | Words | Budget |
|---|---|---|
| Abstract (unchanged) | 200; about 191 once the two H7 placeholders are filled | 200 |
| 1 Introduction | 452 | 500 |
| 2 Related Work | 153 | 180 |
| 3 Methods | 1,159 (3.1: 228, 3.2: 180, 3.3: 112, 3.4: 214, 3.5: 422) | 950 |
| 4 Results | 892 (4.1: 222, 4.2: 172, 4.3: 141, 4.4: 354) | 1,000 |
| 5 Discussion and Limitations | 265 | 300 |
| 6 Conclusion | 69 | 70 |
| **Main text** | **≈2,990** | **3,000** |

- Methods is over its guide because it holds the exact H7 design (about 140 words) and the designs of the held-out comparison and the validation suite. The Introduction, Results and Discussion are under their guides to make up for it.
- The paper has 4 tables (5, 5, 9 and 6 rows; Table 3 has 5 numeric columns) and 1 figure placeholder.

**Remaining placeholders.**
- Abstract and §1 item 4: [[H7: n of 28 planned]] and [[H7: D = X [L, U]; supported / not supported / open]].
- §4.4:
  - [[H7: n of 28 runs and c of 14 configurations evaluated; tipped runs; executions]] (take these from the run log, including the number of executions and, if there was more than one, whether the outputs are byte-identical);
  - [[H7: D = X [L, U]]] and [[H7: supported / not supported / open]];
  - [[H7: time-matched D, global_full − hybrid, pairwise − GNN]];
  - [[H7: 12 predictors]] (the descriptive AUROCs that addendum 3, item 6 promises).
- §5 and §6: [[H7: D = X [L, U]; supported / not supported / open]].
- [[TODO: data link]], [[team: who did what]] and [[team: state what each member verified by hand …]].
- References: BlindGuard, XG-Guard and Holm (1979) are marked [verify].

**Must-fix items not applied as written.**
- **No Appendix (editorial #2, #3, #5(iii)).**
  - To stay within 6–7 pages, I deleted the material that was to move to an appendix instead of moving it: pilot details, LLM-monitor variants, GNN details, fine-tune details, per-arm night_vx results and the synthetic testbed.
  - The dangling [[Appendix ref]] is gone. Author contributions and References were added.
- **Introduction (editorial #6(d)):** I dropped the closing paragraph; the hard part and the open question about larger teams now appear in §5, §6 and the Limitations.
- **Cross-validation (editorial #5(iii)C):** I dropped the two cross-validation sentences of §4.2. Cross-validation remains only in §4.3 and the Limitations.
- **H7 and §5 wording (editorial #7, #8, #22; claims #12, #13):**
  - The H7 design is stated once, compressed, in §3.5. The motivation is in §4.4 and the commit hash in Code and Data.
  - The §5 paragraphs are shorter versions, not verbatim. The untested "enough time to pause an agent" claim is removed, and "Replicate noise" is merged into "The hard part".
- **Deleted instead of reworded:**
  - the horizon sentence (numbers #5; the Limitations bullet uses the corrected wording);
  - the 91% repair sentence (numbers #12);
  - the message-rate comparison (numbers #13);
  - the GLM base-rate sentence (claims #4);
  - the "0 of 96" sentence in §5 (claims #10);
  - the judge swap (numbers #6; so no claim about held-out repetition remains);
  - the stuck-agent rates (editorial #20);
  - the structure-only baseline (editorial #14; with it gone, it needs no definition).
- **Decoy counts (numbers #4, claims #18):** the text uses the committed design facts (DECISIONS.md §5, index.csv). `decoy.py` and `stuck_rates.py` are committed in 896d7099 under `analysis/review/storyline-check/scripts/`, so the 280-vs-26 decoy count and the 43.5%-vs-3.1% stuck rates could be cited if space allows.
- **Table 3:**
  - IQRs are dropped, and the count-head MAE and the AUROC before the shortcut's first announcement are in the caption.
  - Recall at 5% FPR is dropped to keep 5 numeric columns. ANALYSIS_PLAN §4 lists recall among the metrics to report alongside AUROC, so restore it if a column frees up.
- **Table 4:** the GLM-arm columns are replaced by night_vx rep0/rep1 and the range over the four shifted arms (sources: vx.md block table; FINDINGS "Spanne in den 4 Armen").
- **References no longer cited and therefore dropped:** Hines et al. (2024), Cemri et al. (2025), Xu et al. (2019) and the Hugging Face entry.