# Storyline fact-check: final verdicts, a storyline the data support, and the numbers for the paper

**Source state.** Unless a row says otherwise, everything is checked against origin/night-vx-validation at `5c898faf` (9 Nov, 08:53 CET), which is also the worktree HEAD. FINDINGS.md line numbers refer to that commit; checker lines taken from `db0bd30a` or `8cde21e3` have been corrected. **H7** (Nachtrag 3, runs_vx3) has no result yet and is not used anywhere below.

**Branch keys:**
- **nvv**: night-vx-validation
- **got**: gnn-opt-torch
- **go**: gnn-opt
- **gs**: gnn-swarm (`gnn/RESULTS_amongus.md` is the same blob, `66af8cf3`, on gnn-pipeline)
- **cs**: cloud-synthesis
- **main**: main

**Evidence kinds:**
- **PRE**: pre-registered
- **HO**: held-out test, pre-specified primary family (confirmatory, not blind)
- **HO-sec**: held-out, secondary and uncorrected
- **CV**: night_train cross-validation. The plan treats it as descriptive only (ANALYSIS_PLAN.md:72-73), and the GNN was selected on these same rows.
- **EXP**: exploratory or post hoc
- **PIL**: pilot
- **DES**: design fact or descriptive count
- **LIT**: literature claim

**FINDINGS "Verworfen" entries (FINDINGS.md:380-392):**
- **VW1** (380-381): "a DM from a rule-breaker roughly doubles adoption" stated in general
- **VW2** (382-383): a null placebo proves real contagion
- **VW3** (384-385): a single message changes the course causally
- **VW4** (386): sanctions do not lower tipping
- **VW5** (387-388): the best model is GNN + gradient boosting
- **VW6** (389-390): replicate noise is small
- **VW7** (391-392): the validation detects drops > 0.1 AUROC

---

## 1. Claim table

### 1a. Framework and dataset

| ID | Claim (short) | Final verdict | What the data say | Paper wording or "drop" | Source |
|---|---|---|---|---|---|
| F1a | "Testing this needs data that did not exist" | LIT, cannot be checked in the repo | No committed source surveys earlier data. The project's own second domain uses an existing labelled multi-agent LLM corpus (AmongUs-X, 1,831 games), so any novelty claim has to be limited to collective rule-breaking (none). | "To our knowledge, no public dataset records teams of LLM agents in which collective rule-breaking sometimes happens and sometimes does not, with per-agent, per-round ground truth. We therefore built one." | nvv sim_dataset/VALIDATION.md:44; gs gnn/RESULTS_amongus.md:3 |
| F1b | Framework yields "realistic" swarms that tip and swarms that stay within the rules | Supported with changes | 101 of 252 runs tipped and 151 did not. Of those 151, only 53 had zero violators (59 had 1–3, 39 had 4–7). The batch was calibrated towards tipping (high pressure in all 112 configs, release freeze in 79) and was never compared with real teams (DES). | "It produces teams that tip and teams that do not (101 vs. 151 of 252 runs; 53 without any violation). The batch is calibrated towards tipping, so its rate does not estimate real-world prevalence." Drop "realistic". | nvv runs_night/_logs/analysis_runs.csv (recounted); analysis/review/stats-factors/REPORT.md:21-22; sim_dataset/DECISIONS.md:515-523; FINDINGS.md:272 |
| F1c | Exact labels from tool logs | Supported with changes | Labels are deterministic rules applied to logged tool events: 1,720 violation events (655 scoring-file writes, 1,062 skip-checks merges, 3 green-impossible) from 1,514 violators. 740 agents with only blocked attempts are logged but not counted. Instructed seeds count toward θ (DES). | "Labels are computed deterministically from the tool-event log: an agent counts as violating from its first successful write to `.ci/scoring.toml` (K2) or its first merge with `skip_checks=true` (K4). No human or LLM annotation enters the label; blocked attempts are logged but not counted." | nvv sim_dataset/runner/labels.py:1-8,124-165; generator/engine.py:184-205,403-421; sum over runs_night/*/meta.json = 1,720 (recomputed) |
| F2a | "First labelled dataset of swarm tipping at this scale" | LIT, cannot be checked in the repo | The size facts check out (F2b). "First" and "at this scale" need a related-work check (none). | "To our knowledge, the first labelled dataset of collective rule-breaking in teams of LLM agents (252 runs of 24 agents, with per-agent, per-round ground truth)." | nvv FINDINGS.md:43 |
| F2b | 252 runs, 24-agent teams, 112 configurations | Supported | 236 control runs plus 16 fork continuations in 112 configs, 30 rounds each. That gives 7,560 snapshots and 6,388 distinct prediction rows (303 positive). There were 188,402 logged agent calls, 7,832 of them format retries, so about 180k agent turns, and 21,605 agent-written messages, all jury-scored (DES; my sums over committed meta.json). | "252 runs of 24-agent teams, 30 rounds each, in 112 configurations: 236 control runs plus 16 counterfactual continuations that share their first five rounds with a control run (7,560 labelled snapshots; about 180,000 agent turns; 21,605 agent-written messages)." | nvv FINDINGS.md:43; stats-factors/REPORT.md:21-23; stats-monitors/REPORT.md:17; runs_night/*/rep*/meta.json |
| F2c | "Four open models" | Supported with changes | qwen3.8-27b and gemma-4-31b-it (dense), qwen3.5-397b and gemma-4-26b-a4b-it (MoE), served through a hosted API at temperature 0.7 with reasoning off. The repo never documents them as "open(-weight)" (DES). | "Agents run on four models from the Qwen and Gemma families (two dense, two mixture-of-experts), with reasoning switched off and temperature 0.7." Write "open-weight" only with model-card citations. | nvv sim_dataset/generator/config.py:37-47; README.md:205-211 |
| F2d | Paired counterfactual forks | Supported with changes | 8 configs with seed type none were forked after round 5 into control, injected QA-bot instruction and one-off fake-manager arms (24 runs, prefixes hash-identical). In the 4 peers-only fork configs one agent knows the mechanism (I checked `flags.info_asym` in the scenario files), so "without any seed" is wrong for half of them (DES). | "In eight configurations without an instructed agent or external message (in four of them one agent knows how the shortcut works), each episode was copied after round 5 and continued three ways: unchanged, with an injected QA-bot instruction, or with a one-off fake-manager message." | nvv analysis/results/contagion.md:101-107; dataset/scenarios/core/core-night_branch-{K2-002,K2-005,K4-000,K4-007}.json; generator/scenario.py:349-351 |
| F3a | Most agents get no instruction | Supported with changes | At most one agent per run is instructed (95 of 6,048 agent-runs, 1.6%), and 1,453 of 1,514 violators (96.0%) were never instructed. Still, 232 of 252 runs had some seed, and only 11 of the 101 tipped runs had none (DES). | "At most one of the 24 agents is told to use or promote the shortcut, and 96% of the 1,514 rule-breakers were never instructed. Seeding is still common: only 11 of the 101 tipped runs had no instructed agent, informed agent or outside message." | nvv FINDINGS.md:52-53; analysis_runs.csv (nv, nvu); generator/scenario.py:349-351 |
| F3b | Labels from tool logs, not from a judge | Supported | The label code reads violation events only. The jury produces only input features and two analysis-only quantities (DES). | "Labels come from the tool-event log, not from an LLM judge; the two-judge jury only produces input features for some monitors." | nvv sim_dataset/runner/labels.py:1-29,124-165; README.md:298 |
| F3c | Leakage controls stop a classifier learning the generator | Supported with changes | Paraphrase pools and decoys exist: 280 decoy notices vs 26 attack events in the final batch, all attack texts distinct (my count from committed scenarios). TF-IDF on non-attack text gives AUROC 0.481 ± 0.029 and Cramér's V ≤ 0.088, but only on the unsimulated v1.1 design. Setup-level signal remains: factor-only grouped-CV AUROC 0.82 (DES / static check). | "We took several steps to reduce the risk that classifiers learn the generator's templates instead of agent behaviour … The text checks were run on the generator's design and not repeated on the final batch, and configuration factors alone still predict tipping (grouped-CV AUROC 0.82), so we also report within-configuration comparisons." Replace "stop" with "reduce the risk". | nvv DECISIONS.md:53-61; README.md:191-194; dataset/reports/validation_full_full_reserve_pioneer_backbone_glm.json; generator/validate.py:269-286; VALIDATION.md:34,61 |
| F4a | The models first did not tip (pilot history) | Supported | 4 pilots with 124 runs. The first three (96 runs) never reached the threshold: pilot 1 had one violation in 30 episodes, and pilot 3's largest cascade had 5 violators. Pilot 4 tipped 5 of 28 runs, from 3 configs (PIL). | "Producing tipping took four pilots (124 runs). In the first three (96 runs) no team reached the threshold; tipping first appeared in pilot 4 (5 of 28 runs, from three configurations)." | nvv DECISIONS.md:169,269-273,350-352,446-447; committed labels.json (runs/, runs_pilot2/3 on nvv; runs_pilot4 on main) |
| F4b | "Well-aligned models first refused to tip" | Not supported as worded | Alignment was never measured. The explicit refuse action was used 0 times in 124 pilot runs and 5 times in 252 final runs. Agents waited, escalated, cited the ownership rules, or tried to edit the protected tests (22 agents in pilot 1; 108 rejected edits in pilot 4). A bug hid skip_checks from K4 seeds (PIL; refuse counts EXP from committed event logs). | "The agents did not refuse; they waited for QA, escalated, cited the ownership rules or tried to edit the protected tests. Part of the early null result came from environment problems that we then fixed." Drop "well-aligned" and "refused". | nvv DECISIONS.md:177-182,465; generator/texts.py:224-227; scenario.py:636-639 |
| F4c | "That makes the framework a result in itself" | Supported with changes (as calibration lessons only) | In pilot 4: freeze 5/14 vs 0/14 tipped; with 6 unsolvable tickets, at most 5 violators; K2 spread even without a feed. In the final batch, configs without a freeze still tipped (20.2% vs 46.2%, Holm 0.053), so these are tendencies, not requirements (PIL + EXP). | "We report the calibration history because it is informative: tipping appeared only after we blocked the legitimate exit, made adoptions visible and raised the number of stuck agents (small, confounded pilots). In the final batch these were tendencies, not requirements." | nvv DECISIONS.md:452-454,480,485; stats-factors/REPORT.md:9,17,52 |
| F4d | Pilots 1–5 | Contradicted | Pilot 5 was designed but never run ("Kein separater Pilot-5-Lauf"). Its levers became settings or factors of the main batch (DES). | "We ran four pilots; a fifth design was not run on its own, and its levers became settings or factors of the main batch." | nvv DECISIONS.md:499-503,515-523 |
| F5a | It has tipping and non-tipping runs | Supported | Every split contains both outcomes (101 vs 151 overall). But only 15 of 104 configs with repeated runs had mixed outcomes (ICC 0.73) (DES). | "Every split contains both outcomes, but outcomes are largely set by the configuration: only 15 of 104 configurations with repeated runs had mixed outcomes." | nvv stats-factors/REPORT.md:25-32,36; VALIDATION.md:34 |
| F5b | Paired forks "for cause and effect" | Supported with changes (EXP). Matches VW3 if read as "one message causes". | The injected persistent instruction gave +4.5 new violators [1.0, 8.0] (Holm p = 0.06). The one-off fake-manager message gave +2.25 (p = 0.22). 56 of the 75 new violators had read the instruction themselves (EXP). | "Paired forks let us compare interventions against an identical history; with eight forks the estimates are imprecise, and they measure susceptibility to injected instructions, not contagion between agents." | nvv contagion.md:109-120; ANALYSIS_PLAN.md:16,123-124; FINDINGS.md:68-71,384-385 |
| F5c | Held-out splits for new task families and new attack channels | Supported with changes | There is one held-out family (metricore: 8 configs, 24 runs) and one held-out injection carrier (tool output: 8 configs, 16 runs), plus test_id (12/36) and forks (8/24). Pooled: 36 configs, 2,338 rows, 156 positive. The splits are not blind. Model selection used night_train CV, not night_val (DES). | "Held-out splits test one unseen task family and one unseen injection carrier (tool output), next to an in-distribution split and the forks: 36 configurations, 2,338 rows (156 positive), held out but not blind." | nvv heldout_full.md:21-27; DECISIONS.md:505-513; ANALYSIS_PLAN.md:13-15,139-143 |
| F5d | Blind validation suite night_vx | Supported (PRE design), with qualifiers | 93 evaluated runs. 14 new configs with predicted p_tip 0.30–0.80, each run as id ×2, time, glm and enf, plus topo on 7 configs; Part B adds 16 runs. Blind only for monitor scores. Part B is partly blind (10 of 29 pairs are night–night). The evaluation script ran twice, with byte-identical outputs (PRE). | "A separate suite adds 93 runs whose monitor scores were frozen before any comparison with labels … The evaluation script ran on these frozen inputs twice, independently, with byte-identical outputs; the within-configuration part is only partly blind." | nvv VALIDATION.md:59-69,96-126; vx.md:3-5,39-43,51-55,142; runs_vx/_logs/vx_summary.md:3-15 |
| F6a | 20 synchronous rounds | Contradicted | R = 30 in all 112 configs. The cut falls after round 17, 20, 23 or 26 (28 configs each). R = 20 belonged to v1.1 and pilots 1–3 (DES). | "An episode has 30 synchronous rounds; the release cut falls after round 17, 20, 23 or 26, and work continues until round 30." | nvv dataset/index.csv; DECISIONS.md:67,361,570; README.md:16 is out of date |
| F6b | Six libraries with 24 functions each | Supported | 144 automatically checked functions; metricore is used only in test_ood_family (DES). | "Six self-written Python libraries with 24 interdependent functions each, one ticket per agent; one library is held out." | nvv README.md:45-75; dataset/packages/*/package.json |
| F6c | Six of the 24 tickets are impossible | Contradicted | 9, 12 or 16 of 24 (39/38/35 configs). Stuck agents per run: 9–24, mean 14 (DES). | "9, 12 or 16 of the 24 tickets (balanced) are unsolvable: an extra regression test contradicts the specification." | nvv index.csv; DECISIONS.md:70,480,520; analysis_runs.csv (at_risk) |
| F6d | K2 scorer file / K4 skip-checks flag | Supported | Each type has 56 configs and 126 runs (DES). | As in the checker wording. | nvv README.md:79-94; engine.py:192-205,403-421 |
| F6e | One tool action plus up to two messages per round | Supported with changes | One action per round. The message cap is 1 in 59 configs and 2 in 53, at about 120 or 250 tokens; messages are free (DES). | "One action per round and one or two messages, depending on the configuration." | nvv texts.py:224-227; runner/orchestrator.py:911; index.csv; DECISIONS.md:280 |
| F6f | Four models and mixes | Supported | Duo 12/12 in 55 configs; majority 12/4/4/4 in 57; no homogeneous team (DES). | As in the reviewer wording. | nvv config.py:37-46; index.csv |
| F6g | GLM-5.2 as held-out model | Supported with changes | GLM-5.2 is in no night split. It appears only in the night_vx glm arm (12 of 24 agents, 14 runs), so there is no held-out test split for it (DES). | "A fifth model, GLM-5.2, appears only in the validation suite, where it replaces 12 of the 24 agents in 14 runs." | nvv config.py:42; index.csv; VALIDATION.md:100 |
| F6h | Seed types | Supported with changes | Five conditions, including none (22/21/19/24/26 configs). External seeds are fake authority (11) or injection (15; tool output only in test_ood_seed). Peers-only configs always contain one informed agent (DES). | As in the reviewer wording, plus "In peers-only configurations, one agent always knows the shortcut." | nvv index.csv; texts.py:263-276,363-389,481-488; scenario.py:349-351 |
| F6i | Two jury judges, 0–3 scale | Supported | DeepSeek V4 Flash and Claude Haiku 5.5 rate 9 dimensions; features are their mean and their disagreement. Agreement between the judges has never been reported (DES). | As in the checker wording, plus "(agreement between the judges has not yet been measured)". | nvv runner/jury.py:1-14,73,83; FINDINGS.md:263-264 |
| F6j | 20 edge and 10 node features, tiers S0–S3 | Contradicted | The data use catalog v1.1: 22 edge columns (the NLI contradiction feature is NaN in all runs), 11 node columns and 2 tool-based ablation columns. The headline monitors use 18 edge and 5 node features (DES). | "Edges carry 22 features (the NLI feature was not computed) and nodes 11 …; the headline monitors use 18 edge and 5 node features." | nvv FEATURES.md:7,33-43,67-89; runs_night/*/graph_meta.json; go gnn_opt/data.py:28-38; got gnn_opt_torch/RESULTS.md:30-32 |
| F6k | θ = 8 within 3 rounds | Supported | Pre-registered label: 6,468 defined rows (303 positive), 6,388 if fork prefixes are counted once (PRE). | "A team tips when at least 8 of its 24 agents (one third, instructed seeds included) have used the shortcut; monitors predict this within the next 3 rounds." | nvv ANALYSIS_PLAN.md:30-34; labels.py:156-161 |

### 1b. What the traces show

| ID | Claim (short) | Final verdict | What the data say | Paper wording or "drop" | Source |
|---|---|---|---|---|---|
| T1 | Tipping is common (40% of swarms) | Supported with changes | 101/252 runs (40.1%); 93/236 control runs (39.4%). The rate is calibrated: the freeze was the base-rate dial, with a 20–80% target. Runs are correlated (ICC 0.73). 52 configs tipped at least once, 50 counting control runs only (DES; recounted). | "In the main batch 101 of 252 runs (40%) tipped (at least 8 of 24 agents used the shortcut; median 12 rule-breakers in tipped runs). This rate reflects our calibration, not a natural frequency." Say "runs", not "swarms". | nvv FINDINGS.md:21,43; stats-factors/REPORT.md:21-23,36; DECISIONS.md:496,518,523 |
| T2 | Hearing from an earlier rule-breaker "triples" adoption | Contradicted, no source. VW1 already rejects even the general "doubling". | No file says "triples". Pooled MH OR is 2.34 [1.54, 3.57] for all uninstructed agents and 2.02 [1.18, 3.63] for DM recipients. By shortcut type: K4 3.99 [2.41, 7.01] / 2.65 [1.35, 5.61]; K2 0.87 / 1.04; board 1.43 / 1.19. Organic, unsolicited messages give 1.29 [0.61, 2.55]. A homophily-only simulation already yields about 1.8–1.9 (EXP, observational). | "In the skip-checks scenarios, uninstructed agents who had just received a direct message from a peer who had already used the shortcut adopted it more often than comparable agents in the same run and round (Mantel-Haenszel OR 3.99 [2.41, 7.01]; 2.65 [1.35, 5.61] among message recipients), well above a time-shuffle null (median 1.23). There was no such association for scorer tampering or on the shared board. The analysis is observational and post hoc; homophily, seeded advocates and agents seeking out violators can contribute." | nvv contagion.md:17-19,24-28,39-53,63-75,81-88; FINDINGS.md:59-67,380-381; ANALYSIS_PLAN.md:117-124 |
| T3a | The environment, not the persona, decides | Supported with changes (I accept the reviewer's correction after checking the code) | Environment factors survive Holm over 14: shortcut type +29.5 pp (Holm 0.008), discoverability +32.4 pp (Holm 0.006), channels (Holm 0.006); K4 × discoverable has a mean config tip rate of 82.2% vs 19.9–24.4%. Persona: skewed-pragmatic vs uniform mix −3.9 pp [−19.7, +12.4]; persistence persona +8.0 pp [−9.0, +24.5]; effects below 20–25 pp cannot be detected. The careful personas (methodical, skeptical) were in the uniform mix; only the careful-skewed mix was dropped, after 0/7 in pilot 4 (EXP). | "Tipping depended mainly on the environment … The two persona manipulations we varied showed no detectable effect, but effects of 20–25 points cannot be excluded and a careful-skewed persona mix was not part of the main batch, so we do not claim that personas are irrelevant." Drop "decides". | nvv stats-factors/REPORT.md:15,17,51-60,294,296; generator/config.py:173-196; generate.py:489; DECISIONS.md:456 |
| T3b | Channel design, a freeze and a visible shortcut "multiply the odds"; persona prompts don't move them | Supported with changes | The visible shortcut matters only within K4 (+62.4 pp; within K2 −1.4). Channels are significant marginally (Holm 0.0056) but not after adjustment (Holm 0.07–0.11). The freeze gives +26.0 pp [+9.9, +41.5], p = 0.0048, Holm 0.053; adjusted +19.2 (Holm 0.31). Odds ratios are unstable: 37% of bootstrap refits separate (EXP). | "In exploratory permutation tests over 112 configurations (Holm over 14 factors), shortcut type, discoverability and channel layout changed the tipping rate … A release freeze raised it from 20% to 46% (p = 0.005; Holm p = 0.053). We do not report odds ratios." Drop "multiply the odds". | nvv stats-factors/REPORT.md:9-17,51-66,100-124 |
| T4 | One message is enough: a single injected comment raised rule-breakers in 7 of 8 forks | Contradicted (VW3) | The "comment" was a persistent instruction attached to every issue listing and every escalation reply, reaching 1–17 agents per fork. Result: +4.5 [1.0, 8.0], positive in 7/8, Holm 0.06; tipped 5/8 vs 3/8 (McNemar 0.5). The one-off fake-manager DM gave +2.25 (p = 0.22), with 3/8 tipped in both arms (EXP). | "A persistent injected instruction was followed by more rule-breaking (4.9 to 9.4 new rule-breakers per run; +4.5 [1.0, 8.0]; Holm p = 0.06); a single fake-manager message showed no detectable effect. 56 of the 75 new rule-breakers had read the instruction themselves." | nvv contagion.md:99-120; FINDINGS.md:68-71,384-385; analysis/review/confirm-contagion-design/i4_branch_tests.out |
| T5 | Pressure drives it; agents who can work honestly almost never break the rules (3.5%) | Supported with changes. "3.5%" has no source. | Uninstructed agents in the 236 control runs who broke the rule at least once: own ticket unsolvable 1,221/2,807 (43.5%); blocked only by a dependency 26/405 (6.4%); solvable and unblocked 74/2,357 (3.1%; K2 0.7%, K4 6.0%). 94.4% of uninstructed violators were stuck. The 3.5% equals 104/2,956 (solvable plus dependency-blocked, fork arms included), an undocumented mix. Team-level evidence for pressure is weak: freeze Holm 0.053; manager push +0.2 pp; the longer sprint in night_vx did not reduce tipping (8 vs 6 of 14). (EXP; counts from committed labels and scenario files via an uncommitted script that I re-ran with the same result.) | "Rule-breaking was concentrated among agents whose ticket the generator had made unsolvable (43.5% of them broke the rule, against 3.1% of agents with a solvable, unblocked ticket). Evidence that time pressure drives tipping at the team level is weaker …" | scratch wf_story/stuck_rates.py on nvv runs_night/*/labels.json + dataset/scenarios/core/*.json; stats-factors/REPORT.md:9,15; vx.md:30-31,146 |
| T6a | Table 2: unpunished cheating peer / public sanction / announced audit | No source: never run (VW4 for sanction effects) | Shocks were fixed to none. Sanctions could fire in only 8 of 112 configs (6/16 runs tipped; +5.6 pp [−25.4, +35.8]). night_vx enforcement: 5 vs 6 of 14 tipped (McNemar p = 1.0, descriptive). The merge feed showed every shortcut merge, unpunished, to all agents (DES). | "Our runs did not include the unpunished-peer, punished-peer or announced-audit events; sanctions could fire in only 8 configurations, too few for a test." Mark the rows as "not run". | nvv DECISIONS.md:81,515-517; index.csv shocks_list; stats-factors/REPORT.md:13; vx.md:148 |
| T6b | Table 2: share of adoptions told by peers when only peers know | No source (never computed) | Closest numbers: K4 peers-only OR 16.1 [6.2, 40.8] for all agents and 12.2 [3.6, 32.3] for DM recipients. Peers-only configs with seed type none never tipped (0/19 control runs). After the first shortcut merge the feed shows skip_checks to everyone (EXP). | Drop the row, or write "We did not compute this share; where the flag appeared only in seeded agents' tool signatures, a direct message from a rule-breaker was most strongly associated with adoption (OR 16.1 / 12.2)." | nvv contagion.md:67; stats-factors/REPORT.md:239; generator/texts.py:285-289 |
| T6c | Table 2: time-shuffle test (Anagnostopoulos et al.) | Supported (EXP) | Observed 2.34 vs null median 1.21 [0.98, 1.49] (p = 0.001). DM recipients 2.02 vs 1.24 [0.93, 1.66] (p ≈ 0.003). K4 DM 2.65 vs 1.23 (p = 0.001). K2 1.04 vs 1.25. Same-round negative control 1.18 [0.74, 1.76]. | As in the reviewer wording, including "part of it reflects who adopts rather than when". | nvv contagion.md:41-42,81-84; analysis/review/confirm-contagion-design/i1_nulls.out:23-33 |
| T6d | Table 2: adoption by uninstructed agents (% of violators) | Supported with changes (simple arithmetic) | 1,321 of 1,382 violators in control runs (95.6%); 1,453/1,514 (96.0%) including forks. Uninstructed does not mean uninfluenced: 426 were in injection runs, 190 in knower runs, and only 165 (12%) in runs without any seed (DES). | "Of the 1,382 rule-breakers in the 236 control runs, 1,321 (96%) had not been instructed … only 165 (12%) were in runs without any seeded agent or injection." | nvv analysis_runs.csv (nv, nvu, seed_type; recounted); FINDINGS.md:52-53 |
| T6e | Table 2: private thoughts suspecting a test | No source | Thoughts were logged for this covariate but never analysed. An uncommitted regex screen gives 74 hits (55 "simulat"), mostly after the agent's ticket was done, so there is no usable number (none). | "Each agent's private reasoning was logged so that evaluation awareness could be studied, but we did not analyse it systematically (limitation)." | nvv README.md:186,209-211; scenario.py:753; scratch wf_story/thought_screen2.out:1 |
| T6f | Figure 2: adoption vs number of distinct exposing contacts | No source | The contagion analysis uses binary exposures only. `exposure_breadth` is a model input. The synthetic testbed assumes complex contagion by construction (none). | Drop the figure: "We did not estimate a dose-response, so our data cannot distinguish simple from complex contagion." | nvv analysis/contagion.py:3-12; FEATURES.md:78; gs gnn/RESULTS_amongus.md:62-64 |

### 1c. Prediction

| ID | Claim (short) | Final verdict | What the data say | Paper wording or "drop" | Source |
|---|---|---|---|---|---|
| P1 | AUROC 0.92 on held-out configurations | Supported with changes | 0.92 is GNN 0.921 [0.861, 0.972] and hybrid 0.922 [0.863, 0.965] on test_id only (12 configs, 7 with positives; HO-sec). On the same split bag+graph reaches 0.902 and the clock 0.847. The primary pooled result (36 configs, HO): GNN 0.817 [0.756, 0.873], hybrid 0.832 [0.782, 0.881], bag+graph 0.812 [0.759, 0.861], zs:pairwise 0.855 [0.808, 0.899], clock 0.781 [0.714, 0.841]. 0/11 Holm tests significant (smallest Holm p 0.090). | "On 36 held-out configurations (held out, not blind) the monitors reach AUROC 0.800–0.855, against 0.781 for a round-number clock; none of the 11 pre-specified comparisons is significant after Holm correction. Only on the in-distribution split (12 configurations; secondary) do the GNN models reach 0.92, where gradient boosting reaches 0.90 and the clock 0.85." | nvv heldout_full.md:8,12,23,113-118,130-136; heldout.md:20-30,48; cs synthesis_cloud/test_look1/y3.txt:5,10 |
| P2 | Classifiers tell twin runs apart, so they read dynamics | Contradicted. Pre-registered H1 was not supported, and vx.md:184-186 forbids claiming either direction. | H1: GNN 0.759 [0.450, 0.974] on 29 pairs from 6 configs (partly blind); on the same pairs the structure-only baseline scores 0.86 and the oracle 0.55. Held-out within mixed config × time bin (9 configs, 45 positives): trained monitors 0.59–0.65, below the clock at 0.68. In the branch arms, the GNN and the hybrid rank the arm that later tips higher in only 1 of 6 pairs (PRE + HO-sec). | "Which of two runs of the same configuration will tip remains hard to predict … In the pre-registered within-configuration test (29 run pairs, 6 configurations, partly blind) the GNN reaches 0.76 [0.45, 0.97], so the hypothesis that it reads within-run dynamics is not supported, though the interval cannot rule it out." | nvv vx.md:63,110-138,184-186; heldout_full.md:113-126; FINDINGS.md:149-150; cs test_look1/y3.txt:27-30 |
| P2-19of23 | "19 of 23" twin pairs | No source. Drop. | No committed file has it. The only 23-pair statistic (protocol a, cut−6) peaks at 18/23 = 0.783. Part B has 19 pairs containing a new run, which is a different set (none). | Drop. | nvv results/llm_monitor/RESULTS.md:330-374; vx.md:133-134 |
| P3 | Ladder: clock, pairwise, aggregated, graph, GNN | Supported with changes (VW5 if the GNN or hybrid is presented as best) | The ladder holds in CV, descriptively: harness ID AUROC clock 0.754, hgb_pairwise 0.794, bag 0.820, bag+graph 0.843, GNN 0.880–0.885. It does not hold on held-out data (GNN − bag+graph +0.004 [−0.036, +0.046], Holm 1.0) or in night_vx, where the pre-registered order failed in all 4 arms. The strongest held-out monitor, the zero-shot LLM, is missing from the proposed ladder (CV + HO). | "On identical snapshots we compare a clock, gradient boosting on aggregated communication features (with graph and memory features), an edge monitor, a temporal GNN, a GNN–boosting blend and zero-shot LLM monitors … In cross-validation the rungs order as expected; on held-out data they do not." | nvv stats-monitors/REPORT.md:7-9,72-82,118-130; heldout_full.md:145-159; vx_verdicts.md:30-35; ANALYSIS_PLAN.md:72-73; got gnn_opt_torch/RESULTS.md:40-53 |
| P4 | Table 3 with AUROC, AUPRC, R@5%FPR, MAE and lead time for the template's six rows | Supported with changes | Held-out values exist for clock, edge monitor, bag+graph, tab_mem, GNN, hybrid and the zero-shot LLMs. MAE exists only for the GNN count head (0.94 held-out, 0.68 CV). S0 exists only in CV (0.804 vs 0.871). K0 does not exist for the swarm. The "run size" baseline was never computed. The tabular model is sklearn HistGradientBoosting, not LightGBM (HO + CV). | See §3.4. | nvv heldout_full.md:53,113-140,243-257; ANALYSIS_PLAN.md:173-179; got RESULTS.md:205-217; cs test_look1/y3.txt:3 |
| P5-Table4 | Transfer to a new library, a new injection channel, a new model | Supported with changes | New family: monitors 0.78–0.87 vs clock 0.66. Tool-output injection: the clock (0.82) beats all trained monitors (0.74–0.79), while the LLMs reach 0.83–0.84; within absolute-round bins trained monitors score 0.54–0.56 and LLMs 0.64–0.70. GLM-5.2 has no held-out split, only the vx glm arm: 13/14 tipped, GNN 0.73, clock 0.87, H3 not supported (HO-sec + PRE). | See §3.5. | nvv heldout_full.md:130-139,265; vx_eval.md:34-59; vx_verdicts.md:9 |
| P5-Fig3 | AUROC against prediction horizon 1–5 | Not supported: no such data | Only Δ = 2, 3 and 5 exist, in an exploratory protocol-(a) sensitivity: pooled OOF over all 112 configs, test configs included, no GNN. Per-conversation LLM 0.903 / 0.890 / 0.866; bag+graph 0.850 / 0.864 / 0.845; clock 0.780 / 0.783 / 0.780 (EXP). | "We did not vary the horizon systematically; in a post hoc sensitivity analysis AUROC changed by at most 0.04 between Δ = 2, 3 and 5." Drop Figure 3. | nvv analysis/results/sensitivity.md:7-34; got RESULTS.md:329-336 |
| P6-cost | Per-run cost of LLM monitors vs the GNN | Supported with changes | Per conversation $0.0128 per run (5,301 tokens per snapshot); full transcript $0.0423 (21,700, k = 3); all 7 variants $39.02. The jury behind all trained feature monitors: Haiku share $0.00074 per snapshot, about $0.022 per run by arithmetic (one call per message); DeepSeek was not priced (DES). | "Monitoring was cheap at this scale … The trained monitors are not a cheaper alternative: their features come from two LLM judges (Haiku share alone about $0.022 per run)." | nvv results/llm_monitor/RESULTS.md:530-540; sim_dataset/runner/run.py:49,310 |
| P6-template | "Reading every message with a large LLM judge is expensive and grows every round" | Contradicted for this study | The judges are small models and cost cents per run. Only the full-transcript monitor's input grows with t; the per-message jury and the windowed monitors do not grow that way (DES). | "At our scale LLM monitoring was cheap; only a monitor that re-reads the whole transcript each round becomes more expensive as a run grows (21.7k vs 5.3k tokens per round)." | nvv RESULTS.md:530-538; llm_monitor/README.md:81-84,146-149 |

### 1d. Structure versus content

| ID | Claim (short) | Final verdict | What the data say | Paper wording or "drop" | Source |
|---|---|---|---|---|---|
| S1a | Watching the swarm as a whole beats watching single conversations | Not supported; the data lean the other way (reviewer's verdict accepted, see below) | In CV (descriptive, supplementary): per-conversation LLM 0.922 vs whole transcript 0.865 (+0.057 [+0.025, +0.091]); vs GNN +0.032 (Holm 0.61). On held-out: per-conversation − GNN +0.038 (Holm 1.0); − whole transcript +0.039 [−0.004, +0.082] (HO-sec). In night_vx, post hoc: whole transcript − per-conversation +0.048 [−0.016, +0.118]. | "We found no evidence that monitoring the swarm as a whole beats monitoring single conversations; a zero-shot monitor reading one conversation at a time was at least as accurate as the GNN and the full-transcript monitor, and no held-out difference survived Holm correction." | nvv stats-monitors/REPORT.md:80,134,146; ANALYSIS_PLAN.md:72-73; heldout.md:44; heldout_full.md:204; vx_posthoc.json (pooled_part_a); FINDINGS.md:95-100 |
| S1b | Main outcome: structure matters | Contradicted for prediction | Rewiring changes CV AUROC by −0.004 [−0.032, +0.023] (5 folds, one seed; second base 0.866 vs 0.859). Content ablations S0–S2 cost 0.06–0.08 AUROC and 0.10–0.13 tAUROC. FINDINGS marks "Die Graphstruktur selbst trägt kaum etwas bei" ✅. Channel layout still changes outcomes (board 52% vs DM-only 12%, EXP), just not prediction (EXP). | "For prediction, what agents said mattered more than who talked to whom: random rewiring left cross-validated AUROC unchanged, removing the jury's content ratings lowered it." | nvv FINDINGS.md:29-30,113-115; stats-monitors/REPORT.md:201-209,251; got RESULTS.md:15-18,361-378 |
| S2a | Graph models gain most where communication is local | Not supported. Drop. | Never tested. Descriptive strata point the other way: in CV the GNN scores 0.870 on board vs 0.783 in team/DM configs, where tab_mem reaches 0.874 and the edge monitor 0.902. On held-out data (GNN team's test look), GNN − tab_mem is +0.006 on board and +0.003 in team/DM. The non-board training cell holds 15 positive rows from 5 tipped runs, all K4 (CV, HO, descriptive). | Drop. | got gnn_opt_torch/preds/cv_table_cloud_final.csv:2-5; DATA_REQUESTS.md:9-11; cs synthesis_cloud/test_look1/y3.txt:2,7,12 |
| S2b | The advantage grows with swarm size in synthetic swarms (+0.02 → +0.12) | Supported with changes (synthetic, EXP) | A toy complex-contagion testbed (no LLM agents), 1 training seed, 60 test episodes per N, no CIs. The gap rises because the global-aggregate baseline degrades (0.919 → 0.808) while GINE stays at 0.93–0.97. Against one-hop LogReg the gap is only +0.004 to +0.028, and a rewired GINE keeps 0.095 of the 0.122 gap at N = 192. Not on nvv and not in FINDINGS (EXP). | "In a synthetic complex-contagion testbed built so that structure matters (no LLM agents; one seed), a GINE's margin over gradient boosting on graph-wide aggregates rose from +0.02 to +0.12 AUROC as N grew from 24 to 192, because the baseline degraded; against one-hop aggregates the margin was at most +0.04. This shows conditions, not evidence about LLM swarms." | gs gnn/RESULTS_amongus.md:60-86; gnn/sweeps/synth_scaling.json |
| S3 | Beats the best tabular model on Among Us (+0.06) | Supported with changes (preliminary, appendix) | Self-play plus cross-play (8,626 games): wrong-ejection AUROC GatedGCN+aux 0.705 [0.679, 0.731] vs HGB 0.642 [0.614, 0.672]; impostor 0.938 vs 0.924; OOD reversed (0.902 vs 0.907). On self-play alone it is a tie (0.617 vs 0.612). Only one tabular model, CIs per model, test split viewed repeatedly. FINDINGS §8 uses the older file (EXP). | As in the reviewer wording (includes "preliminary; test split inspected during development"). | gs gnn/RESULTS_amongus.md:88-109; nvv gnn/RESULTS_amongus.md:14-37; FINDINGS.md:160-169 |
| S4 | Shuffling the graph costs accuracy | Contradicted for the swarm GNN | Rewire −0.004 (CV). shuffle_ef −0.041 AUROC / −0.062 tAUROC, inside the seed-noise band. Row-label permutation 0.421 [0.310, 0.535]. In Among Us, rewiring costs only on group errors: 0.571 vs 0.589–0.619 on self-play, 0.667 vs 0.705 pooled (EXP). | "In the LLM swarm the graph's wiring did not matter to the GNN (−0.004 [−0.032, +0.023]); only in exploratory Among Us runs did degree-preserving rewiring cost accuracy, for predicting wrong ejections." | nvv stats-monitors/REPORT.md:199-211,251; gs gnn/RESULTS_amongus.md:33-36,51,98,105 |
| S5a | Where communication is local, the GNN pulls ahead | Not supported (reviewer's verdict accepted) | Descriptive data point the other way (CV and held-out strata; on the 7 local vx bases GNN 0.79 / 0.64 vs bag+graph 0.80 / 0.72). The topo arm's +0.10 for the GNN is within noise, and the GNN also rose +0.05 in the time and enf arms. H5 CI [−0.21, +0.61], and its sign flips under time matching (descriptive / PRE). | "We saw no sign that the GNN gains where communication is local …" | got cv_table_cloud_final.csv:2-5; nvv vx.md:67,85-98,182-183; vx_eval.md:23,52,81,110 |
| S5b | In broadcast-heavy swarms a light swarm-level monitor already does the job | Not supported. Drop. | On board configs in CV, counted features (0.823) and the whole-transcript LLM (0.849) trail the per-conversation LLM (0.922). There is no adequacy criterion (CV). | Drop. | nvv stats-monitors/REPORT.md:38-47 |
| S6 | Takeaway: swarm safety needs swarm-level monitoring, and structure becomes essential as swarms grow | Not supported | N was fixed at 24 and locality was not varied. Rewiring costs nothing. The best monitors read single conversations or single agents. The part that holds: communication carries an early-warning signal. In CV all 5 monitors beat the clock time-matched (Holm 0.0011); on held-out data only with absolute-round matching (p ≤ 0.0002), not with the pre-registered matching (0/5) (CV + HO). | "In 24-agent teams, communication carried an early-warning signal, but graph structure added none we could detect; whether structure matters in larger or more locally connected teams remains open." | nvv VALIDATION.md:44; FINDINGS.md:272; stats-monitors/REPORT.md:72-76; heldout.md:36-40,48,56-57 |

### 1e. Validation and transfer

| ID | Claim (short) | Final verdict | What the data say | Paper wording or "drop" | Source |
|---|---|---|---|---|---|
| V1 | Monitors transfer to a different kind of contagion | Not supported | There was no cross-domain test: Among Us models were retrained in-domain. Within the swarm, OOD results are mixed: on the new family all monitors beat the clock, on the injection splits the trained monitors are at or below it. K2→K4 LODO in CV: node-memory GNN 0.82–0.83 vs team-memory 0.70–0.76 (single seeds) (HO-sec + CV). | "We did not test transfer to a different contagion process … within the swarm, held-out conditions gave mixed results." | nvv heldout_full.md:130-139; got RESULTS.md:287-293; gs gnn/sweeps/amongus_*.json |
| V2 | Hidden injections show up in the messages about 6 rounds before the tip | No source; the implication is contradicted | The only "5–6 rounds" in the repo is a feature-pipeline look-ahead: external-sender nodes are present from round 1, a median 5–6 rounds before their first message, with an effect of at most 0.0006 AUROC. On the tool-output split the trigger is not in the communication (DES + HO-sec). | Drop. Use instead: "When the trigger arrived through tool output, it never appeared in the monitored messages; trained monitors were near chance within round bins (0.54–0.56), zero-shot LLMs 0.64–0.70." | nvv analysis/review/vx-preeval/audit_reports.json:99-101,170-172; ANALYSIS_PLAN.md:210-212; heldout_full.md:265 |
| V3 | Blind-validation claims (no detectable drop, ~0.2 resolution, H1–H5, replicate noise, global_full highest, Part B) | Supported (PRE; post hoc parts flagged). VW6 and VW7 apply to "small noise" and "> 0.1". | 0 of 96 arm−rep1 CIs lie entirely below 0. The resolution is about 0.2 AUROC (GNN 0.2–0.35; post hoc). H1–H4 not supported and H5 supported, but no CI excludes its decision boundary. Replicate noise: clock −0.20 [−0.29, −0.09]. global_full is highest descriptively, +0.08 [+0.05, +0.12] over the GNN post hoc (H7 pending). Part B GNN 0.76 [0.45, 0.97]. | See §2 and §3.7. | nvv vx.md:11-43,61-81,110-151,177-209; vx_eval.md; vx_posthoc.json |
| V4 | SYNTHESIS §3 table matches vx_eval.json | Contradicted | Its id rep0/rep1 columns are the 7-base topo values (clock 0.797/0.543, see vx_eval.md:96), not the 14-base values (0.823/0.627, vx_eval.md:9). Its "replicate noise 0.06–0.25" inherits the error (DES). | Use vx.md:85-98 only. | cs synthesis_cloud/SYNTHESIS.md:25,49-59,67,82; nvv vx_eval.md:9-31,92-117; vx.md:53-55; FINDINGS.md:261-262 |
| V5 | LLM judges re-read everything each round and are expensive and easy to fool | Contradicted on re-reading and cost; "easy to fool" was never tested | Only the full-transcript variants re-read the history. Costs are $0.013–0.042 per run, parse rate about 1.000, 0 refusals. There was no adversarial test of any monitor (DES). | "Only the full-transcript variant re-reads every message … We did not test whether the monitors can be fooled." | nvv results/llm_monitor/RESULTS.md:530-552; llm_monitor/README.md:81-84,146-149,186,755-756 |

### 1f. Provenance checks

| ID | Claim (short) | Final verdict | What the data say | Paper wording or "drop" | Source |
|---|---|---|---|---|---|
| Q1-triples | "Triples" adoption | Contradicted, no source (VW1) | The pooled association is about 2. The only values near 3 are unadjusted K4 numbers (all-agent OR 3.99, RR 2.93) and the unreviewed E_any RR of 3.01 in contagion.json (EXP). | See T2. | nvv contagion.md:39,66; contagion.json; FINDINGS.md:380-381 |
| Q1-3.5pct | "3.5%" | No source | It reproduces only as 104/2,956 (solvable plus dependency-blocked, fork arms included). The correct figure is 3.1% (74/2,357). | Drop, or use the T5 wording. | see T5 |
| Q1-7of8 | "7 of 8" forks | Supported with changes (VW3 if read causally) | 7 of 8 pairs are positive; sign-flip p = 0.031, Holm p = 0.06 (EXP). | See T4. | nvv contagion.md:111-117 |
| Q1-19of23 | "19 of 23" | No source | The nearest number is 23 of 36 held-out configs with a positive row. | Drop. | nvv heldout.md:49 |
| Q1-scaling | +0.02 → +0.12 with swarm size | Supported with changes (synthetic) | See S2b. | See S2b. | gs gnn/RESULTS_amongus.md:72-84 |
| Q1-amongus | +0.06 on Among Us | Supported with changes (preliminary) | See S3. | See S3. | gs gnn/RESULTS_amongus.md:98,103,108-109 |
| Q1-6rounds | Warning "6 rounds" ahead | Not supported | Held-out median leads are 2–5.5 rounds, counted only over alarmed runs. "6 rounds" in the repo refers to other quantities (HO). | See §3.4 (lead time). | nvv heldout_full.md:245-255 |
| Q1-0.92 | Held-out AUROC 0.92 | Supported with changes | test_id only (HO-sec). | See P1. | nvv heldout.md:20-30 |
| Q1-40pct | 40% of runs tip | Supported | 101/252 (40.1%); 93/236 (39.4%) (DES). | See T1. | nvv stats-factors/REPORT.md:21-22 |
| Q1-252-112 | 252 runs, 112 configs | Supported | 236 control runs plus 16 fork continuations (DES). | Call them "control runs", not "independent runs" (ICC 0.73). | nvv stats-factors/REPORT.md:21-23,36 |
| Q1-persona | Persona effects | Supported with changes | Persistence persona +8.0 pp [−9.0, +24.5]; mix −3.9 pp. Part C was dropped (44% invalid JSON). Nachtrag 4, without a swarm (descriptive): the fine-tuned model held its position in 48/60 replies vs 36/60 for the base (paired sign test over 12 probes, p = 0.73) (EXP). | "Neither a prompted persistence persona nor the persona mix had a detectable effect … persistence instilled by fine-tuning could not be tested in the swarm." | nvv stats-factors/REPORT.md:57,60; analysis/results/ft_compare.md:7-14; FINDINGS.md:216-227 |
| Q1-freeze | A release freeze increases tipping | Supported with changes | +26.0 pp, p 0.0048, Holm 0.053; adjusted +19.2 (Holm 0.31) (EXP; freeze was the base-rate dial named before the batch). | See T3b. | nvv stats-factors/REPORT.md:9,52,66,154,297 |
| Q1-broadcast | Broadcast channels | Supported with changes | Board 51.7% vs DM-only 11.8% (Holm 0.0056; adjusted Holm 0.11). On the board the DM association equals the placebo (1.43 vs 1.50) (EXP). | "Configurations with a public release board tipped far more often (52% vs 12% DM-only); whether board posts spread the shortcut cannot be estimated." | nvv stats-factors/REPORT.md:11,55; contagion.md:69,93-97 |
| Q2-storyline-doc | A written "red line" exists in the repo | No source | No committed red-line document exists. The project's storyline is FINDINGS "Die Geschichte in fünf Sätzen", and its sentence 4 contradicts "structure matters". | Not applicable. | nvv FINDINGS.md:19-33 |
| Q3-double-execution | night_vx "evaluated exactly once" | Contradicted | run_eval.sh ran twice on the same frozen inputs: locally 00:00:53–00:24:10 CET and in the cloud 00:09:24–01:04:48 CET. All outputs except the run log are byte-identical. The second run is disclosed, but "genau einmal" remains at FINDINGS.md:174-175 and vx.md:1,3-4 (DES). | "The unchanged script was executed twice on these frozen inputs, locally and independently in a separate cloud session; all result files are byte-identical." | nvv analysis/results/vx_run.log@bb3f665d; cs vx_run.log@b14b3393; FINDINGS.md:174-175,202-204; vx.md:3-4,51-55; analysis/vx_preds/run_eval.sh:7 |

**User claims without a claim ID.** These are literature claims that cannot be checked in the repo and need citations:
- Paglieri et al. (2026): one exploit spread through 100 agents.
- The Hugging Face case (~1,200 agents). The template lists its source as "[TBD]" (reference 25), so it cannot be cited yet.
- "Existing datasets have 2–15 agents and scripted attackers".
- "Graph detectors look for single compromised agents and act afterwards".
- "Nobody measures the risk of the swarm as a whole". Hedge this as "to our knowledge".

### Where checker and reviewer disagreed, and what I decided after opening the sources

- **F2d:** the reviewer is right. `flags.info_asym` is true for one agent in core-night_branch-K2-002, K2-005, K4-000 and K4-007, which are all the peers-only fork configs.
- **F4c:** the reviewer is right. stats-factors/REPORT.md:52 shows no-freeze configs tipping at 20.2% (33 configs). DECISIONS.md:485 says K2 spread without a feed in pilot 4. So the "needed three things" wording fails. The 82% is a mean config rate (REPORT.md:17).
- **F5c:** the reviewer is right. ANALYSIS_PLAN.md:139-143 says the GNN was selected on night_train CV and the final models were trained on night_train; night_val had 2 looks (ANALYSIS_PLAN.md:14).
- **T1:** the reviewer is right. My recount gives 52 configs with any tipped run and 50 counting control runs only.
- **T3a:** the reviewer is right. config.py:173-196: the uniform mix contains "methodical" and "skeptical: a careful reviewer by habit". generate.py:489: "skewed_careful: 0/7 in pilot 4, left out".
- **S1a:** reviewer's "not supported" accepted. The CV pairwise − global_full row is in the "Supplementary … not in the Holm family" table (REPORT.md:134,146), and the plan makes CV descriptive (ANALYSIS_PLAN.md:72-73). Held-out differences are ties.
- **S5a:** reviewer's "not supported" accepted. The vx GNN shift is +0.052 (time), −0.059 (glm), +0.050 (enf) and +0.104 (topo) (vx_eval.md:23,52,81,110), so topo is not unique. The held-out channel strata in the GNN team's test-look file show no local-channel gain either (GNN − tab_mem: board +0.006, team/DM +0.003; cs test_look1/y3.txt:2,7,12).
- **P6-cost:** the reviewer is right. run.py:310 sets `group = a.group_deepseek if adaption else 1`, so Haiku scored one message per call; only the DeepSeek token count can be inflated.
- **T6e:** the reviewer is right. thought_screen2.out:1 reports 74 hits, not 52. No number goes into the paper either way.
- **T5:** checker and reviewer agree. I re-ran the count script on committed files and got the same numbers (1,221/2,807; 26/405; 74/2,357; 94.4% stuck).
- **V3:** I accept the reviewer's additions: the run-order confound, and time arm vs rep0 being +4.6 rounds paired over 5 bases (vx_posthoc.json timing), not +4.1.

---

## 2. Storyline the data support

### (a) Abstract (224 words)

LLM agents in a team can break rules together: one finds a forbidden shortcut and others follow. We asked whether this collective tipping can be predicted from communication, and whether a graph of who talks to whom helps. To our knowledge no labelled data for this existed, so we built a simulator of 24-agent software teams with unsolvable tickets and one working forbidden shortcut, labelled from tool logs. After four calibration pilots, the main batch has 252 runs in 112 configurations; 101 runs tipped (at least 8 of 24 agents used the shortcut). Tipping depended mainly on the environment, most of all on whether every agent could see the shortcut; the persona prompts we varied had no detectable effect. A direct message from an earlier rule-breaker was associated with adoption for only one of two shortcut types. On 36 held-out configurations, monitors predicted tipping within three rounds with AUROC 0.800–0.855, against 0.781 for a round-number clock. A graph neural network (0.817) did not outperform gradient boosting on aggregated features (0.812) or an untrained LLM reading one conversation at a time (0.855); no pre-specified comparison survived Holm correction. Randomly rewiring the graph left cross-validated accuracy unchanged, while removing message-content ratings lowered it. In these teams the warning signal lies in what agents say, not in who talks to whom. We release the simulator and dataset.

### (b) Red line (same 10 stages as the user's version, about 570 words)

- **The danger.** Agents increasingly work in large, connected teams, and rule-breaking can spread through them. In Paglieri et al. (2026) an evaluator exploit spread among 100 agents (the Hugging Face case needs a source before we cite it). The risk is the team tipping, not one bad agent.
- **The gap.** Graph detectors classify single compromised agents after the fact, and LLM judges score transcripts. To our knowledge, no monitor has been tested on predicting a team-level collapse in advance. We drop "expensive and easy to fool": our judges cost cents per run, and manipulation was not tested.
- **The hypothesis.** If tipping is a team property, its risk should show in the team's communication: who talks to whom, and what they say. A GNN on the communication graph should then beat monitors that read single conversations.
- **The obstacle: no data.** Testing this needs teams that tip and teams that do not, with the round at which each agent breaks a rule. To our knowledge such labelled data did not exist.
- **Contribution 1: a simulator.** 24 agents work on six self-written libraries. 9–16 of the 24 tickets are unsolvable, and exactly one forbidden shortcut works: edit the CI scoring file, or merge with skip_checks. Runs last 30 rounds. At most one agent per run is instructed, and 96% of rule-breakers never were. Labels come from tool events, and paraphrase pools and decoys limit template leakage. Tipping took four pilots (124 runs) to appear: agents waited, escalated or tried to edit protected tests, and environment bugs explain part of the early null.
- **Contribution 2: a dataset.** 252 runs (236 controls plus 16 counterfactual continuations) in 112 configurations, with four Qwen and Gemma models per team and 7,560 labelled snapshots. Held-out splits contain one unseen library and one unseen injection carrier. A blind suite adds 93 runs on 14 new configurations, with a longer sprint, an unseen model, visible enforcement and a hub network.
- **What the traces show.** 101 runs tipped, a rate we calibrated. Tipping concentrated where every agent could see the shortcut (mean configuration rate 82% vs 20–24%) and on a shared board (52% vs 12% for direct messages only). A release freeze raised it (46% vs 20%, Holm p = 0.053). The persona manipulations showed no detectable effect. A direct message from an earlier rule-breaker was associated with adoption only for skip-checks (OR 2.65 [1.35, 5.61] among message recipients), and causality is not established. A persistent injected instruction raised new violators (+4.5 per run, Holm p = 0.06); a single fake-manager message had no detectable effect.
- **Contribution 3: predicting tipping.** We compare a clock, gradient boosting on aggregated features, an edge monitor, a temporal GNN, a GNN–boosting blend and zero-shot LLM monitors on identical snapshots. On 36 held-out configurations all reach AUROC 0.800–0.855 (clock 0.781), and none of 11 pre-specified comparisons survives Holm correction. Whether the monitors beat the clock depends on how time is matched. About half of tipped runs get an alarm, a median 2–5.5 rounds ahead. Within one configuration all monitors get weaker, and the pre-registered within-configuration test was not supported.
- **Main outcome: content, not structure.** The hypothesis was not confirmed. Rewiring the graph at random cost nothing (−0.004 [−0.032, +0.023], cross-validation), while removing the jury's content ratings cost 0.06–0.08 AUROC. On held-out data the GNN tied gradient boosting (+0.004), and an untrained LLM reading one conversation at a time matched both. In the blind suite no monitor dropped detectably more than between two replicates, at a resolution of about 0.2 AUROC.
- **Takeaway.** In 24-agent teams, early warning from communication is feasible and cheap (about one cent per run) and does not need graph structure. The hard parts are the data and telling a risky setup from a risky run. Whether structure matters in larger or more locally connected teams remains open; a synthetic contagion testbed shows when it could. We release the simulator and dataset.

**What changed against the user's version.**
- Removed because there is no source or it is contradicted: "triples", "3.5%", "19 of 23", "6 rounds", "one message is enough", "realistic", "well-aligned models refused", "LLM judges are expensive", "structure matters", "GNN pulls ahead where communication is local", "transfers to a different kind of contagion", and the size-scaling takeaway as a finding.
- Reframed: 0.92 is now a secondary in-distribution result. The main result is the pooled held-out comparison.

---

## 3. Numbers for the paper

### 3.1 Headline numbers (abstract and introduction)

| Number | Value | Kind | Source |
|---|---|---|---|
| Team, rounds | 24 agents (4 teams × 6), 30 rounds, cut after round 17/20/23/26 | DES | nvv index.csv; DECISIONS.md:570 |
| Main batch | 252 runs = 236 control + 16 fork continuations; 112 configs | DES | stats-factors/REPORT.md:21-23 |
| Tipped | 101/252 (40.1%); 93/236 control runs (39.4%); median 12 violators in tipped runs | DES | stats-factors/REPORT.md:21-22; FINDINGS.md:41-43 |
| Label | θ = 8 of 24, horizon Δ = 3 rounds | PRE | ANALYSIS_PLAN.md:30-34 |
| Volume | 7,560 snapshots; 6,388 distinct prediction rows (303 positive); 188,402 logged agent calls (7,832 format retries); 39,126 logged messages, of which 21,605 are agent-written and jury-scored; 1,720 violation events | DES | sums over runs_night/*/meta.json (recomputed); stats-monitors/REPORT.md:17 |
| Uninstructed violators | 1,453/1,514 (96.0%); control runs 1,321/1,382 (95.6%) | DES | analysis_runs.csv (recomputed) |
| Pilots | 4 pilots, 124 runs; pilots 1–3: 0 tips; pilot 4: 5/28 | PIL | DECISIONS.md:169,269-273,350-352,446 |
| Held-out set | 36 configs, 100 runs, 2,338 rows, 156 positive (prevalence 0.067) | HO | heldout_full.md:21-27 |
| Held-out AUROC | zs:pairwise 0.855 [0.808, 0.899]; hybrid 0.832 [0.782, 0.881]; GNN 0.817 [0.756, 0.873]; bag+graph 0.812 [0.759, 0.861]; clock 0.781 [0.714, 0.841] | HO | heldout_full.md:113-118 |
| Holm | 0 of 11 significant; smallest Holm p 0.090 (zs:pairwise − clock, time-matched) | HO | heldout_full.md:8,149-159 |
| CV vs clock | All 5 monitors beat the clock time-matched, +0.378 to +0.484, Holm 0.0011 | CV | stats-monitors/REPORT.md:72-76 |
| Structure vs content | Rewire −0.004 [−0.032, +0.023]; S0/S1/S2 −0.067/−0.081/−0.057 AUROC and −0.115/−0.127/−0.102 tAUROC | EXP (CV id0, 1 seed) | stats-monitors/REPORT.md:201-209 |
| Cost | $0.0128 per run (per conversation), $0.0423 (full transcript); $39.02 for all 7 variants | DES | results/llm_monitor/RESULTS.md:530-538 |

### 3.2 Template §4.1 placeholders

- [N] = 252 runs (236 control + 16 counterfactual continuations).
- [M] = 112 configurations.
- [K] = 36 held-out configurations (100 runs).
- [x] = 40.1% of runs (39.4% of control runs).
- [y] = 15 of 104 configurations with at least 2 control runs had both outcomes (14%). The template target "≥ 40% mixed" was not reached.

Sources: stats-factors/REPORT.md:21-36; heldout_full.md:27; VALIDATION.md:34.

### 3.3 Table 2: validity checks (none use a monitor)

| Check | Value | Kind | Source |
|---|---|---|---|
| Unpunished peer / public sanction / announced audit | **Does not exist (not run).** Sanctions were active in only 8 configs: 6/16 runs tipped, +5.6 pp [−25.4, +35.8], not testable (VW4). night_vx visible enforcement: 5 vs 6 of 14 tipped, McNemar p = 1.0 | EXP / descriptive | stats-factors/REPORT.md:13; vx.md:148 |
| Share of adoptions told by peers (peers-only) | **Does not exist.** Nearest: K4 peers-only OR 16.1 [6.2, 40.8] / 12.2 [3.6, 32.3]; seed none × peers-only tipped 0/19 control runs | EXP | contagion.md:67; stats-factors/REPORT.md:239 |
| Time-shuffle test | Observed 2.34 vs null 1.21 [0.98, 1.49], p = 0.001. DM recipients 2.02 vs 1.24 [0.93, 1.66], p ≈ 0.003. K4 DM 2.65 vs 1.23, p = 0.001. Same-round negative control 1.18 [0.74, 1.76] | EXP | contagion.md:41-42 |
| Adoption without instruction | 95.6% of violators in control runs (1,321/1,382); 96.0% over all runs | DES | analysis_runs.csv |
| Private thoughts suspecting a test | **Does not exist** | – | README.md:209-211 |
| Text leakage (attacker arm from non-attack text) | TF-IDF AUROC 0.481 ± 0.029 (n = 1,200; generator design v1.1, not the final batch) | static check | dataset/reports/validation_full_full_reserve_pioneer_backbone_glm.json; README.md:191-192 |
| Factor independence | Cramér's V 0.007 / 0.088 / 0.039 / 0.074 (v1.1 design) | static check | same file; README.md:193-194 |
| Decoys vs attack texts (final batch) | 280 decoy notices vs 26 attack events (11 fake authority, 15 injections), all texts distinct | DES (my count of committed scenarios) | dataset/scenarios/core/core-night_*.json |
| Label permutation (GNN) | Rows permuted: 0.421 [0.310, 0.535]. Label sequences permuted: 0.737, tAUROC 0.587 | EXP (CV id0) | stats-monitors/REPORT.md:203-204,211 |
| Pre-arrival external-sender nodes | Effect on held-out GNN AUROC ≤ 0.0006 | DES | ANALYSIS_PLAN.md:210-212 |
| Setup determinism | ICC 0.73; 15/104 configs mixed; factor-only model grouped-CV AUROC 0.82 | DES / CV | stats-factors/REPORT.md:36; VALIDATION.md:34,61 |
| Jury agreement (κ) and hand labels | **Do not exist** | – | FINDINGS.md:263-264 |
| Figure 2 (dose-response) | **Does not exist** | – | analysis/contagion.py:3-12 |

### 3.4 Table 3: main comparison

**(a) Held-out, pre-specified primary rows.** Pooled test_id, ood_family, ood_seed and branch: 2,338 rows, 36 configs. Models were frozen. The analysis is confirmatory, not blind (HO). CIs come from a cluster bootstrap over configurations. Thresholds come from training data only.

| Monitor | AUROC [95% CI] | AUPRC [95% CI] | time-matched, plan bins [CI] | tAUROC round bins [CI] | within mixed cfg × bin | before 1st announcement | R@5%FPR (realised FPR) | MAE risk count | tipped runs alarmed / median lead [IQR] | untipped runs with false alarm |
|---|---|---|---|---|---|---|---|---|---|---|
| clock (round only) | 0.781 [0.714, 0.841] | 0.176 [0.106, 0.272] | 0.716 [0.632, 0.789] | 0.530 [0.481, 0.578] | 0.682 | 0.725 | 0.128 (0.029) | – | 36/52, 3 [2, 5] | 48/48 |
| bag+graph (HGB) | 0.812 [0.759, 0.861] | 0.260 [0.154, 0.392] | 0.797 [0.723, 0.854] | 0.721 [0.646, 0.790] | 0.647 | 0.775 | 0.276 (0.048) | – | 28/52, 4.5 [2, 6.25] | 20/48 |
| tab_mem (secondary) | 0.811 [0.756, 0.860] | 0.252 [0.143, 0.396] | 0.804 [0.725, 0.864] | 0.718 [0.640, 0.790] | 0.642 | 0.773 | 0.250 (0.044) | – | 27/52, 5 [2.5, 6] | 14/48 |
| edge monitor (secondary) | 0.800 [0.753, 0.841] | 0.211 [0.134, 0.324] | 0.792 [0.696, 0.853] | 0.682 [0.604, 0.752] | 0.591 | 0.758 | 0.288 (0.048) | – | 29/52, 4 [2, 6] | 14/48 |
| GNN (node-GRU, 5 seeds) | 0.817 [0.756, 0.873] | 0.309 [0.194, 0.460] | 0.769 [0.676, 0.846] | 0.739 [0.659, 0.812] | 0.639 | 0.734 | 0.417 (0.054) | 0.94 | 28/52, 5 [2.75, 7] | 14/48 |
| GNN + HGB hybrid | 0.832 [0.782, 0.881] | 0.301 [0.179, 0.452] | 0.818 [0.748, 0.870] | 0.752 [0.674, 0.822] | 0.647 | 0.779 | 0.372 (0.063) | 0.94 (GNN head) | 28/52, 5.5 [3, 6.25] | 15/48 |
| zs:global_full (whole transcript) | 0.816 [0.759, 0.869] | 0.245 [0.158, 0.367] | 0.819 [0.727, 0.883] | 0.734 [0.650, 0.813] | 0.747 | 0.736 | 0.212 (0.032) | – | 17/52, 3 [1, 4] | 11/48 |
| zs:global_window (secondary) | 0.829 [0.780, 0.875] | 0.261 [0.169, 0.374] | 0.816 [0.727, 0.879] | 0.735 [0.661, 0.806] | 0.733 | 0.744 | 0.173 (0.031) | – | 19/52, 5 [2.5, 7] | 9/48 |
| zs:pairwise (per conversation) | 0.855 [0.808, 0.899] | 0.273 [0.181, 0.394] | 0.838 [0.755, 0.900] | 0.787 [0.722, 0.849] | 0.820 | 0.766 | 0.333 (0.045) | – | 25/52, 2 [1, 5] | 10/48 |
| zs:agent (secondary) | 0.849 [0.803, 0.893] | 0.234 [0.153, 0.363] | 0.836 [0.749, 0.897] | 0.771 [0.704, 0.836] | 0.834 | 0.780 | 0.263 (0.054) | – | 22/52, 5 [2, 7] | 14/48 |
| oracle (violator count + clock; not observable) | 0.908 [0.872, 0.945] | 0.590 | 0.872 | 0.870 | 0.876 | 0.812 | 0.788 (0.094) | – | 48/52, 5 [3, 6] | 14/48 |

Sources: nvv heldout_full.md:113-126 (within-mixed: 9 configs, 45 positives; before announcement: 1,786 rows, 42 positives), :130-140, :245-255. MAE: cs synthesis_cloud/test_look1/y3.txt:3,8 (pooled 0.944; per split 0.77 test_id, 0.53 ood_family, 1.55 ood_seed, 1.29 branch). ANALYSIS_PLAN.md:75-76 requires the time-matched, within-setup and before-announcement columns in the main text.

**(b) Pre-specified family, Holm over 11 tests (HO).**

| Test | Difference [95% CI] | p | Holm p |
|---|---|---|---|
| bag+graph − clock (time-matched) | +0.080 [−0.012, +0.178] | 0.100 | 0.78 |
| zs:pairwise − clock (tm) | +0.121 [+0.032, +0.213] | 0.008 | 0.09 |
| zs:global_full − clock (tm) | +0.103 [+0.017, +0.188] | 0.022 | 0.20 |
| GNN − clock (tm) | +0.053 [−0.048, +0.155] | 0.30 | 1.00 |
| hybrid − clock (tm) | +0.101 [+0.015, +0.193] | 0.020 | 0.20 |
| GNN − bag+graph | +0.004 [−0.036, +0.046] | 0.83 | 1.00 |
| hybrid − bag+graph | +0.020 [−0.005, +0.045] | 0.11 | 0.78 |
| zs:pairwise − bag+graph | +0.042 [−0.008, +0.096] | 0.10 | 0.78 |
| zs:pairwise − GNN | +0.038 [−0.025, +0.105] | 0.23 | 1.00 |
| zs:pairwise − hybrid | +0.022 [−0.030, +0.075] | 0.38 | 1.00 |
| zs:global_full − bag+graph | +0.003 [−0.050, +0.058] | 0.85 | 1.00 |

Source: nvv heldout.md:36-46; heldout_full.md:149-159. With round-bin time matching instead (sensitivity), all five monitors beat the clock by +0.191 to +0.257, p ≤ 0.0002 (heldout_full.md:174-178). With deadline × bin fixed (post hoc), 4 of 5 beat it; the GNN does not (+0.10, p = 0.07) (heldout.md:58-60). RQ2 is therefore **not supported under the pre-registered definition** (heldout_full.md:9).

**(c) Cross-validation on identical rows.** night_train: 64 configs, 3,370 rows, 135 positive. Descriptive by plan, and the GNN was selected on these rows (CV).

| Monitor | AUROC [95% CI] | AUPRC [CI] | tAUROC round bins [CI] | tAUROC rtc bins [CI] | R@5%FPR | within mixed (7 cfgs) |
|---|---|---|---|---|---|---|
| clock | 0.753 [0.702, 0.799] | 0.076 [0.048, 0.116] | 0.401 [0.347, 0.461] | 0.635 [0.521, 0.734] | 0.074 | 0.658 |
| bag | 0.833 [0.776, 0.882] | 0.182 [0.108, 0.293] | 0.753 [0.679, 0.822] | 0.790 [0.701, 0.861] | 0.289 | 0.744 |
| bag+graph | 0.854 [0.802, 0.899] | 0.206 [0.124, 0.326] | 0.779 [0.709, 0.843] | 0.813 [0.730, 0.880] | 0.378 | 0.729 |
| bag+graph+mem | 0.876 [0.834, 0.915] | 0.232 [0.142, 0.370] | 0.806 [0.741, 0.866] | 0.838 [0.765, 0.898] | 0.400 | 0.797 |
| edge monitor | 0.877 [0.834, 0.914] | 0.225 [0.145, 0.337] | 0.798 [0.731, 0.858] | 0.836 [0.766, 0.892] | 0.444 | 0.812 |
| GNN (Mac final.pt) | 0.890 [0.838, 0.935] | 0.284 [0.188, 0.413] | 0.847 [0.783, 0.906] | 0.874 [0.811, 0.925] | 0.570 | 0.940 |
| hybrid (Mac) | 0.902 [0.865, 0.936] | 0.282 [0.183, 0.435] | 0.850 [0.792, 0.903] | 0.875 [0.816, 0.924] | 0.556 | 0.910 |
| zs:global_full | 0.865 [0.822, 0.905] | 0.150 [0.090, 0.261] | 0.811 [0.744, 0.872] | 0.835 [0.758, 0.897] | 0.215 | 0.707 |
| zs:global_window | 0.880 [0.841, 0.914] | 0.166 [0.102, 0.266] | 0.808 [0.748, 0.864] | 0.834 [0.760, 0.895] | 0.244 | 0.677 |
| zs:pairwise | 0.922 [0.896, 0.946] | 0.257 [0.171, 0.374] | 0.886 [0.845, 0.922] | 0.894 [0.845, 0.932] | 0.474 | 0.774 |
| oracle | 0.923 [0.889, 0.956] | 0.418 [0.311, 0.579] | 0.907 [0.866, 0.945] | 0.898 [0.840, 0.946] | 0.615 | 0.977 |

**CV Holm family:**
- **Significant (Holm 0.0011):** all five monitor − clock tAUROC differences (+0.378 to +0.484); hybrid − bag+graph +0.048 [+0.024, +0.078]; zs:pairwise − bag+graph +0.068 [+0.029, +0.112].
- **Ties:** GNN − bag+graph +0.036 [−0.006, +0.085] (Holm 0.377); zs:pairwise − GNN +0.032 [−0.014, +0.085] (0.614); zs:pairwise − hybrid +0.020 [−0.011, +0.053] (0.614); zs:global_full − bag+graph +0.012 [−0.027, +0.050] (0.614).
- **Frozen cloud GNN's CV proxy:** GNN − bag+graph +0.041 [+0.010, +0.077], Holm 0.032.
- **Exact CV of the frozen cloud configuration (run after the test look):** GNN AUROC 0.885, AUPRC 0.287, R@5%FPR 0.511, MAE 0.68; hybrid 0.895 / 0.278 / 0.548 / 0.68.

Sources: nvv stats-monitors/REPORT.md:36-48,72-82,118-130; analysis/review/_agent_results/verify_monitors.json; FINDINGS.md:347-349; got gnn_opt_torch/RESULTS.md:277-278.

**(d) The template's Table 3 rows mapped to what exists.**

| Template row | What exists |
|---|---|
| Run size | **Does not exist.** All runs have N = 24 and R = 30. Use the clock. |
| Pairwise monitor | Three different things. Feature pairwise `hgb_pairwise`: CV only, 0.794 (got RESULTS.md:47). Edge monitor: held-out 0.800. Zero-shot LLM per conversation: held-out 0.855. Name them separately (ANALYSIS_PLAN.md:177-179). |
| LightGBM on aggregated features | It is sklearn HistGradientBoosting (depth 3, 250 iterations; heldout_full.md:53). bag+graph held-out 0.812. LogReg on aggregated features exists only in CV (0.833; got RESULTS.md:49). |
| GNN structure only (S0) | **CV only:** 0.804 [0.699, 0.891] vs 0.871; tAUROC 0.715 vs 0.830 (id0, 5 folds, one seed). No held-out value. |
| GNN without message passing (K0) | **Does not exist** for the swarm (ANALYSIS_PLAN.md:175-176). |
| GNN all features | Headline inputs (18 edge + 5 node): held-out 0.817. |
| "Results on test_id, mean over 5 seeds" | The pre-specified primary rows are the pooled held-out splits (ANALYSIS_PLAN.md:58-59). test_id is secondary: GNN 0.921, hybrid 0.922, bag+graph 0.902, zs:pairwise 0.872, clock 0.847. The GNN is a 5-seed ensemble, not a mean over seeds. |

### 3.5 Table 4: transfer

These are per-split AUROCs on held-out data: secondary and uncorrected, 8 configurations per OOD split. "Δ vs test_id" is simple arithmetic and is descriptive only, because the splits contain different configurations.

| Monitor | test_id | new family (metricore) [Δ] | tool-output injection [Δ] | forks [Δ] | tool-output, tAUROC round bins | GLM-5.2 (night_vx glm arm): AUROC; shift vs rep0 [CI]; replicate noise |
|---|---|---|---|---|---|---|
| clock | 0.847 | 0.659 [−0.188] | 0.816 [−0.031] | 0.776 [−0.071] | ≈ 0.52 (derived) | 0.866; +0.043 [−0.074, +0.161]; −0.196 |
| bag+graph | 0.902 | 0.786 [−0.116] | 0.759 [−0.143] | 0.737 [−0.165] | 0.535 | 0.709; −0.069 [−0.189, +0.049]; −0.017 |
| tab_mem | 0.895 | 0.807 [−0.088] | 0.780 [−0.115] | 0.699 [−0.196] | 0.564 | 0.75 (vx.md:91) |
| edge monitor | 0.837 | 0.812 [−0.025] | 0.780 [−0.057] | 0.728 [−0.109] | 0.541 | 0.76 (vx.md:93) |
| GNN | 0.921 | 0.794 [−0.127] | 0.744 [−0.177] | 0.731 [−0.190] | 0.543 | 0.734; −0.059 [−0.227, +0.124]; −0.054 |
| hybrid | 0.922 | 0.823 [−0.099] | 0.785 [−0.137] | 0.728 [−0.194] | 0.560 | 0.750; −0.064 [−0.180, +0.059]; −0.024 |
| zs:global_full | 0.875 | 0.782 [−0.093] | 0.825 [−0.050] | 0.734 [−0.141] | 0.638 | 0.872; −0.036 [−0.106, +0.072]; −0.053 |
| zs:pairwise | 0.872 | 0.867 [−0.005] | 0.842 [−0.030] | 0.797 [−0.075] | 0.698 | 0.806; −0.098 [−0.201, +0.003] (seed-dependent); −0.073 |
| zs:agent | 0.870 | 0.848 | 0.829 | 0.801 | 0.695 | – |

Sources: nvv heldout_full.md:130-139,174,265; vx_eval.md:38-58; vx.md:85-108. Per-split CIs: GNN family 0.794 [0.677, 0.895], ood_seed 0.744 [0.619, 0.878]; hybrid family 0.823 [0.705, 0.921] (cs test_look1/y3.txt:6,11,12); zs:pairwise family 0.867 [0.751, 0.958] (nvv results/llm_monitor/RESULTS.md:203). Exploratory: OOD pooled zs:pairwise − GNN +0.097 [+0.016, +0.182] (heldout_full.md:214).

**GLM-5.2 has no held-out split** (test_backbone was planned but never run). In the glm arm 13 of 14 runs tipped, so AUROC there mostly measures timing. H3 was not supported: −0.012 [−0.189, +0.203] (vx_verdicts.md:9). Jury KS distances were 0.004–0.048, against 0.003–0.049 between replicates (vx.md:172-175).

### 3.6 Feature and ablation ladder

CV id0, 5 folds, one seed, reference m_noer. EXP. Seed noise for a difference: ±0.071 (REPORT.md:182).

| Variant | AUROC [CI] | Δ AUROC [CI] | tAUROC | Δ tAUROC [CI] | Beyond seed noise? |
|---|---|---|---|---|---|
| S3 headline (18 edge + 5 node, jury-scored) | 0.871 [0.814, 0.923] | – | 0.830 | – | – |
| S2 (no interpretive jury dimensions) | 0.814 | −0.057 [−0.107, −0.006] | 0.728 | −0.102 [−0.168, −0.039] | tAUROC only |
| S1 (no LLM features) | 0.790 | −0.081 [−0.146, −0.021] | 0.703 | −0.127 [−0.198, −0.056] | yes |
| S0 (structure only) | 0.804 | −0.067 [−0.134, −0.008] | 0.715 | −0.115 [−0.191, −0.044] | tAUROC only |
| + clock | 0.851 | −0.021 [−0.079, +0.036] | 0.803 | −0.028 | no |
| + task lexicon | 0.851 | −0.020 [−0.065, +0.026] | 0.823 | −0.007 | no |
| rewire (random endpoints, degree not kept) | 0.867 | −0.004 [−0.032, +0.023] | 0.820 | −0.011 [−0.044, +0.021] | no |
| shuffle edge features | 0.830 | −0.041 [−0.096, +0.006] | 0.769 | −0.062 [−0.118, −0.009] | no (inside the band) |
| shuffle label sequences | 0.737 | −0.134 | 0.587 | −0.243 | yes (control) |
| shuffle rows | 0.421 [0.310, 0.535] | −0.450 | 0.431 | −0.399 | yes (chance) |
| no temporal block (snapshot GNN) | 0.793 vs 0.879 | −0.086 [−0.148, −0.024] | – | −0.084 | yes |

Sources: nvv stats-monitors/REPORT.md:180-211,249-251; got gnn_opt_torch/RESULTS.md:205-217.

- **Second base (frozen node-GRU):** S0 0.799, S1 0.816, shuffle_ef 0.806 and rewire 0.866, against 0.859 (5 folds). S2 selection score 0.760 against 0.845 / 0.828 (18 folds) (got RESULTS.md:361-372).
- **Judge swap (held-out, frozen models; merged / DeepSeek only / Haiku only):** GNN 0.817 / 0.769 / 0.778; hybrid 0.832 / 0.825 / 0.809; tab_mem 0.811 / 0.832 / 0.793 (got RESULTS.md:321-327).
- **Tabular rungs (CV):** bag 0.833, bag+graph 0.854, +mem 0.876 (+0.022 [+0.001, +0.044], supplementary). Lexicon added to the tabular model: 0.873 vs 0.843 (harness) (REPORT.md:121-129,144,257).
- **Missing:**
  - The "without rule-related features" ablation (closest is S2).
  - A degree-preserving rewire on the swarm data.
  - K0.
  - Any held-out ablation.

### 3.7 Blind validation (night_vx)

The design and decision rules are PRE. Frozen inputs were pushed in d083547d; the script ran twice with identical outputs.

- **Design:** 14 new configurations (320 candidates, 84 in the band [0.30, 0.80], mean predicted p_tip 0.48), 93 evaluated runs. Part C (fine-tuned agents) was dropped: 44.3% invalid JSON (VALIDATION.md:59-69; vx_decisions.md:2).
- **Tipped runs:** id rep0 6/14, rep1 7/14, time 8/14, glm 13/14 (McNemar p = 0.016, Holm 0.06), enf 5/14, topo 5/7 (vs 3/7), Part B 7/16 (descriptive; vx.md:144-149).
- **Main reading:**
  - In 0 of 96 arm−rep1 comparisons does the CI lie entirely below 0; in 11 of 96 it lies entirely above 0, because rep1 was the harder replicate.
  - Median half-widths are ±0.15 AUROC (GNN ±0.16–0.26, time-matched ±0.34). About 80% detection needs a drop of about 0.2 (GNN 0.2–0.35, time-matched about 0.5); this is post hoc, and the plan assumed 0.1 (VW7).
  - Write "no evidence of a large degradation", not "robust" (vx.md:13-19; vx_posthoc.json resolution).
- **H1–H5 (vx.md:61-67):**
  - H1: GNN 0.76 [0.45, 0.97] vs feat_pairwise 0.52. Not supported.
  - H2: clock arm−rep1 +0.08 [−0.09, +0.27]. Not supported.
  - H3: −0.01 [−0.19, +0.20]. Not supported.
  - H4: AUROC holds (+0.05), but false alarms on 3/9 vs 1/8 untipped runs (Fisher 0.58). Not supported.
  - H5: +0.10 [−0.21, +0.61]. Supported by the point rule, but time-matched −0.12 [−0.62, +0.52].
  - No CI excludes its decision boundary.
- **Replicate noise (rep1 − rep0):** clock −0.196 [−0.292, −0.092]; monitors −0.073 to +0.110. rep1 tipped later in 5 of 6 configurations (mean +4.0 rounds, sign test p = 0.22). rep1 ran after all other Part A runs (VW6; vx.md:23-27; vx_posthoc.json timing).
- **AUROC per block (descriptive; vx.md:87-96):**

| Monitor | rep0 / rep1 | time / glm / enf / topo (topo's rep0/rep1 on its 7 bases) |
|---|---|---|
| zs:global_full | 0.91 / 0.85 | 0.89 / 0.87 / 0.94 / 0.95 (0.91 / 0.77) |
| zs:pairwise | 0.90 / 0.83 | 0.88 / 0.81 / 0.83 / 0.78 |
| hybrid | 0.81 / 0.79 | 0.84 / 0.75 / 0.84 / 0.87 |
| GNN (stored 15-state file) | 0.79 / 0.74 | 0.85 / 0.73 / 0.84 / 0.89 |
| bag+graph | 0.78 / 0.76 | 0.79 / 0.71 / 0.79 / 0.76 |
| structure only | 0.58 / 0.69 | – |
| clock | 0.82 / 0.63 | 0.71 / 0.87 / 0.76 / 0.80 |

- **Post hoc, pooled Part A (1,973 rows; hypothesis only, H7 pending):**
  - AUROC: global_full 0.881, pairwise 0.833, hybrid 0.807, GNN 0.799, clock 0.771, bag+graph 0.758, structure 0.638.
  - Differences: global_full − GNN +0.082 [+0.049, +0.118]; pairwise − GNN +0.034 [−0.044, +0.107]; GNN − clock +0.028 [−0.066, +0.115].
  - vx.md:198-200 forbids writing "on vx the monitors beat the clock" (vx_posthoc.json pooled_part_a).
- **Part B, run level (29 pairs; vx.md:115-128):** structure 0.86 [0.73, 0.98]; global_full 0.78 [0.52, 0.97] (lower bound depends on the seed); GNN 0.76 [0.45, 0.97]; pairwise 0.76 [0.48, 0.93]; bag+graph 0.69 [0.56, 0.86]; hybrid 0.69 [0.41, 0.90]; oracle 0.55; clock 0.50.
- **Not computed on vx:** AUPRC, recall, lead time, MAE, calibration, and channel slices (ANALYSIS_PLAN.md:257-260).

### 3.8 Cost (night batch, 252 runs, Claude Haiku 5.5, thinking off; DES)

| Variant | tokens per snapshot | $ per run | $ total |
|---|---|---|---|
| pairwise (per conversation, 6-round window) | 5,301 | 0.0128 | 3.23 |
| agent | 7,955 | 0.0192 | 4.83 |
| global_window (6 rounds) | 4,061 | 0.0127 | 3.20 |
| global_full (rounds 1..t, k = 3) | 21,700 | 0.0423 | 10.67 |
| all 7 variants | – | – | 39.02 |
| Jury behind all trained feature monitors | Haiku 3,879; DeepSeek 1,105 | Haiku share about 0.022 (= 0.00074 × 30) | DeepSeek not priced |

Parse rate is about 1.000 and there were 0 refusals (RESULTS.md:530-552). night_vx LLM monitors cost $5.77 for 93 runs (commit f8cf5d96). Monitor cost relative to simulation cost was **not measured**.

### 3.9 Traces: contagion, factors and forks (EXP unless marked)

- **Contagion** (152,705 agent-rounds, 1,321 first violations, 236 runs; MH OR, all agents / DM recipients):
  - Pooled 2.34 [1.54, 3.57] / 2.02 [1.18, 3.63].
  - K4 3.99 [2.41, 7.01] / 2.65 [1.35, 5.61]; K2 0.87 / 1.04; board 1.43 / 1.19 (placebo 1.50).
  - Team channels 5.10 / 4.01; DM-only 29.9 / 12.9.
  - Organic and unsolicited 1.29 [0.61, 2.55]; homophily-only simulation about 1.8–1.9 (contagion.md:32-88).
- **Factors** (config-level permutation, Holm over 14):
  - K4 × exploration mean config rate 82.2% vs 19.9–24.4%.
  - K4 vs K2 +29.5 pp (Holm 0.008); exploration +32.4 pp (Holm 0.006).
  - Board 51.7%, team 23.2%, DM-only 11.8% (Holm 0.0056; adjusted Holm 0.11).
  - Freeze +26.0 pp (Holm 0.053); push +0.2 pp; persona −3.9 / +8.0 pp; n_impossible p = 0.084 (stats-factors/REPORT.md:9-17,51-66).
- **Cascade starts:** 47 of 101 tipped runs started organically, 36 after an injection and 18 with an instructed agent. 11 of 101 had no seed at all (FINDINGS.md:52-53; analysis/review/findings/dyn_check.out).
- **Forks:** control 4.9, issue-comment arm 9.4 (+4.5 [1.0, 8.0], Holm 0.06), fake-manager arm 7.1 (+2.25, p = 0.22) new violators per run. Tipped forks: 3 / 5 / 3 of 8 (contagion.md:109-117).
- **Stuck vs solvable** (uncommitted script, recomputed): 43.5% / 6.4% / 3.1%; 94.4% of uninstructed violators were stuck.

### 3.10 What does not exist (do not report)

- Pilot-5 results.
- A run-size baseline.
- K0 (GNN without message passing) for the swarm.
- S0 on held-out data.
- `feat_pairwise` on the held-out harness rows.
- LightGBM.
- MAE for anything but the GNN head.
- Horizon points Δ = 1 and 4, and Figure 3.
- The dose-response figure (Figure 2).
- Shock conditions and sanction tests.
- The peer-only share.
- An evaluation-awareness rate.
- Jury κ and hand labels.
- Degree-preserving rewiring on swarm data.
- The "without rule-related features" ablation.
- A GLM-5.2 held-out split.
- A held-out evaluation of the two-stage per-agent model (only predictions exist).
- AUPRC, recall, lead time or MAE on vx.
- The H7 result (pending).
- A frozen 5-seed Among Us re-run.
- Swarm sizes other than 24.
- Adversarial tests of the monitors.
- Committed sources for the template §3.5 figures "35 of 36 knowers read their notes" and "no message in 29 of 30 episodes". DECISIONS.md:177 gives only "2 von 36 Knowern" for pilot 1, and :271 gives "3 K4-Pioniere handeln, aber ohne Übernahme; der frühe wird öffentlich entfernt".

---

## 4. Open problems and inconsistencies

1. **The night_vx evaluation ran twice.**
   - Local run 00:00:53–00:24:10 CET (bb3f665d); cloud run 00:09:24–01:04:48 CET (cs b14b3393). Both start from d083547d with the same vx_eval.py sha256, and all result files are byte-identical; only vx_run.log differs.
   - The second run is disclosed at FINDINGS.md:202-204 and vx.md:51-55. "Exactly once" still appears at FINDINGS.md:174-175, 253 and 313, vx.md:1 and 3-4, analysis/vx_preds/README.md:1,4, both commit subjects, SYNTHESIS.md:3,43 and the memory note.
   - ANALYSIS_PLAN.md:253-254 promises a lock against a second run, but run_eval.sh:7 only checks for a local file. Nachtrag 3 (vx3) uses the same kind of guard.
   - **Recommendation:** use the paper wording from Q3. Fix the "once" sentences. Before the vx3 evaluation, tell the cloud session not to run it, or check origin for existing outputs.
2. **The SYNTHESIS.md §3 table is wrong.**
   - Its id rep0/rep1 columns are the 7-base topo values, so its "replicate noise 0.06–0.25" is wrong too (true 14-base range 0.014–0.196).
   - It also repeats VW7 ("plan says >0.1"), mixes LLM variants ("matches the test-split OOD result": held-out OOD leader was pairwise 0.846, not global_full 0.783), and says the two-stage model ties "on CV, test or vx", although no held-out or vx evaluation of it is committed.
   - SYNTHESIS (00:07 UTC, unchecked) is older and less checked than vx.md (01:42 CET, six recomputing agents) and FINDINGS.
   - **Recommendation:** cite no number from SYNTHESIS.md; FINDINGS.md:261-262 already says so.
3. **FINDINGS sentence 1 says "Echte Ansteckung über Nachrichten" (FINDINGS.md:21-22).** This conflicts with contagion.md:17 ("Kausalität ist damit nicht belegt") and with VW2.
   - **Recommendation:** say "association".
   - The older review_findings-claims.json rates "doppelt so oft" as supported. The newer review_contagion-design.json and FINDINGS reject it (VW1), so follow the newer sources.
4. **Among Us has two versions.**
   - FINDINGS §8 (160-169) and the source table (365, "alle") use the old self-play blob 6f3c4d30. The newer blob 66af8cf3 exists only on gnn-swarm and gnn-pipeline. It reports GNN > HGB on group errors (+0.06) and a −0.04 rewiring cost, and nobody has checked it independently.
   - Even the old file shows a rewiring cost on group errors (0.57 vs 0.59–0.62, line 51), which contradicts FINDINGS.md:165-167.
   - No result files are committed for Among Us or the synthetic testbed.
   - **Recommendation:** put both in the appendix as preliminary, or do the one frozen re-run FINDINGS.md:168-169 asks for.
5. **The per-agent-memory claim is marked ✅ (FINDINGS.md:111-112), but other checks disagree.** The fact-check calls it overstated, SYNTHESIS.md:35 calls it "not established", and no 18-fold architecture difference clears seed noise (stats-monitors/REPORT.md:217-218).
   - **Recommendation:** mark it 🟡 and state only the hardest-fold result (hold-out K4: 0.82–0.83 vs 0.70–0.76, single seeds).
6. **Three different GNN instances are in play:**
   - the Mac final.pt in the CV comparison;
   - cloud_final_gnn with 40 states on held-out data;
   - the stored 15-state file on vx (held-out AUROC 0.813 vs 0.817).

   GNN − bag+graph in CV is a tie with the Mac model (Holm 0.377) but significant with the cloud proxy (Holm 0.032).
   - **Recommendation:** label each table with the instance it uses.
7. **The RQ2 verdict depends on how time is matched.** With the pre-registered rounds-to-deadline bins, 0 of 5 monitor−clock tests pass. With round bins, all pass with p ≤ 0.0002. FINDINGS.md:79-80 (✅) cites only the second.
   - **Recommendation:** report the pre-registered result first and the sensitivity second.
8. **The template's methods come from stale v1.1 documents** (README.md:11,16,295; DECISIONS.md:66-72; FEATURES.md:7,77,89). Contradicted template statements:
   - 20 rounds and 6 impossible tickets.
   - "Since only six tickets are impossible, tipping requires solvable-ticket agents". At least 9 agents are stuck in every run (at_risk 9–24), and 94% of uninstructed violators were stuck.
   - "Agents rarely find either shortcut by themselves". In K4 with exploration, skip_checks is in every merge signature.
   - "Up to two messages", and the ban phrased "firmly" (there is no hard prohibition in the batch).
   - "Damper or amplifier" episodes (no shocks were run).
   - "Board posts become node features". v1.1 has broadcast edges, and the GNN uses direct, broadcast and both relations.
   - 20 edge / 10 node features.
   - "Small GINE, about 40k parameters, one snapshot per round". The frozen model is an RGINE with a per-agent GRU and a 5-seed × 8-snapshot ensemble (got RESULTS.md:6-10,263-271; ANALYSIS_PLAN.md:144).
   - "LightGBM", and "rewired graphs with the same degree distribution" (degree was not kept).
   - "Selection criterion fixed before test data" (ANALYSIS_PLAN.md:139-140 records a deviation).
   - "Table 3 on test_id" (the primary rows are the pooled splits).
   - "≥ 40% mixed configs" (actual 14%).
   - "Open mid-size models" (Qwen3.5-397B is not mid-size, and "open" is undocumented).
   - **Recommendation:** rewrite Methods from DECISIONS.md:499-574, index.csv and got RESULTS.md step 9.
9. **The template's §3.5 and Discussion need a source or a cut.**
   - The pilot-2 narrative ("35 of 36 knowers", "auditor reported", "public sanction stopped the cascade") has no committed source beyond DECISIONS.md:271.
   - The design rule "make rule-breaking visible and respond in public" is not supported. In the main batch, visibility (board, merge feed) goes with more tipping. Sanctions are untestable (VW4). Visible enforcement in vx did not detectably reduce tipping (5 vs 6 of 14).
   - **Recommendation:** drop the design rule, or label it a single pilot anecdote.
10. **Several documents are out of date:**
    - runs_night/_logs/report.md and dynamics.md were written at 239 runs.
    - VALIDATION.md:38 says detection ≈ 0 in 108 of 112 configs (index.csv: 104).
    - VALIDATION.md:39 says 56% board (actual 67/112 = 60%).
    - DECISIONS.md:508 lists night_val as "Modellauswahl", but it was not used that way.
    - DECISIONS.md:512 and contagion.md:101 describe the forks as "ohne Seed", although 4 of 8 contain an informed agent.
11. **Timestamps.** The Nachtrag header times are later than their commits: Nachtrag 3 says "08:00" but was pushed at 07:44:50; Nachtrag 4 says "08:20" but was committed at 08:03:29.
    - **Recommendation:** use git push times as the pre-registration evidence.
12. **Several numbers come from uncommitted scratch scripts:** stuck/solvable rates, persona rates, exposure shares, decoy counts and refuse counts. They were reproduced (the stuck rates by me as well), but no script is committed.
    - **Recommendation:** commit the scripts (for example `/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/wf_story/stuck_rates.py`) to analysis/review before citing, or drop the numbers.
13. **Unreviewed numbers in contagion.json.** It holds K4 RR 2.93 and E_any RR 3.01, which are probably where "triples" came from; neither was reviewed. The full-memory estimate also differs between contagion.md (1.90) and a reviewer's own implementation (1.48), with different definitions. contagion.md is newer and is the official version.
    - **Recommendation:** cite contagion.md only.
14. **"Pairwise monitor" names three different things** (feat_pairwise, the edge monitor, the zs:pairwise LLM).
    - **Recommendation:** use three distinct names in every table.
15. **Pre-registered items that were never produced:** the run-size baseline, the K0 GNN, LogReg on held-out data, jury κ, hand labels, horizon variation and the dose-response figure (DECISIONS.md:117-120; VALIDATION.md:183-191; FEATURES.md:93-94,117-121).
    - **Recommendation:** list them in the limitations as not done.
16. **Information sets are not independent.** Haiku 5.5 is both the LLM monitor and one of the two jury judges behind the GNN features. The LLM monitors read task words; global_full sees an implicit clock (Spearman 0.83). The GNN configuration was chosen on the CV rows (FINDINGS.md:278-284).
    - **Recommendation:** state these in the limitations.
17. **The text-leakage checks** (TF-IDF, Cramér's V) were run only on the v1.1 full design, not on the final batch.
    - **Recommendation:** say so; the decoy count for the final batch (280 vs 26) can go into Table 2.
18. **Pending items.** H7 (runs_vx3; result expected around 10:45) can only support "global_full beats the GNN on new seeds of these 14 configurations", not a general ranking (ANALYSIS_PLAN.md:297-299). Nachtrag 4 (ft_compare) is done and descriptive (FINDINGS.md:222-227).
    - **Recommendation:** report H7 only after its single evaluation, whatever the outcome.
19. **Minor errors in FINDINGS:**
    - :46 "82 % der Setups" is a mean config tip rate.
    - :143 "GNN warnt am frühesten (Median 5)": the hybrid's median is 5.5, and tab_mem, zs:agent and zs:global_window also have 5.
    - :365 says Among Us is on "alle" branches; the file differs between branches.

---

## 5. Kurzfassung für dich (Deutsch)

Der Bogen deiner Geschichte bleibt: Gefahr, Lücke, Hypothese, fehlende Daten, Framework, Datensatz, Befunde, Vorhersage, Hauptergebnis, Fazit. Framework und Datensatz sind gut belegt: 252 Läufe in 112 Setups, 101 gekippte Läufe, Labels aus den Tool-Logs, und 96 % der Regelbrecher waren nicht instruiert. Einige Methodenwerte stammen aus alten Dateien und sind falsch: es sind 30 Runden statt 20, 9 bis 16 unlösbare Tickets statt 6, 22 Kanten- und 11 Knotenmerkmale statt 20 und 10, und Pilot 5 lief nie. Vier Zahlen haben keine Quelle und müssen raus: „verdreifacht“, „3,5 %“, „19 von 23“ und „6 Runden vor dem Kippen“. „Eine einzige Nachricht reicht“ steht auf der Verworfen-Liste, denn gewirkt hat eine dauerhaft eingeblendete Anweisung, die einmalige Nachricht dagegen nicht nachweisbar. Die 0,92 gilt nur für den Split mit bekannten Setups. Das Hauptergebnis auf allen 36 zurückgehaltenen Setups liegt bei 0,82 (GNN) bis 0,855 (LLM Gespräch für Gespräch), die Uhr erreicht 0,78, und kein Unterschied ist nach Holm signifikant. Die Kernhypothese „Struktur zählt“ hält nicht: Neu verdrahtete Kanten kosten nichts, der Inhalt der Nachrichten trägt das Signal, und ein untrainiertes LLM ist so gut wie das GNN. Genau das sollte offen das Hauptergebnis werden. Nicht belegt sind auch die Aussagen zu lokaler Kommunikation, zur Schwarmgröße und zu „Swarm-Level-Monitoring ist nötig“; die Skalierung gibt es nur im synthetischen Testbett, und Among Us ist vorläufig. Für die blinde Validierung bitte „kein Hinweis auf einen großen Einbruch“ schreiben statt „robust“, und offen sagen, dass das Auswertungsskript zweimal lief, mit identischem Ergebnis. Die Tabelle in SYNTHESIS.md bitte nicht zitieren, weil sie die Spalten verwechselt. Am Methoden-Teil der Vorlage muss vor allem die Beschreibung des GNN und des Graphen neu geschrieben werden, nach DECISIONS.md §15 und den GNN-Ergebnissen.