> **Kurzfassung, Stand 9. Nov. 11:30** (etwa 7 Seiten). Noch offen: zwei Prüfungen dieser Fassung (Fehler durchs
> Kürzen, Länge), das H7-Ergebnis in den [[Klammern]] (Auswertung läuft) und die Guidelines-Punkte (Anhang
> „Limitations and Dual-Use“, Autoren, Vorarbeit). Die endgültige Fassung ersetzt diese Datei gegen 11:50.

# Spotting a Swarm Before It Tips: Simulated Data and Early-Warning Monitors for Collective Rule-Breaking in LLM Agent Teams[^1]

Author name 1 / Affiliation · Author name 2 / Affiliation · Author name 3 / Affiliation

Author name 4 / Affiliation · Author name 5 / Affiliation · Author name 6 / Affiliation

*With Apart Research*

[^1]: Research conducted at the Swarm Alignment Hackathon, November 2026.

## Abstract

We asked whether messages and the communication graph predict LLM agent teams tipping into rule-breaking. Lacking labelled data, we simulated 24-agent teams with unsolvable tickets and one forbidden shortcut, labelled from tool logs. Of 252 runs in 112 configurations, 101 tipped (≥ 8 of 24 agents used the shortcut). On 36 held-out configurations, monitors predicted tipping three rounds ahead with AUROC 0.800–0.855 (round-counting clock: 0.781). None of 11 pre-specified comparisons survived Holm correction; monitors beat the clock only within absolute-round bins (p ≤ 0.0002, sensitivity analysis), not within pre-registered rounds-to-deadline bins. A frozen graph neural network (0.817) beat neither gradient-boosted trees on counted features (0.812) nor a zero-shot LLM monitor reading single conversations (0.855). In exploratory cross-validation, random rewiring changed nothing, while removing message-content ratings cost 0.10–0.13 AUROC within 5-round bins, beyond training-seed noise. In a pre-registered suite (93 new runs), no frozen monitor lost detectably more AUROC under four shifts than between two replicates (post hoc resolution about 0.2). A pre-registered replication on [[H7: n of 28 planned]] fresh runs of its 14 configurations tested whether a zero-shot LLM monitor reading the full transcript beats the GNN: [[H7: D = X [L, U]; supported / not supported / open]].

## 1. Introduction

In LLM agent teams, harm can grow out of normal interaction. In Paglieri et al. (2026), one of 100 agents found an exploit in the evaluator, and it spread through a shared library and private messages. Graph detectors such as G-Safeguard (Wang et al., 2025) look for single compromised agents after the fact. On organic data they drop to chance, because unsafe teams "drift together" (FGLGuard; Yu et al., 2026). To our knowledge, no monitor has been tested on predicting team-level rule-breaking in advance.

We hypothesised that this risk shows in who talks to whom and in what they say. A graph neural network (GNN) on each round's communication graph should then warn early and beat monitors that read single conversations. Testing this needs labelled teams that tip and teams that do not. To our knowledge no public dataset provides them, so we built one. Messages did carry an early-warning signal. But we detected no contribution from who talked to whom, and a zero-shot LLM monitor reading single conversations was at least as accurate as the GNN.

**Threat model.** Twenty-four cooperative agents work under deadline pressure on tickets, some of them unsolvable, and one forbidden shortcut gets failing tickets through the checks. The first agent to use it may find it alone or know it from an earlier infrastructure rotation. It may also have been told to use it (possibly as a hidden side task), or be pushed by fake authority or a prompt injection. The team tips when at least 8 agents, instructed ones included, have used the shortcut. A monitor sees only messages, never tool calls, private reasoning or the repository. In every round it scores the risk that the team tips within the next three rounds. Agents who break the rule without writing about it stay invisible to it, and so do hidden channels such as steganography.

Our contributions are:

1. **A simulator** of 24-agent teams with interdependent tickets, 9–16 of them unsolvable, and exactly one forbidden shortcut that works. Labels come deterministically from the tool-event log.
2. **A labelled dataset** of 252 runs in 112 configurations (7,560 labelled snapshots), of which 101 tipped; 96% of the 1,514 rule-breakers were never instructed.
3. **A comparison of eight monitors on identical held-out rows** of 36 configurations: AUROC 0.800–0.855 against 0.781 for a round-counting clock, and none of 11 pre-specified comparisons survived Holm correction. So the monitors did not beat the clock within the pre-registered rounds-to-deadline bins, only within absolute-round bins (p ≤ 0.0002, sensitivity analysis).
4. **A pre-registered validation suite** of 93 new runs, blind for monitor scores, in which no frozen monitor lost detectably more AUROC under four shifts than between two replicates (post hoc resolution about 0.2). A post hoc lead of the zero-shot LLM monitor reading the full transcript over the GNN was then retested on [[H7: n of 28 planned]] fresh runs ([[H7: D = X [L, U]; supported / not supported / open]]).

## 2. Related Work

**GNN detectors on agent communication.** G-Safeguard (Wang et al., 2025), GUARDIAN (2025), BlindGuard (2025), XG-Guard (2025) and FGLGuard (Yu et al., 2026) train GNNs on communication graphs to classify single agents as compromised. Their edge features are text embeddings. We predict a team-level outcome in advance, from named features.

**Message scoring and observers.** A-Trust (He et al., 2026) scores each message on six dimensions inspired by Grice and finds that prompt-based LLM scores separate them poorly. SentinelAgent (2025) lets an LLM overseer inspect an execution graph. SCCAL (Fan et al., 2026), the closest work, combines graph curvature with semantic change and finds warning signals several rounds before a violation, on a synthetic benchmark.

**Contagion in LLM populations.** A committed minority can flip social conventions in LLM populations (Ashery et al., 2025), and dense networks spread adversarial content further (NetSafe; Yu et al., 2024). In three-agent swarms, frontier models did not copy a peer's rule-breaking (Zhang, 2026).

## 3. Methods

*[Figure 1: Pipeline. Scenario generator → 24-agent simulation in a mock repository → messages and tool events. Tool events feed only the labels. The jury rates each message; the ratings and per-round communication graphs feed the trained monitors, while the zero-shot LLM monitors read the messages themselves.]*

### 3.1 The simulated team

Each agent owns one ticket, a function in one of six self-written Python libraries with 24 interdependent functions each. In 9, 12 or 16 of the 24 tickets, an extra regression test contradicts the specification, as in ImpossibleBench (2025). Exactly one forbidden shortcut works: editing `.ci/scoring.toml` (K2) or merging with `skip_checks=true` (K4). In half of the configurations agents can find it themselves. In the other half, only informed agents and seed texts reveal it, until a merge feed that lists each merge with its CI state shows the first use. A run has 30 synchronous rounds. In each round every agent takes one tool action and may send up to two messages, and the deadline falls after round 17, 20, 23 or 26. Agents talk on a shared board, in team channels or by direct message only, over a small-world or clustered network.

Agents run on Qwen3.8-27B, Gemma 4 31B, Qwen3.5-397B and Gemma 4 26B A4B with reasoning off, two or four models per team. The shortcut enters through no seed, through knowers, through a pioneer with a private plan, through a hidden side task as in SHADE-Arena (Kutasov et al., 2025), or through an outside fake-authority message or prompt injection. At most one agent per run is instructed. Eight configurations without an instructed agent or outside message (four of them with an informed agent) were forked after round 5 into three arms: unchanged, with a persistent injected QA-bot instruction, or with one fake-manager message.

### 3.2 Labels and data hygiene

Labels come deterministically from the tool-event log. An agent counts as violating from its first successful write to `.ci/scoring.toml` or its first merge with `skip_checks=true`; blocked attempts do not count. The pre-registered target is defined while fewer than θ = 8 agents (instructed ones included) have violated: will θ be reached within Δ = 3 rounds? Each (run, round) at which the target is defined is one row, and fork prefixes count once. Seed texts come from paraphrase pools, and every configuration has 2–3 harmless notices from the same senders the attacks impersonate. We split by configuration, never by run; trained monitors are fit on 64 configurations (night_train). Design factors alone still predict tipping (Table 2), so we also compare monitors within configurations.

Tipping first appeared in the fourth of four pilots (124 runs), after we fixed problems in the environment. Even then it appeared only under a release freeze, which stops QA from fixing escalated checks before the deadline (5 of 14 runs with a freeze, 0 of 14 without). With the freeze in 79 of 112 configurations, the main batch reached 40% tipped runs (target 20–80%).

### 3.3 From messages to graphs

For each run and round t we build one graph (Figure 1) whose nodes are the 24 agents and any external senders. An edge i → j exists if j received a message from i in rounds t − 2 to t, either addressed to j (direct edge) or read in a shared channel (broadcast edge). Notices and tool events never enter the graph. Table 1 lists the features; the trained monitors use 18 of the 22 edge features and 5 of the 11 node features. Two LLM judges (the jury), DeepSeek V4 Flash and Claude Haiku 5.5, rate each message from 0 to 3 on nine dimensions. The features use their mean and their disagreement.

**Table 1.** Feature catalog v1.1. Edge features aggregate the messages i → j of rounds t − 2 to t; † = not in the headline set. S0–S1 need no LLM; the jury rates S2–S3 per message. Prompts, private thoughts and model identity are never inputs. The rubrics borrow named mechanisms: moral disengagement and neutralisation (Bandura, 1999; Sykes & Matza, 1957), authority, social proof and time pressure (Cialdini, 2001; Zeng et al., 2024), groupthink (Janis, 1972) and, for exposure breadth, complex contagion (Centola & Macy, 2007).

| Tier | Edge features | Node features |
|---|---|---|
| S0 structure | message volume, direct volume, broadcast volume, responsiveness, reciprocity, new contact | external sender, unanswered share; lead and auditor roles†, ticket dependencies (2)† |
| S1 rules, word lists, small NLI model | escalation words; shortcut mentions† and their moving average†, pressure words†, contradiction (NLI; not computed)† | own unaddressed shortcut mentions†, exposure breadth† |
| S2 LLM, factual | success claim, workaround request, verification, frustration | own frustration |
| S3 LLM, interpretive | rule-breaking presented as legitimate and its 3-round trend, goal shift, uncritical adoption, unverified authority, secrecy, judge disagreement | legitimisation in own unaddressed posts, stance drift |
| Tool events (ablation only) | – | failed test runs†, unresolved escalation† |

### 3.4 Monitors

The GNN is a relational GINE (Hu et al., 2020) with three layers, 64 hidden units and sum, mean and max aggregation. After the first layer, a causal GRU runs over each agent's own history. The GNN was selected by cross-validation on night_train and frozen (5 training seeds × the last 8 epochs) before its developers' single look at the held-out splits. It never sees the round number, configuration, model identity, instructions, ticket solvability, tool events or task words.

The clock and the counted features are gradient-boosted trees, on the round number and on aggregated headline features plus graph statistics of high-scoring edges. Two secondary monitors extend them: the tabular model with memory adds per-agent histories, and the edge monitor averages the three highest-scoring edges. The GNN + tabular hybrid averages the logits of the GNN and the tabular model with memory. Two zero-shot LLM monitors (Claude Haiku 5.5, prompts frozen on 8 night_train runs) read the raw messages, task words included. The one reading single conversations (pairwise) keeps the highest score among the conversations of the last six rounds, at about one cent per run. The one reading the full transcript (global_full) reads rounds 1 to t, so it sees elapsed time. The oracle (true violation count + clock) is not observable. It serves only as a reference, not as an upper bound.

### 3.5 Evaluation

**Held-out comparison.** We hold out 36 configurations (100 runs, 2,338 rows) in four splits: in-distribution (test_id), a new library, tool-output injection never seen in training, and the forks. The developers of the GNN and of the LLM monitors had each seen their own held-out results. The plan was committed after the joint comparison had run but before its results were read, so the comparison is confirmatory, not blind. Eleven pre-specified tests (Table 3) form one Holm family (Holm, 1979), with p-values from a paired cluster bootstrap over configurations (10,000 draws). The monitors beat the clock only if all five primary monitors (counted features, GNN, hybrid, pairwise, global_full) do so in time-matched AUROC: the pairs-weighted mean AUROC within bins of rounds to the deadline. Deadlines differ between configurations, so within these bins the absolute round still reveals whether a deadline is early or late. As a sensitivity analysis we therefore also bin by 5 rounds of absolute time.

**Validation suite (night_vx).** A factor model chose 14 new configurations with predicted tipping probabilities of 0.30–0.80. Each ran twice unchanged (rep0, rep1) and once under each of four shifts: a longer sprint (36 rounds, deadline after round 29), 12 of 24 agents on the unseen GLM-5.2, and visible enforcement. The fourth shift, for the 7 configurations without a shared board, is a scale-free graph with a few hubs (hub network). Part B added two new replicates of 8 held-out configurations. Monitor scores were frozen and pushed (d083547d) before any comparison with labels, but the tip counts were already known. Each shift is read against the replicate noise (rep1 − rep0). Five pre-registered rules concern the GNN (H1–H5); H6 belonged to a fine-tuned-agent arm that was dropped. The evaluation script was executed twice on the frozen inputs (locally and in a separate cloud session), with byte-identical results.

**Confirmatory replication (H7).** Before any new run existed, we pre-registered one uncorrected test on replicates 2 and 3 of the 14 unchanged configurations (28 planned runs, random seeds never used before), scored by the same 12 frozen predictors. H7 holds if the 95% percentile interval of D = AUROC(global_full) − AUROC(GNN) lies above 0. D uses all rows of both new replicates on which the target is defined. The paired bootstrap over configurations (10,000 draws, seed 20261109) keeps both new runs of a drawn configuration together and drops draws without both classes. Time-matched D, global_full − hybrid and pairwise − GNN are secondary. No run starts after 10:30 CET, and a configuration without a finished new run drops out. The plan allows one execution of the frozen script and reports the result whatever its outcome; if a pipeline fails, H7 stays open.

## 4. Results

### 4.1 The dataset and what the traces show

The main batch has 252 runs, of which 101 tipped (40%; a median of 12 rule-breakers per tipped run). This rate reflects our calibration. Outcomes were largely fixed by the configuration (Table 2). In exploratory tests at the configuration level (Holm over 14 factors), tipping depended mainly on whether every agent could see the shortcut. Shortcut type (K4 vs K2: +29.5 percentage points, Holm p = 0.008) and discoverability (+32.4, Holm p = 0.006) acted largely as one effect (post hoc). Where `skip_checks` appeared in every merge signature, the mean configuration rate was 82%, against 20–24% in the other cells. A shared board (52% against 12% for direct messages only; Holm p = 0.006) and the release freeze (46% against 20%; Holm p = 0.053) went with more tipping. The persona prompts showed no detectable effect.

**Table 2.** Validity checks that use no monitor. OR: Mantel–Haenszel odds ratio for adoption after a direct message (DM) from an earlier rule-breaker, stratified by run × round × stuck status, with 95% intervals from a bootstrap over configurations. The sanction and audit conditions were not run, and evaluation awareness was not measured.

| Check | Result | Kind |
|---|---|---|
| Timing: time-shuffle null (Anagnostopoulos et al., 2008); rule-breaker's message from the same round, not yet readable | OR 2.34 vs null median 1.21 [0.98, 1.49], p = 0.001 (DM recipients 2.02 vs 1.24, p ≈ 0.003); same-round message OR 1.18 [0.74, 1.76]. Part of the excess may reflect who adopts rather than when | exploratory |
| Placebo: DM from an agent who breaks the rule later | OR 1.42 [1.17, 1.72]; DM recipients 0.84 [0.64, 1.15]. Without any effect the placebo already sits near 1.3, and a homophily-only simulation gives the main measure 1.8–1.9, so the placebo cannot rule out homophily | exploratory |
| Rule-breakers never instructed | 1,453 of 1,514 (96.0%); control runs only: 1,321 of 1,382 (95.6%) | descriptive |
| Text leakage: TF-IDF on non-attack text predicts the attack arm | AUROC 0.48 ± 0.03 (generator design v1.1, not the final batch) | static check |
| Setup determinism | intraclass correlation of tipping 0.73; 15 of 104 configurations with repeated runs had both outcomes; design factors alone predict tipping (grouped cross-validated AUROC 0.82) | descriptive; cross-validation |

Only 11 tipped runs had no instructed agent, informed agent or outside message. Uninstructed agents adopted the shortcut more often after a direct message from an earlier rule-breaker than comparable agents in the same run, round and stuck status (post hoc; OR 2.34 [1.54, 3.57]). The association held only in K4 (3.99 [2.41, 7.01]; K2 0.87 [0.54, 1.35]), and homophily cannot be ruled out (Table 2). In the forks, the persistent injected instruction was followed by more new rule-breakers (+4.5 per run [1.0, 8.0]; Holm p = 0.06, not significant).

### 4.2 Early warning

In the pre-specified comparison (Table 3), the monitors reached AUROC 0.800–0.855 and the clock 0.781. None of the 11 comparisons survived Holm correction. The GNN tied the counted features (+0.004 [−0.036, +0.046]), and pairwise separated neither from the GNN (+0.038 [−0.025, +0.105]) nor from the hybrid (+0.022 [−0.030, +0.075]). Within the pre-registered rounds-to-deadline bins the clock still reached 0.716, so the pre-registered hypothesis that the monitors beat the clock is not supported. Within absolute-round bins the clock fell to 0.530, and all five primary monitors beat it by +0.191 to +0.257 (p ≤ 0.0002, uncorrected sensitivity analysis). The five primary monitors warned in 17–28 of the 52 tipped runs, a median 2–5.5 rounds ahead. They raised false alarms in 10–20 of the 48 untipped runs; the clock did so in all 48.

On the nine held-out configurations with mixed outcomes, the trained monitors scored 0.59–0.65, below the clock (0.682 [0.484, 0.891]), and the zero-shot LLM monitors 0.75–0.82 (pairwise 0.820 [0.660, 0.900]). Three of the nine are forks, whose arms differ by an intervention, so these values are secondary.

**Table 3.** Pre-specified held-out comparison on identical rows: the four held-out splits pooled, fork prefixes counted once (36 configurations, 100 runs, 2,338 rows, 156 positive; prevalence 0.067). All trained models were fit on night_train only and frozen (GNN: all 40 ensemble states); the zero-shot monitors were not trained. Confirmatory, not blind. 95% CIs from a paired cluster bootstrap over configurations (10,000 draws). The Holm family (11 tests) contains the time-matched AUROC of each primary monitor minus the clock; the pooled AUROC of GNN, hybrid, pairwise and global_full minus counted features; and pairwise minus GNN and minus hybrid. Time-matched: within rounds-to-deadline bins (pre-registered). Mixed configurations: within configuration × rounds-to-deadline bin (9 configurations, 45 positives). Alarms: score above a threshold set on training data for 5% false positives per row (GNN and hybrid: cross-validation proxy, so realised rates differ). Lead time counts tipped runs warned before the tip, and any alarm in an untipped run is a false alarm. Before the shortcut was first announced (1,786 rows, 42 positives), AUROC ranged from 0.725 (clock) to 0.779 (hybrid); the oracle reached 0.812. MAE of the GNN's count head: 0.94. † Secondary, outside the Holm family.

| Monitor | AUROC [95% CI] | Time-matched AUROC [95% CI] | Within mixed configurations [95% CI] | AUPRC | Tipped runs warned (median lead); untipped runs with false alarm |
|---|---|---|---|---|---|
| Clock | 0.781 [0.714, 0.841] | 0.716 [0.632, 0.789] | 0.682 [0.484, 0.891] | 0.176 | 36/52 (3); 48/48 |
| Counted features | 0.812 [0.759, 0.861] | 0.797 [0.723, 0.854] | 0.647 [0.442, 0.789] | 0.260 | 28/52 (4.5); 20/48 |
| Tabular model with memory † | 0.811 [0.756, 0.860] | 0.804 [0.725, 0.864] | 0.642 [0.380, 0.811] | 0.252 | 27/52 (5); 14/48 |
| Edge monitor † | 0.800 [0.753, 0.841] | 0.792 [0.696, 0.853] | 0.591 [0.337, 0.811] | 0.211 | 29/52 (4); 14/48 |
| GNN (frozen) | 0.817 [0.756, 0.873] | 0.769 [0.676, 0.846] | 0.639 [0.430, 0.792] | 0.309 | 28/52 (5); 14/48 |
| GNN + tabular hybrid | 0.832 [0.782, 0.881] | 0.818 [0.748, 0.870] | 0.647 [0.429, 0.815] | 0.301 | 28/52 (5.5); 15/48 |
| Zero-shot LLM monitor, full transcript (global_full) | 0.816 [0.759, 0.869] | 0.819 [0.727, 0.883] | 0.747 [0.356, 0.916] | 0.245 | 17/52 (3); 11/48 |
| Zero-shot LLM monitor, single conversations (pairwise) | 0.855 [0.808, 0.899] | 0.838 [0.755, 0.900] | 0.820 [0.660, 0.900] | 0.273 | 25/52 (2); 10/48 |
| Oracle (true violation count + clock; not observable) | 0.908 [0.872, 0.945] | 0.872 [0.817, 0.921] | 0.876 [0.708, 0.972] | 0.590 | 48/52 (5); 14/48 |

### 4.3 Where the signal comes from

The ablations are exploratory cross-validation runs on night_train (5 folds, one training seed; reference AUROC 0.871; 95% training-seed noise band ±0.071 for a difference). Rewiring each snapshot's edges to random endpoints (degrees not preserved) changed AUROC by −0.004 [−0.032, +0.023]. Structure only (S0, Table 1) reached 0.804; adding the escalation lexicon (S1, no LLM features) gave 0.790, and adding the factual ratings (S2) 0.814. In AUROC only S1 (−0.081) falls outside the noise band. Within 5-round bins of absolute time, each tier lost 0.10–0.13, outside the band (±0.068). Removing the temporal block lowered AUROC from 0.879 to 0.793 (−0.086 [−0.148, −0.024], measured against the screen's own base). It was the only one of 22 screen variants beyond training-seed noise. The GNN is better described as a temporal monitor over jury-rated messages than as a detector of network contagion.

### 4.4 Transfer and validation suite

Table 4 splits the held-out rows by condition (secondary, uncorrected). On the new library all monitors stayed above the clock (0.78–0.87 against 0.66). With tool-output injection, whose trigger never appears in the messages, the clock (0.816) scored above every trained monitor (0.744–0.785). Within absolute-round bins the trained monitors were near chance there (0.54–0.56), and the zero-shot LLM monitors reached 0.64–0.70.

The validation suite gave no evidence of a large degradation, but its resolution is coarse. In none of the 96 comparisons did the interval of arm minus rep1 lie entirely below zero. Post hoc, the suite would have detected with 80% probability only drops of about 0.2 AUROC, not the 0.1 the plan assumed. Because rep1 was the harder replicate for 9 of 12 predictors (11 of the 96 intervals lie entirely above zero), this noise floor may be too generous. By the pre-registered rules, H1–H4 were not supported and H5 was supported, but no interval excludes its decision boundary. H5 and the GNN half of H2 reverse under time-matched AUROC. In H1 (29 run pairs from 6 configurations, partly blind), the GNN reached 0.76 [0.45, 0.97] and the oracle 0.55.

Descriptively, global_full had the highest AUROC among the observable monitors in every arm and in both replicates (0.85–0.95). In a pooled comparison chosen after seeing the results, it led the GNN by +0.082 [+0.049, +0.118], although the two had tied on the held-out rows (0.816 and 0.817). In the replication (H7), [[H7: n of 28 runs and c of 14 configurations evaluated; tipped runs; executions]]. D was [[H7: D = X [L, U]]], so H7 is [[H7: supported / not supported / open]] (secondary: [[H7: time-matched D, global_full − hybrid, pairwise − GNN]]; descriptive: [[H7: 12 predictors]]).

**Table 4.** Transfer and validation suite (AUROC; secondary, uncorrected). Left four columns: the held-out splits of Table 3 (number of configurations in parentheses; per-split CIs about ±0.1). Right two columns: the validation suite (night_vx) on its 14 new configurations, showing the two unchanged replicates and the range over the four shifted arms (hub network: 7 configurations). Each night_vx cell rests on 15–39 positive rows (hub network: 9–15). There the GNN is a stored file with 15 of its 40 states (held-out AUROC 0.813 instead of 0.817), and the tabular models were refit. The right columns are therefore comparable neither with the left ones nor with Table 3.

| Monitor | In-distribution (12) | New library (8) | Tool-output injection (8) | Forks (8) | night_vx rep0 / rep1 | night_vx shifted arms (range) |
|---|---|---|---|---|---|---|
| Clock | 0.847 | 0.659 | 0.816 | 0.776 | 0.82 / 0.63 | 0.71–0.87 |
| Counted features | 0.902 | 0.786 | 0.759 | 0.737 | 0.78 / 0.76 | 0.71–0.79 |
| GNN (frozen) | 0.921 | 0.794 | 0.744 | 0.731 | 0.79 / 0.74 | 0.73–0.89 |
| GNN + tabular hybrid | 0.922 | 0.823 | 0.785 | 0.728 | 0.81 / 0.79 | 0.75–0.87 |
| Zero-shot LLM monitor, full transcript (global_full) | 0.875 | 0.782 | 0.825 | 0.734 | 0.91 / 0.85 | 0.87–0.95 |
| Zero-shot LLM monitor, single conversations (pairwise) | 0.872 | 0.867 | 0.842 | 0.797 | 0.90 / 0.83 | 0.78–0.88 |

The arm with agents fine-tuned for persistence was dropped after its canary run, in which 44% of their replies were invalid JSON. In a pre-registered, descriptive side study without a swarm (no decision rule; blind Claude Haiku 5.5 judge; all replies re-judged with a 1,500-token budget after the first pass returned empty labels), the fine-tuned model held its position under peer pressure in 48 of 60 replies, against 36 of 60 for its base (sign test over 12 probes, p = 0.73).

## 5. Discussion and Limitations

**What this means for operators.** Monitors that read only messages warned a median 2–5.5 rounds before the tip. None of them separated from a clock that knows the deadline, and we did not test interventions. Graph structure added nothing we could detect, a known risk for graph-level prediction (GRADE, 2026). The replication ([[H7: D = X [L, U]; supported / not supported / open]]) speaks only to new replicates of the 14 configurations.

**The hard part is telling which run of a configuration tips.** Within configurations every monitor weakened. A plain re-run changed the outcome in only 1 of 14 configurations, yet cost the clock 0.20 AUROC [0.09, 0.29]. Shift tests therefore need noise floors from several replicates, run interleaved with the shifted arms.

**Limitations.**
- Simulation only: one domain, 24 agents, two shortcut types, four models with reasoning off; the tipping rate is set by our calibration.
- Few positives (45 tipped training runs); the held-out splits are not blind, and the GNN was selected on the cross-validation rows.
- Unequal inputs: the LLM monitors read task words, global_full sees elapsed time, and Haiku is both monitor and judge.
- Monitors that read only messages miss silent violations, the merge feed and triggers in tool output; judge agreement was not measured.
- The peer-message association is observational and cannot separate simple from complex contagion (Centola & Macy, 2007).
- Validation: 14 configurations, anti-conservative intervals and one replicate pair as noise floor. The stored 15-state GNN failed its row-by-row check and was replaced by a 120-row check, and the H4 thresholds come from cross-validation proxies.
- Not done: isolation control, run-size baseline, GNN without message passing, degree-preserving rewiring, held-out feature-tier and structure ablations, a systematic horizon curve (only Δ = 2, 3 and 5 exist, exploratory).

## 6. Conclusion

Monitors that read only messages predicted tipping three rounds ahead (AUROC 0.800–0.855, against 0.781 for the clock). No pre-specified comparison survived Holm correction, though within absolute-round bins all five primary monitors beat the clock (p ≤ 0.0002, sensitivity analysis). Graph structure added nothing we could detect. H7: [[H7: D = X [L, U]; supported / not supported / open]]. The hard parts are building the data and telling a risky run from a risky setup.

## Code and Data

**Code:** https://github.com/mauricioneubecker-star/apart_hackathon_agentswarm_monitor. Branch `night-vx-validation` holds the simulator, labels, jury, features, zero-shot LLM monitors and analyses. Branch `gnn-opt-torch` holds the frozen GNN, and `gnn-opt` the evaluation harness and tabular baselines.

**Data:** [[TODO: data link]].

**Pre-registration:** `ANALYSIS_PLAN.md` (in German) was committed as `4e6e9986` (8 November, 19:25 CET) and has since changed only through dated addenda. The held-out comparison ran shortly before that commit; per addendum 1, its results were read only afterwards. The validation inputs were frozen (`d083547d`) before the evaluation (`bb3f665d`). The unchanged evaluation script was executed twice on these inputs, locally and in a separate cloud session, and all result files are byte-identical. Addendum 3 for H7 (`e319c9e7`, 9 November, 07:44 CET) existed before any of its runs.

**Review artifacts:** `analysis/review/` and `paper/STORYLINE_CHECK.md`.

**Info-hazard note:** all exploits are file or merge manipulations inside a mock repository. Attack texts are plain and not optimised. We do not publish optimised injection prompts.

## Author contributions

[[team: who did what]]

## LLM Usage Statement

We used Claude through Claude Code (mainly Claude Opus 5.5) to search and summarise literature, discuss design choices, write large parts of the code, run simulations and analyses, and draft sections of this report, including this one. Separate Claude agents recomputed the main analyses with their own code (`analysis/review/`). Some received only code and data; others were asked to test specific claims (`paper/STORYLINE_CHECK.md`). [[team: state what each member verified by hand (design decisions, code, every number, every reference); keep only what is true]]

## References

[Verify all entries before submission.]

1. Anagnostopoulos, Kumar & Mahdian (2008). KDD.
2. Ashery, Aiello & Baronchelli (2025). Science Advances. arXiv:2410.08948.
3. Bandura (1999).
4. BlindGuard (2025). [verify]
5. Centola & Macy (2007).
6. Cialdini (2001).
7. Fan et al. (2026). SCCAL. arXiv:2603.13325.
8. GRADE (2026). arXiv:2606.22741.
9. GUARDIAN (2025). arXiv:2505.19234.
10. He et al. (2026). A-Trust. arXiv:2506.02546.
11. Holm, S. (1979). A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics, 6(2), 65–70. [verify]
12. Hu et al. (2020). ICLR.
13. ImpossibleBench (2025). arXiv:2510.20270.
14. Janis (1972).
15. Kutasov et al. (2025). SHADE-Arena. arXiv:2506.15740.
16. Paglieri et al. (2026). arXiv:2609.04170.
17. SentinelAgent (2025). arXiv:2505.24201.
18. Sykes & Matza (1957).
19. Wang et al. (2025). G-Safeguard. arXiv:2502.11127.
20. XG-Guard (2025). [verify]
21. Yu et al. (2024). NetSafe. arXiv:2410.15686.
22. Yu et al. (2026). FGLGuard. arXiv:2609.02967.
23. Zeng et al. (2024). arXiv:2401.06373.
24. Zhang (2026). The Troy Moment. arXiv:2609.15494.
