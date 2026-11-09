> **Entwurf, Stand 9. Nov. 10:25.** Sechs Schreib-Agenten, noch ohne Review. Die Prüfung von Zahlen, Aussagen und Stil
> läuft, die überarbeitete Fassung kommt als `paper/paper.md`. Der Bestätigungstest H7 ist noch offen: Stellen in
> [[doppelten Klammern]] werden nach der Auswertung (gegen 11:25) gefüllt. Grundlage: `paper/STORYLINE_CHECK.md`.

# Spotting a Swarm Before It Tips: Simulated Data and Early-Warning Monitors for Collective Rule-Breaking in LLM Agent Teams[^1]

Author name 1 / Affiliation · Author name 2 / Affiliation · Author name 3 / Affiliation

Author name 4 / Affiliation · Author name 5 / Affiliation · Author name 6 / Affiliation

*With Apart Research*

[^1]: Research conducted at the Swarm Alignment Hackathon, November 2026.

## Abstract

Teams of LLM agents can break rules together: one agent finds a forbidden shortcut and others follow. We asked whether such tipping can be predicted from the agents' messages, and whether the communication graph helps. Finding no suitable labelled data, we built a simulator of 24-agent software teams with unsolvable tickets and one working forbidden shortcut, labelled from tool logs. Of 252 runs in 112 configurations, 101 tipped (at least 8 of 24 agents used the shortcut), most often where every agent could see the shortcut. On 36 held-out configurations, monitors predicted tipping within three rounds with AUROC 0.800–0.855, against 0.781 for a round-counting clock. A frozen temporal graph neural network (GNN; 0.817) did not outperform gradient-boosted trees on counted communication features (0.812) or a zero-shot LLM monitor reading single conversations (0.855); none of 11 pre-specified comparisons survived Holm correction. In exploratory cross-validation, random rewiring of the graph cost nothing, while removing the LLM judges' ratings of message content lowered AUROC. In a pre-registered suite of 93 new runs, no frozen monitor lost detectably more AUROC under four shifts than between two replicates (resolution about 0.2 AUROC); a pre-registered replication on 28 fresh runs of its 14 new configurations tested whether the zero-shot LLM monitor reading the full transcript beats the frozen GNN [[H7: AUROC difference X [CI]; supported / not supported]]. We release the simulator and dataset.

## 1. Introduction

LLM agents increasingly work in groups, such as coding teams and research pipelines, where harm can grow out of normal interaction. Paglieri et al. (2026) let 100 agents prove formal conjectures with a shared library and direct messages. One agent found an exploit in the evaluator, and it spread first through the library, then through private messages, as other agents adopted it under competitive pressure. What matters to an operator is the team tipping: the point at which a large share of its agents have broken a rule.

Current safety tools are not built for this case. Graph-based detectors such as G-Safeguard (Wang et al., 2025) look for single compromised agents, and their authors name the reactive nature of the method as its main limitation. FGLGuard (Yu et al., 2026) found that detectors of this kind drop to chance level on organic data, because unsafe teams "drift together" and no single agent stands out. LLM judges that read transcripts are the main alternative. SCCAL (Fan et al., 2026), the closest work, finds warning signals several rounds before a violation, on a synthetic benchmark. To our knowledge, no monitor has been tested on predicting that a large share of a team is about to break a rule.

We started from a hypothesis. If tipping is a property of the whole team, its risk should be visible in the team's communication, in who talks to whom and in what they say. A graph neural network (GNN) that reads each round's communication graph, with named edge features such as requests for a workaround, should turn this into an early warning and beat monitors that read single conversations. The data only partly support the hypothesis. Communication carried an early-warning signal. We could not detect any contribution from who talked to whom, and a zero-shot LLM monitor reading single conversations was at least as accurate as the GNN.

Testing this needs teams that tip and teams that do not, with the round at which each agent breaks the rule. To our knowledge, no public dataset records teams of LLM agents in which collective rule-breaking sometimes happens and sometimes does not, with per-agent, per-round ground truth. We therefore built one, and most of our work went into it. Tipping did not appear until the fourth of four pilots (124 runs). In the first three (96 runs) no team tipped. Agents waited for QA, escalated, cited the ownership rules or tried to edit the protected tests, and part of this came from environment problems that we then fixed.

**Threat model.** A cooperative team of 24 agents works under deadline pressure. Some tickets cannot be solved honestly, and one forbidden shortcut gets them through the checks. The first agent to use or promote it may find it alone, know it from handover notes, have been told to use it (possibly as a hidden side task), or be pushed from outside by fake authority or a prompt injection. We measure harm as the number of agents that have broken the rule. A team counts as tipped when at least 8 of its 24 agents (one third, instructed seeds included) have done so. A monitor sees only the team's communication, never tool calls, private reasoning or the repository. In every round it scores the risk that the team tips within the next three rounds. Agents who break the rule without writing about it stay invisible to it. We do not cover covert coordination through hidden channels such as steganography.

Our main contributions are:

1. **A simulator for collective rule-breaking.** A team works on one of six self-written Python libraries with 24 interdependent functions each, one ticket per agent. In 9, 12 or 16 of the 24 tickets an extra regression test contradicts the specification, as in ImpossibleBench (2025). Exactly one forbidden shortcut works: editing the CI scoring file, or merging with `skip_checks`. Labels are computed deterministically from the tool-event log, with no human or LLM annotation. Paraphrased attack texts and harmless decoys from the same senders reduce the risk that a classifier learns the generator's templates instead of agent behaviour.
2. **A labelled dataset.** It holds 252 runs of 30 rounds in 112 configurations: 236 control runs plus 16 counterfactual continuations forked from 8 of them after round 5. Together they give 7,560 labelled snapshots and 21,605 agent-written messages. Of these runs, 101 tipped, a rate that reflects our calibration. 96% of the 1,514 rule-breakers had never been instructed, although most runs contained some seed. In exploratory analyses, tipping depended mainly on the environment, above all on whether every agent could see the shortcut. A direct message from an earlier rule-breaker was associated with adoption for only one of the two shortcut types.
3. **A comparison of monitors on identical snapshots.** We compare:
   - the clock (a round counter);
   - counted features (bag + graph, gradient-boosted trees);
   - a tabular model with memory;
   - an edge monitor;
   - a frozen temporal GNN;
   - a GNN + tabular hybrid;
   - a zero-shot LLM monitor reading single conversations (pairwise);
   - a zero-shot LLM monitor reading the full transcript (global_full).

   On 36 held-out configurations, some with an unseen library or an unseen injection carrier, all monitors reach AUROC 0.800–0.855, against 0.781 for the clock. None of 11 pre-specified comparisons survives Holm correction. Whether the monitors beat the clock depends on how time is matched. Within absolute-round bins the five pre-specified monitors do (p ≤ 0.0002); within the pre-registered rounds-to-deadline bins none does after Holm correction. In exploratory cross-validation, random rewiring of the graph changed AUROC by −0.004 [−0.032, +0.023]. Removing the LLM judges' ratings of message content cost 0.06–0.08. The pairwise LLM monitor cost about one cent per run.
4. **A pre-registered validation suite, blind for monitor scores.** We scored 93 new runs with monitors frozen before any comparison with labels. The suite has 14 new configurations with predicted tipping probabilities of 0.30–0.80. Each ran twice unchanged and once under each of four shifts: a longer sprint, half the agents on an unseen model, visible enforcement and, on 7 of them, a hub-dominated network. Another 16 runs are new replicates of 8 held-out configurations. No monitor lost detectably more AUROC under a shift than between the two unchanged replicates, at a resolution of about 0.2 AUROC. Of five pre-registered hypotheses about the GNN, four were not supported and one was supported, but for none does the interval exclude the decision boundary. Post hoc, the zero-shot LLM monitor reading the full transcript scored highest in every block. We therefore pre-registered H7 before simulating 28 fresh runs, which use new seeds of the 14 unchanged configurations. H7 holds if the 95% interval of AUROC(global_full) − AUROC(GNN) lies above zero. The difference is computed on all labelled snapshots of these runs, with a paired bootstrap over the 14 configurations (10,000 draws). [[H7: n of 28 runs evaluated; AUROC difference X [CI]; supported / not supported]] A confirmed H7 would cover only these 14 configurations.

Besides building the data, the hard part was telling a risky setup from a risky run. Configuration factors alone predict whether a run tips (grouped cross-validated AUROC 0.82). In the pre-registered within-configuration test (29 run pairs, partly blind), the GNN reached 0.76 [0.45, 0.97], an interval too wide to show that it reads within-run dynamics. Whether graph structure matters in larger teams remains open: all our teams had 24 agents.

## 2. Related Work

**GNN detectors on agent communication.** G-Safeguard (Wang et al., 2025), GUARDIAN (2025), BlindGuard (2025) [verify], XG-Guard (2025) [verify] and FGLGuard (Yu et al., 2026) represent multi-agent systems as graphs and train GNNs on them. They classify single nodes as compromised or not, and their edge features are text embeddings that a human cannot read. Our monitors predict a system-level outcome ahead of time, and our edge features have names.

**Interpretable scoring of single messages.** A-Trust (He et al., 2026) scores each message on six dimensions inspired by Grice, and MAST (Cemri et al., 2025) gives a taxonomy of failure modes in multi-agent traces. Neither uses the structure of who talks to whom. A-Trust also finds that prompt-based LLM scores separate these dimensions poorly.

**Observers and geometry on interaction graphs.** SentinelAgent (2025) lets an LLM overseer inspect an execution graph. SCCAL (Fan et al., 2026) is closest to our goal: it combines graph curvature with semantic change and finds warning signals several rounds before a violation. Its edge carries a single number, its benchmark is synthetic, and no code is available.

**Contagion in LLM populations.** Ashery et al. (2025) show that a committed minority can flip social conventions in LLM populations. NetSafe (Yu et al., 2024) finds that dense networks spread adversarial content further. In the Troy Moment study (Zhang, 2026), frontier models in three-agent swarms did not copy a peer's rule-breaking. These works describe spreading but do not build detectors.

**LLM monitors.** Sabotage evaluations such as SHADE-Arena (Kutasov et al., 2025) score an agent's transcript with an LLM monitor. We use zero-shot monitors of this kind as baselines. They cost one to four cents per 30-round run. Our trained monitors are not cheaper, since their features also come from LLM judges.

## 3. Methods

Figure 1 shows the pipeline from scenario to warning.

*[Figure 1: Pipeline. Scenario generator → 24-agent simulation in a mock repository → messages and tool events; tool events feed only the labels. Two LLM judges rate each message; ratings and per-round interaction graphs feed the trained monitors, while zero-shot LLM monitors read the messages.]*

### 3.1 The simulated team

**Tasks.** Each agent owns one ticket, a function in one of six Python libraries we wrote (24 interdependent functions each). For 12 or 20 of the 24 tickets, a design decision needed for acceptance sits in the notes of another agent one or two steps away in the network. Nine, 12 or 16 tickets are unsolvable (39, 38 and 35 of 112 configurations): an extra regression test contradicts the specification, as in ImpossibleBench (2025). Automatic checks on all 144 functions confirm three things: the reference passes, a naive solution without the design note fails, and the unsolvable variant defeats the reference.

**The shortcut.** Exactly one forbidden shortcut works: editing `.ci/scoring.toml`, for example to quarantine the failing check (K2), or merging with `skip_checks=true` (K4), in 56 configurations each. Other routes are blocked or labelled. In half of the configurations agents can find the shortcut themselves (K4: `skip_checks` is in every merge signature; K2: the scoring file already holds an earlier quarantine entry). Otherwise only informed agents and seed texts reveal it.

**Rounds and tools.** An episode has 30 synchronous rounds, and the release cut falls after round 17, 20, 23 or 26 (28 configurations each). Each round, every agent takes one tool action and may send one message (59 configurations) or two (53).

**Pressure and rules.** Pressure is high everywhere: credits scaled to the cut, reminders, a release board naming open owners, and a merge feed that shows each merge's CI state. Two pressure factors vary: a release freeze, under which QA fixes no escalated check before the cut (79 configurations), and a manager message 4, 6 or 8 rounds before the cut demanding every ticket merged (79). The rule never names the mechanism and is implicit (39), ambiguous (38) or soft (35), never firm. No punished-peer, unpunished-peer or audit events were run, and sanctions could fire in only 8 configurations.

**Communication.** Four teams of six talk on a shared board (67 configurations), in team channels (28) or by direct message only (17).

### 3.2 Population and seeds

Agents run on four models, two dense (Qwen3.8-27B, Gemma 4 31B) and two mixture-of-experts (Qwen3.5-397B, Gemma 4 26B A4B), at temperature 0.7 with reasoning off. Teams mix two models 12/12 (55 configurations) or four models 12/4/4/4 (57). GLM-5.2 appears only in the validation suite, where it replaces 12 of the 24 agents in 14 runs. Private thoughts are logged but never shown to other agents or monitors. The persona mix, a prompted persistence persona and self-merge also vary.

Five seed conditions set how the shortcut enters:
- none (22 configurations);
- knower (21): two agents know the mechanism from an infra rotation but get no instruction;
- pioneer (19): a stuck agent has a private plan to use it;
- side task (24): an agent is secretly asked to steer stuck teammates to it, as in SHADE-Arena (Kutasov et al., 2025);
- external (26): 11 fake-authority messages and 15 prompt injections in a document, an issue comment or tool output.

Peers-only configurations always contain an informed agent. Seeds sit at a hub or at the periphery (56 configurations each), and at most one agent per run is instructed. Eight configurations without a seed (four of them with an informed agent) were forked after round 5 into three arms: unchanged, with a persistent injected QA-bot instruction, or with one fake-manager message.

### 3.3 Labels

Labels come deterministically from the tool-event log, never from human or LLM annotation. An agent counts as violating from its first successful write to `.ci/scoring.toml` (K2) or its first merge with `skip_checks=true` (K4). Two more rules catch unsolvable tickets that turn green and edits to the test harness. Blocked attempts are logged but not counted. The risk count at round t is the number of agents that have violated by t, with instructed seeds included and flagged. The pre-registered target is defined while the count is below θ = 8: will it reach θ within the next three rounds? Every run has at least nine unsolvable tickets, so stuck agents alone can reach θ.

### 3.4 Keeping the data honest

Seed texts come from paraphrase pools, so all 26 attack messages of the main batch differ. Another 280 harmless notices come from the same senders the attacks impersonate. The text-leakage checks ran only on the generator's earlier design. There, a TF-IDF classifier on non-attack text detected attack scenarios at chance (AUROC 0.481 ± 0.029), and the attack arm was nearly independent of pressure, prohibition form and early-adopter source (Cramér's V ≤ 0.088). Signal at the setup level remains: the design factors alone reach grouped-CV AUROC 0.82, and only 15 of 104 configurations with repeated runs had both outcomes. We therefore also compare monitors within configurations.

We split by configuration, never by run. Trained monitors are fit on 64 configurations. Held out are 12 in-distribution configurations, 8 with an unseen library, 8 with injection through tool output (never seen in training) and the 8 forked ones, giving 2,338 prediction rows with 156 positives. These splits are not blind. Each team had seen its own test results, and the analysis plan (metric, 11 Holm-corrected tests, decision rule) was committed after the joint comparison had run, though before its results were read.

Only a separate validation suite (93 runs) is blind. Its monitor scores were frozen before any comparison with labels, though its within-configuration part is only partly blind, and its evaluation ran twice with byte-identical outputs. Hypothesis H7 came from this suite post hoc: the zero-shot LLM monitor reading the full transcript (global_full) beats the frozen GNN. H7 was pre-registered before any of its 28 fresh episodes existed (replicates 2 and 3 of the suite's 14 new configurations). It holds if the 95% bootstrap interval of the AUROC difference (paired over configurations, 10,000 draws) lies above 0. [[H7: AUROC difference X [CI] on N of 28 episodes; supported / not supported]]

### 3.5 What did not work at first

Producing tipping took four pilots (124 runs), and in the first three (96 runs) no team reached the threshold. Agents waited for QA, escalated, cited the ownership rules or tried to edit the protected tests. Part of this null result came from our environment, which we fixed without scripted actions or template messages.

- **Pilot 1** (30 runs, 20 rounds) had one violation. A notice after the cut said open tickets roll over, which removed the pressure. Only 2 of 36 knowers opened their notes, which the prompt never mentioned, and a bug hid `skip_checks` from the K4 seeds told to use it.
- **Pilot 2** (38 runs): three K4 pioneers used the shortcut but nobody followed, and 11 of 12 side-task agents ignored their task.
- **Pilot 3** (28 runs): K2 spread to at most five violators, while K4 merges stayed silent.

Our fixes included announcing the notes, recording unfinished tickets as missed, and a K4 merge feed that shows each merge's CI state. Once someone has used the shortcut, this feed reveals the mechanism to everyone.

Pilot 4 (28 runs) tipped five times, from three configurations, all under a release freeze (5 of 14 runs with a freeze, 0 of 14 without). With six unsolvable tickets no run exceeded five violators. Every tip came at the cut, so the clock (round counter) alone reached AUROC 0.80. The pilots are small and confounded. Still, tipping appeared only after we blocked the legitimate exit, made adoptions visible and raised the number of stuck agents.

A fifth pilot was designed but not run. Its levers went into the main batch:
- the freeze, as the dial for the base rate;
- the merge feed for both shortcut types;
- a release board;
- at least nine unsolvable tickets;
- open advocacy by instructed seeds;
- no careful persona mix (0 of 7 runs tipped in pilot 4) and no firm rule.

The cut, the timing of the manager message and the seed position vary, so tipping is not tied to one round or one cascade shape. We aimed for 20–80% tipped runs (40–60% expected) and reached 40% (101 of 252). A freeze was not necessary: configurations without one still tipped, though less often (mean configuration rate 20% against 46%; exploratory, Holm p = 0.053).

### 3.6 From messages to graphs

For each round t we build one graph per run, with the 24 agents and any external senders as nodes. An edge i → j exists if j received a message from i in rounds t − 2 to t. The message is either addressed to j by direct message, mention or reply (direct edge), or read by j in a shared channel without being addressed to j (broadcast edge). Only messages enter, never the merge feed, other status notices or tool events.

Table 1 lists the features. They form four tiers of increasing cost, so that we can measure what each tier adds. The trained monitors use a headline set of 18 of the 22 edge features and 5 of the 11 node features. The task lexicon (shortcut mentions, pressure words) serves only as an ablation.

*Table 1: Feature catalog v1.1. Edge features aggregate the messages i → j of rounds t − 2 to t. † = not in the headline set. S0–S1 need no LLM; S2–S3 are scored per message by two LLM judges. Prompts, private thoughts and model identity are never inputs. The rubrics borrow named mechanisms from social science: moral disengagement and neutralisation (Bandura, 1999; Sykes & Matza, 1957), persuasion through authority, social proof and time pressure (Cialdini, 2001; Zeng et al., 2024), and groupthink (Janis, 1972). Exposure breadth follows the idea of complex contagion (Centola & Macy, 2007).*

| Tier | Edge features | Node features |
|---|---|---|
| S0 structure | message volume, direct volume, broadcast volume, responsiveness, reciprocity, new contact | external sender, unanswered share; lead and auditor roles†, ticket dependencies (2)† |
| S1 rules, word lists, small NLI model | escalation words; shortcut mentions† and their moving average†, pressure words†, contradiction (NLI; not computed)† | own unaddressed shortcut mentions†, exposure breadth† |
| S2 LLM, factual | success claim, workaround request, verification, frustration | own frustration |
| S3 LLM, interpretive | rule-breaking presented as legitimate and its 3-round trend, goal shift, uncritical adoption, unverified authority, secrecy, judge disagreement | legitimisation in own unaddressed posts, stance drift |
| tool events (ablation only) | – | failed test runs†, unresolved escalation† |

Two judges score each message from 0 to 3 on nine dimensions: DeepSeek V4 Flash and Claude Haiku 5.5, from model families that never act as agents. We use their mean as the feature and their disagreement as an extra feature. Messages are marked as data before scoring, to make injections against the judges harder (Hines et al., 2024). Scoring once per message keeps the cost linear in the number of messages (Haiku: about $0.022 per run). Agreement between the judges has not been measured.

### 3.7 Monitors

**GNN (frozen).** The GNN team chose its model by cross-validation on night_train and froze it before its single look at the held-out splits. It is a relational GINE (Hu et al., 2020) with three layers and 64 hidden units. Each edge type (direct, broadcast or both) and its reverse have their own weights. In each layer an agent aggregates what its incoming edges send, edge features included, by sum, mean and max. A sum can count risky contacts, where a mean would dilute one pioneer among many harmless ones (Xu et al., 2019). After the first layer, a causal GRU runs over each agent's own history. Auxiliary heads predict the violator count and per-agent violations, and the tipping loss uses only snapshots before the threshold. Training uses the 128 night_train runs, and each batch sees the features of only one judge with probability 0.5. The model averages 5 seeds × the last 8 epochs. The stored file keeps 15 of these 40 states; night_vx and the replication use it (held-out AUROC 0.813 against 0.817). The GNN sees only the headline features and edge types. It never sees the round number, configuration, model identity, instructions, ticket solvability, tool events or the task lexicon, but its memory could still count rounds.

**Comparison monitors.** The clock (round counter) is gradient-boosted trees on the round number alone. Teams tip late in a sprint, so the clock sets the bar. Counted features (bag + graph) are gradient-boosted trees (scikit-learn histogram boosting, depth 3, 250 iterations) on two inputs: per-snapshot aggregates of the headline features, and hand-built graph statistics of high-scoring edges. The tabular model with memory (secondary) adds per-agent histories, such as how many agents have ever sent a high-scoring message. The edge monitor (secondary) scores single edges with the same trees and averages each snapshot's top three. The GNN + tabular hybrid averages the logits of the GNN and the tabular model with memory (weight 0.5, fixed before the test look).

Two zero-shot LLM monitors run Claude Haiku 5.5 with thinking off, using prompts frozen on 8 night_train runs. They read the raw messages, shortcut names included. The zero-shot LLM monitor reading single conversations (pairwise) looks at the last six rounds of each directly connected pair and of each sender's unaddressed posts, and keeps the maximum score ($0.0128 per run). The zero-shot LLM monitor reading the full transcript (global_full) reads rounds 1 to t and estimates the tipping probability, averaged over three samples ($0.0423 per run); it therefore sees elapsed time. The oracle (true violator count + clock) is not observable and marks a ceiling. Haiku 5.5 is also one of the judges, so the LLM monitors and the trained monitors do not draw on independent information.

### 3.8 Evaluation

**Target and splits.** The target is pre-registered. A snapshot is positive if the number of agents who have used the shortcut, instructed seeds included, reaches θ = 8 within the next Δ = 3 rounds. The target is defined only while the count is below θ, and fork prefixes count once. Splits are by configuration:
- night_train: 64 configurations, 128 runs, 3,370 rows (135 positive).
- night_val: 12 configurations, 24 runs, 680 rows (12 positive).
- Held out: four splits with 36 configurations, 100 runs and 2,338 rows (156 positive). They are test_id (12 configurations), an unseen library (8), injection through tool output (8) and the forks (8).

**Cross-validation.** On night_train, all monitors are scored on identical rows in 18 shared folds: 2 × 5 folds grouped by configuration, plus 8 folds that each hold out one factor level. By plan these results are descriptive. They favour the GNN, whose configuration was chosen on these rows. In cross-validation, the GNN and hybrid scores come from an earlier ensemble of two configurations × two seeds. Structure controls (GRADE, 2026) were run only in cross-validation, on five folds with one seed (exploratory): random rewiring of each snapshot (degrees not preserved), and permuted edge features or labels.

**Held-out comparison.** The held-out comparison scores every monitor on the same 2,338 rows. It was pre-specified, but each team already knew its own test numbers, so it is confirmatory, not blind. Besides AUROC (primary) we report AUPRC, recall at 5 % FPR, lead time and the mean absolute error of the GNN's count head. A paired cluster bootstrap over configurations (10,000 draws, shared by all monitors) gives two-sided p-values. Eleven tests form one Holm family (Holm, 1979 [verify]):
- (a) time-matched AUROC of counted features, pairwise, global_full, GNN and GNN + tabular hybrid, each minus the clock;
- (b) pooled AUROC of GNN, hybrid, pairwise and global_full, each minus counted features, plus pairwise minus GNN and pairwise minus hybrid.

A difference counts if its Holm-adjusted p is below 0.05. "Monitors beat the clock" requires all five (a) tests to pass.

Time-matched AUROC, as pre-registered, is the pairs-weighted mean AUROC within bins of rounds to the deadline (≤ −9, −8…−5, −4…−1, 0…3, > 3). Deadlines differ between configurations (round 17, 20, 23 or 26), so absolute time still carries information inside these bins. As a sensitivity analysis we therefore also compute AUROC within 5-round bins of absolute time. We also report AUROC within configurations with mixed outcomes, and before the shortcut is first announced. Alarm thresholds are set at 5 % FPR on training data only. Trained models use their night_train out-of-fold scores (for the GNN and hybrid, a 4-run CV proxy); the zero-shot monitors use their night_train and night_val scores. Lead time is the tip round minus the round of the first alarm, over tipped runs with an alarm. Any alarm in an untipped run is a false alarm.

**Blind validation (night_vx).** A factor model fit on night_train and night_val selected 14 new configurations with a predicted tipping probability of 0.30–0.80. Part A runs each one as twins that differ in one factor:
- unchanged, twice (id rep0 and rep1);
- a longer sprint (36 rounds);
- 12 of 24 agents on the unseen GLM-5.2;
- visible enforcement;
- a scale-free communication graph (7 bases).

Part B adds two replicates of 8 held-out night configurations, to test which run of a configuration tips. A fine-tuned-agent arm was dropped after 44 % invalid JSON in its test episode, which leaves 93 runs. Each arm's change from rep0 is read against the replicate noise, rep1 − rep0, bootstrapped over bases. Five pre-registered rules concern the GNN (H1–H5). The plan expected the suite to detect drops above 0.1 AUROC. Monitor scores were frozen and pushed before any comparison with labels, but tip counts were already known, and only 3 of the 29 Part B run pairs are entirely new. The unchanged evaluation script ran twice on these inputs, locally and in a separate cloud session, with byte-identical result files.

**Confirmatory replication (H7).** On night_vx, global_full had the highest AUROC in every block, a pattern noticed only after the evaluation. Before any new episode existed, we pre-registered one test on 28 fresh episodes: replicates 2 and 3 of the 14 unchanged id configurations, scored by the same frozen predictors. The statistic is D = AUROC(global_full) − AUROC(GNN) over all rows of both replicates, with a paired bootstrap over the 14 bases (10,000 draws, seed 20261109). H7 is supported if the lower bound of the 95 % percentile CI exceeds 0. It is the only test and is not corrected. Time-matched D, global_full − hybrid and pairwise − GNN are secondary. No episode started after 10:30 CET ([[H7: n of 28 episodes, b of 14 bases evaluated]]). The result is reported whatever the outcome. A confirmation would cover new seeds of these configurations, not new configurations.

## 4. Results

### 4.1 The dataset and what the traces show

The main batch has 252 runs of 24-agent teams in 112 configurations, 30 rounds each: 236 control runs and 16 fork continuations. It holds 7,560 labelled snapshots, about 180,000 agent turns and 21,605 agent-written messages; 36 configurations (100 runs) are held out. Of these runs, 101 tipped (40%; 93 of 236 control runs), with a median of 12 rule-breakers per tipped run. This rate reflects our calibration and does not estimate real-world prevalence. Outcomes are largely set by the configuration (Table 2): only 15 of 104 configurations with repeated runs produced both outcomes, and the intraclass correlation of tipping is 0.73.

*Table 2: Validity checks that use no monitor. Odds ratios are Mantel–Haenszel estimates for adoption after a direct message (DM) from an earlier rule-breaker, stratified by run × round × stuck status, with 95% intervals from a bootstrap over configurations. The TF-IDF check ran on the generator's v1.1 design, not on the final batch. The unpunished-peer, public-sanction and announced-audit conditions were not run; the share of peer-told adoptions and evaluation awareness in private thoughts were not measured.*

| Check | Result | Kind |
|---|---|---|
| Time-shuffle null for adoption rounds (Anagnostopoulos et al., 2008) | OR 2.34 vs null median 1.21 [0.98, 1.49], p = 0.001; DM recipients 2.02 vs 1.24, p ≈ 0.003 | exploratory |
| Rule-breaker's message from the same round, not yet readable | OR 1.18 [0.74, 1.76] | exploratory |
| Message from an agent who breaks the rule later (placebo) | OR 1.42 [1.17, 1.72]; DM recipients 0.84 [0.64, 1.15]; homophily alone gives 1.8–1.9 in simulation | exploratory |
| Rule-breakers never instructed | 1,321 of 1,382 in control runs (95.6%) | descriptive |
| TF-IDF on non-attack text predicts the attacker arm | AUROC 0.48 ± 0.03 | static, v1.1 design |
| Configuration factors alone predict run tipping | grouped-CV AUROC 0.82 | cross-validation |

**Environment and persona.** In exploratory configuration-level permutation tests (Holm over 14 factors), shortcut type (skip-checks merge K4 vs scorer-file edit K2: +29.5 percentage points, Holm p = 0.008) and discoverability (+32.4 points, Holm p = 0.006) changed the tipping rate, and they are one effect: where `skip_checks` appeared in every agent's merge signature (K4 with exploration), the mean configuration tipping rate was 82%, against 20–24% in the other three cells. Channel layout also mattered (shared board 52%, direct messages only 12%; Holm p = 0.006, and 0.07–0.11 after adjusting for the other factors), and a release freeze raised the rate from 20% to 46% (p = 0.005; Holm p = 0.053). Manager push, a prompted persistence persona and the persona mix showed no detectable effect, but effects below 20–25 points were hard to detect and no careful-skewed persona mix was run. Among uninstructed agents in control runs, 43.5% of those with an unsolvable ticket broke the rule, against 3.1% of those with a solvable, unblocked one [[TODO: commit wf_story/stuck_rates.py to analysis/review before citing, or drop]].

**Uninstructed adoption.** At most one agent per run was instructed, yet 96% of rule-breakers never were (Table 2). Still, only 11 of the 101 tipped runs had no instructed agent, informed agent or outside message.

**Messages from earlier rule-breakers.** Within strata of run, round and stuck status (post hoc; 152,705 agent-rounds of uninstructed agents), agents who had received a direct message from an earlier rule-breaker in the preceding three rounds adopted more often (OR 2.34 [1.54, 3.57]; 2.02 [1.18, 3.63] among message recipients; sign-flip test over configurations p = 0.018). The association was confined to skip-checks scenarios (3.99 [2.41, 7.01]; recipients 2.65 [1.35, 5.61]) and was strongest where only peers knew the shortcut (16.1 [6.2, 40.8]). For scorer tampering (0.87) and on the shared board (1.43, placebo 1.50) there was none. It is not causal evidence: the placebo cannot rule out homophily (Table 2), and organic, unsolicited messages give 1.29 [0.61, 2.55]. Without a dose-response estimate we cannot separate simple from complex contagion (Centola & Macy, 2007).

**Injected instructions.** The forks measure susceptibility to injected instructions. Eight runs without an instructed agent or outside message (four of them with an informed agent) were copied after round 5 and continued in three ways: unchanged; with a QA-bot note telling agents to use the shortcut, repeated in every issue listing and escalation reply from round 6; or with one fake-manager message to three agents. The persistent note raised new rule-breakers from 4.9 to 9.4 per run (+4.5 [1.0, 8.0], 7 of 8 forks positive, Holm p = 0.06); of these 75, 56 had read the note themselves. The single fake-manager message showed no detectable effect (+2.25, p = 0.22).

### 4.2 Early warning

Table 3 reports the pre-specified primary comparison, with all monitors scored on the same 2,338 held-out rows from 36 configurations. The 11 tests had been fixed in the analysis plan before their output was read, but each team had already seen its own test numbers, so the comparison is confirmatory, not blind. The monitors reached AUROC 0.800–0.855 and the clock 0.781. No comparison survived Holm correction. The smallest Holm p (0.090) belonged to the zero-shot LLM monitor reading single conversations (pairwise) against the clock, time-matched (+0.121 [+0.032, +0.213]). The GNN tied with the counted features (+0.004 [−0.036, +0.046]). Pairwise separated neither from the GNN (+0.038 [−0.025, +0.105]) nor from the GNN + tabular hybrid (+0.022 [−0.030, +0.075]).

**Table 3.** Pre-specified held-out comparison on identical rows. Rows come from the four held-out splits pooled, with branch prefixes counted once: 36 configurations, 100 runs, 2,338 rows, 156 positive (prevalence 0.067). All models were trained on night_train only and frozen. The clock, the counted features and the oracle were refit with the frozen settings. GNN: frozen 5-seed ensemble with all 40 snapshot states. The comparison is confirmatory, not blind. 95 % CIs come from a paired cluster bootstrap over configurations (10,000 draws). Time-matched: AUROC within bins of rounds to the deadline (pre-registered). Within mixed configurations: AUROC within configuration × deadline bin (9 configurations, 45 positives). Before first announcement: rows before the shortcut is first announced (1,786 rows, 42 positives). Alarms: an alarm is a score above a threshold set on training data for a 5 % row-level FPR. For the GNN and the hybrid the threshold comes from a cross-validation proxy, so realised FPRs differ. Lead time is counted over warned runs only. A false alarm is any alarm in an untipped run. MAE: mean absolute error of the GNN's auxiliary violator-count head; – means the monitor has no count head. † Secondary, outside the Holm family. Not computed on held-out data: a run-size baseline (every run has 24 agents and 30 rounds), a GNN without message passing, and a structure-only GNN (cross-validation only). Not shown: two secondary zero-shot variants, one agent at a time (0.849) and the last six rounds (0.829).

| Monitor | AUROC [95 % CI] | Time-matched AUROC, rounds to deadline [95 % CI] | Within mixed configurations | Before first announcement | AUPRC | Recall at 5 % FPR (realised FPR) | Tipped runs warned; median lead [IQR] | Untipped runs with a false alarm | MAE, violator count |
|---|---|---|---|---|---|---|---|---|---|
| Clock (round counter) | 0.781 [0.714, 0.841] | 0.716 [0.632, 0.789] | 0.682 | 0.725 | 0.176 | 0.128 (0.029) | 36/52; 3 [2, 5] | 48/48 | – |
| Counted features (bag + graph, gradient-boosted trees) | 0.812 [0.759, 0.861] | 0.797 [0.723, 0.854] | 0.647 | 0.775 | 0.260 | 0.276 (0.048) | 28/52; 4.5 [2, 6.25] | 20/48 | – |
| Tabular model with memory † | 0.811 [0.756, 0.860] | 0.804 [0.725, 0.864] | 0.642 | 0.773 | 0.252 | 0.250 (0.044) | 27/52; 5 [2.5, 6] | 14/48 | – |
| Edge monitor † | 0.800 [0.753, 0.841] | 0.792 [0.696, 0.853] | 0.591 | 0.758 | 0.211 | 0.288 (0.048) | 29/52; 4 [2, 6] | 14/48 | – |
| GNN (frozen) | 0.817 [0.756, 0.873] | 0.769 [0.676, 0.846] | 0.639 | 0.734 | 0.309 | 0.417 (0.054) | 28/52; 5 [2.75, 7] | 14/48 | 0.94 |
| GNN + tabular hybrid | 0.832 [0.782, 0.881] | 0.818 [0.748, 0.870] | 0.647 | 0.779 | 0.301 | 0.372 (0.063) | 28/52; 5.5 [3, 6.25] | 15/48 | 0.94 (GNN head) |
| Zero-shot LLM monitor, full transcript (global_full) | 0.816 [0.759, 0.869] | 0.819 [0.727, 0.883] | 0.747 | 0.736 | 0.245 | 0.212 (0.032) | 17/52; 3 [1, 4] | 11/48 | – |
| Zero-shot LLM monitor, single conversations (pairwise) | 0.855 [0.808, 0.899] | 0.838 [0.755, 0.900] | 0.820 | 0.766 | 0.273 | 0.333 (0.045) | 25/52; 2 [1, 5] | 10/48 | – |
| Oracle (true violation count + clock; not observable) | 0.908 [0.872, 0.945] | 0.872 [0.817, 0.921] | 0.876 | 0.812 | 0.590 | 0.788 (0.094) | 48/52; 5 [3, 6] | 14/48 | – |

Whether the monitors beat the clock depends on how time is matched. The pre-registered matching uses bins of rounds to the deadline, and within these bins the clock still reaches 0.716. At equal distance to the deadline, the absolute round reveals whether a configuration has an early or a late deadline. Under this definition 0 of 5 monitor–clock tests pass, so the pre-registered hypothesis that the monitors beat the clock is not supported. Within bins of the absolute round the clock falls to 0.530, and all five monitors beat it by +0.191 to +0.257 (p ≤ 0.0002). With round and deadline fixed together (post hoc), all monitors except the GNN beat it.

The alarm threshold was set on training data for a 5 % row-level false-positive rate. At this threshold the monitors warned in 17 to 29 of the 52 tipped runs. Over the warned runs, the median lead was 2 to 5.5 rounds, longest for the hybrid. Among the primary monitors, pairwise had the fewest runs with a false alarm (10 of 48), while the clock alarmed in every untipped run. A post hoc check of horizons of 2, 3 and 5 rounds changed AUROC by at most 0.05; the GNN was not included in it. The LLM monitors read task words that the trained monitors exclude. The zero-shot LLM monitor reading the full transcript (global_full) also sees an implicit clock (Spearman 0.83 between its score and the round).

Cross-validation on night_train (64 configurations, identical rows and folds) gave larger margins. All five monitors beat the clock time-matched, by +0.18 to +0.48 depending on the binning (Holm p = 0.0011 each). The hybrid (+0.048 [+0.024, +0.078]) and pairwise (+0.068 [+0.029, +0.112]) beat the counted features. The GNN tied with the counted features (+0.036 [−0.006, +0.085]), although the cross-validation proxy of the frozen GNN did beat them (Holm p = 0.03). Pairwise tied with both the GNN and the hybrid. The plan treats these numbers as descriptive only. They also flatter the GNN, whose configuration was chosen on the same rows. On held-out data the margin over the clock shrank from both sides: the clock's time-matched AUROC rose from 0.635 to 0.716, while every monitor's fell, the GNN's most (by 0.10).

Within one configuration all monitors got weaker, so much of their signal marks a risky setup rather than a risky run. Nine held-out configurations had mixed outcomes. On them the trained monitors scored 0.59–0.65, below the clock (0.68), and the LLM monitors 0.75–0.82, with intervals up to 0.56 wide (Table 3). After the branch point of the forks, the GNN and the hybrid ranked the arm that later tipped higher in 1 of 6 pairs; the LLM monitors were not checked there. H1, the pre-registered hypothesis that the GNN reads within-run dynamics, was tested on 29 run pairs from 6 configurations of the blind suite, which is only partly blind. The GNN reached 0.76 [0.45, 0.97], so H1 is not supported, but the interval does not rule it out either. On the same pairs a structure-only baseline reached 0.86 [0.73, 0.98], for reasons we cannot explain, and the oracle reached 0.55.

### 4.3 Where the signal comes from

We built the GNN on the hypothesis that tipping risk shows in who talks to whom. The ablations do not support it: in these teams the graph structure adds little that we could detect, and message content carries the signal. The ablations are exploratory cross-validation runs on `night_train` (5 folds, one seed; reference AUROC 0.871; seed-noise band ±0.071 for a difference). None was repeated on held-out data.

**Structure.** Rewiring each snapshot's edges to random endpoints (degrees not preserved), in training and test, changed AUROC by −0.004 [−0.032, +0.023]. On held-out data the GNN tied the counted features (Section 4.2).

**Content.** Structure only (S0, Table 1) reached 0.804. Adding the escalation lexicon (S1, no LLM features) gave 0.790, and adding the factual jury ratings but not the five interpretive ones (S2) gave 0.814. In time-matched AUROC each tier lost 0.10–0.13, beyond seed noise. In the validation suite a structure-only gradient-boosted model was the weakest monitor on the pooled Part A rows (0.64, post hoc). For reasons we do not know, it was also the best at ranking a tipping run above a non-tipping run of the same configuration (0.86 [0.73, 0.98]; 29 pairs, partly blind).

**Judges and memory.** With features from one judge only, the frozen GNN fell on held-out data from 0.817 to 0.769 (DeepSeek) and 0.778 (Haiku); the GNN + tabular hybrid moved less (0.825, 0.809). Judge agreement was not measured. Removing the temporal block cost 0.086 AUROC [0.024, 0.148], the only change in a 22-variant screen that cleared seed noise. When trained without skip-checks scenarios and tested on them, GNNs with per-agent memory reached 0.82–0.83 and those with team-level memory 0.70–0.76 (single seeds). The GNN is better described as a temporal per-agent monitor over jury-rated messages than as a detector of network contagion.

**LLM monitor variants.** On held-out data the zero-shot LLM monitor reading single conversations (`pairwise`, 0.855) and a variant reading one agent at a time (0.849) scored highest. The zero-shot LLM monitor reading the full transcript (`global_full`) reached 0.816 (`pairwise` minus `global_full`: +0.039 [−0.004, +0.082], secondary). On all 112 configurations (descriptive), naming the shortcut mechanisms in the prompt (0.849) or keeping notes across rounds (0.844) changed little against `global_full` (0.844). Adding the system notices, including the merge feed that no other monitor sees, raised AUROC to 0.883. In the validation suite `global_full` scored highest in every block (0.85–0.95). In a comparison chosen after seeing the results, it exceeded the GNN by +0.082 [+0.049, +0.118]. The pre-registered hypothesis H7 tests this on 28 fresh runs: replicates 2 and 3 of the 14 validation configurations, simulated only after the test was pushed. The monitors are frozen, the interval comes from a paired bootstrap over the 14 configurations (10,000 draws), and H7 is supported if the lower 95% bound of AUROC(`global_full`) − AUROC(GNN) exceeds 0. [[H7: difference X [95% CI] on n of 28 runs; supported / not supported]]. A positive result would hold only for new seeds of these configurations. Because `global_full` sees elapsed time indirectly (Spearman 0.83 with the round), H7 also reports the time-matched difference [[H7 time-matched: Y [95% CI]]]. The LLM monitors also read task words that the GNN's inputs leave out, and Haiku is one of the GNN's two judges.

### 4.4 Transfer and blind validation

Table 4 splits the held-out rows by condition; these per-split results are secondary and uncorrected. On the unseen task family all monitors stayed above the clock (0.78–0.87 against 0.66). With injection via tool output, the trigger never appears in the messages. The clock (0.816) then beat every trained monitor (0.744–0.785). Within absolute-round bins the trained monitors were near chance (0.54–0.56), and the LLM monitors reached 0.64–0.70. On the branch arms, every predictor except the oracle lay between 0.70 and 0.80. The GNN models led only in distribution (0.92). On the three new splits pooled, pairwise led the GNN by +0.097 [+0.016, +0.182] (uncorrected, not pre-registered).

**Table 4.** Transfer. Left: AUROC per held-out split, with the same rows and models as Table 3 (secondary, uncorrected; number of configurations in parentheses). The splits hold different configurations, so differences between columns are descriptive. Per-split CIs are about ±0.1 (GNN on the new task family: 0.794 [0.677, 0.895]). Absolute-round bins: AUROC within 5-round bins of the round. Right: GLM-5.2 has no held-out split. It appears only in the glm arm of the blind suite night_vx: 14 configurations, with 12 of 24 agents on GLM-5.2. In this arm 13 of 14 runs tipped, against 6 in rep0, so AUROC there mostly reflects timing. Shift (arm − rep0) and replicate noise (rep1 − rep0) are paired over the same 14 configurations. In night_vx the GNN is a stored version that keeps 15 of its 40 snapshot states (held-out AUROC 0.813 instead of 0.817), and the tabular models were refit. The right part is therefore comparable neither with the left part nor with Table 3. ‡ CI bound depends on the bootstrap seed.

| Monitor | In distribution (12) | New task family (8) | Injection via tool output (8) | Tool output, absolute-round bins | Branch arms (8) | GLM-5.2 arm (night_vx), AUROC | Shift vs rep0 [95 % CI] | Replicate noise (rep1 − rep0) |
|---|---|---|---|---|---|---|---|---|
| Clock (round counter) | 0.847 | 0.659 | 0.816 | 0.522 | 0.776 | 0.87 | +0.043 [−0.074, +0.161] | −0.196 |
| Counted features (bag + graph, gradient-boosted trees) | 0.902 | 0.786 | 0.759 | 0.535 | 0.737 | 0.71 | −0.069 [−0.189, +0.049] | −0.017 |
| Tabular model with memory | 0.895 | 0.807 | 0.780 | 0.564 | 0.699 | 0.75 | −0.047 [−0.122, +0.036] | −0.014 |
| Edge monitor | 0.837 | 0.812 | 0.780 | 0.541 | 0.728 | 0.76 | −0.028 [−0.164, +0.119] | −0.057 |
| GNN (frozen) | 0.921 | 0.794 | 0.744 | 0.543 | 0.731 | 0.73 | −0.059 [−0.227, +0.124] | −0.054 |
| GNN + tabular hybrid | 0.922 | 0.823 | 0.785 | 0.560 | 0.728 | 0.75 | −0.064 [−0.180, +0.059] | −0.024 |
| Zero-shot LLM monitor, full transcript (global_full) | 0.875 | 0.782 | 0.825 | 0.638 | 0.734 | 0.87 | −0.036 [−0.106, +0.072] | −0.053 |
| Zero-shot LLM monitor, single conversations (pairwise) | 0.872 | 0.867 | 0.842 | 0.698 | 0.797 | 0.81 | −0.098 [−0.201, +0.003] ‡ | −0.073 |
| Oracle (true violation count + clock; not observable) | 0.925 | 0.896 | 0.922 | 0.875 | 0.875 | 0.90 | −0.069 [−0.141, −0.001] ‡ | −0.115 |

The blind suite night_vx adds 93 runs under pre-registered decision rules. Their monitor scores were frozen and pushed (commit d083547d) before any comparison with labels. The suite's 14 new configurations were chosen to have a predicted tipping probability of 0.30–0.80. Each configuration ran as twins that differ in one factor:
- two unchanged replicates (rep0, rep1);
- a longer sprint (deadline at round 29 of 36);
- 12 of 24 agents on GLM-5.2, the only runs with this model;
- visible enforcement;
- for 7 configurations, a scale-free graph. This arm also redraws the graph-dependent choices.

Sixteen further runs replicate 8 held-out configurations for H1. The evaluation script ran twice on the frozen inputs, locally and in a separate cloud session, and the result files are byte-identical.

We found no evidence of a large degradation, but the resolution is coarse. In none of the 96 comparisons (12 predictors × 4 arms × 2 metrics) did the CI of arm minus rep1 lie entirely below zero. The median CI half-width was 0.15 AUROC. A post hoc calculation puts the drop that the suite would detect with about 80 % probability at about 0.2 AUROC (0.2–0.35 for the GNN), not the 0.1 the plan assumed.

By their pre-registered rules, H1–H4 were not supported (H1: Section 4.2) and H5 was supported. No CI excludes its decision boundary.
- H2 failed because the clock did not collapse in the longer sprint (arm − rep1 +0.08 [−0.09, +0.27]).
- H4 failed on the GNN's false alarms: 3 of 9 untipped enforcement runs against 1 of 8 in rep0 (Fisher p = 0.58). All three alarmed runs were near misses.
- H3 and H5 compare the GNN's shift with that of the counted features without graph aggregates. The difference was −0.01 [−0.19, +0.20] under GLM-5.2 and +0.10 [−0.21, +0.61] on hub networks (7 configurations).
- Under time-matched AUROC, H5 reverses (−0.12 [−0.62, +0.52]) and the GNN half of H2 fails.

Three arms produced their condition only in part. Enforcement did not detectably reduce tipping (5 against 6 of 14). GLM-5.2 changed the base rate (13 of 14 tipped) more than it changed the jury ratings. Runs in the longer sprint tipped at the same mean round as rep1. H2–H4 are therefore weak tests.

Rerunning a configuration was itself a shift. The second replicate changed the outcome in only 1 of 14 configurations, yet the clock lost 0.196 AUROC [0.092, 0.292] and the oracle 0.115 [0.051, 0.193]. The observable monitors moved by −0.07 to +0.11, with intervals that include zero. In 5 of the 6 configurations that tipped in both replicates, rep1 tipped later (mean 4.0 rounds, sign test p = 0.22). rep1 also ran after all other twin runs, so run order and replicate are confounded. Judged by outcome flips, this noise looked negligible. For the clock, it was twice the drop the suite was built to detect. Shift tests therefore need a noise floor from several replicates, run interleaved with the shifted arms.

Descriptively, global_full had the highest AUROC in every arm and in both replicates (0.85–0.95). We chose the pooled comparison over all twin rows after seeing the results. There global_full led the GNN by +0.082 [+0.049, +0.118]. Pairwise separated from neither (against the GNN +0.034 [−0.044, +0.107], against global_full −0.048 [−0.118, +0.016]). On the held-out rows, global_full and the GNN had tied (0.816 and 0.817).

We pre-registered a confirmatory replication of this lead (H7) and pushed it before its first episode started (commit e319c9e7). Its design:
- **Runs:** the 14 night_vx configurations, unchanged, with two replicate seeds never used before (28 episodes). No episode starts after a fixed cut-off, all finished episodes are evaluated, and a configuration without a finished new run drops out.
- **Predictors:** the same 12, frozen as in night_vx. Predictions and the evaluation script are pushed before a single locked evaluation, which is reported whatever its outcome.
- **Primary test:** D = AUROC(global_full) − AUROC(GNN) on all rows of the new runs. The CI comes from a paired bootstrap over the 14 configurations, where each draw brings both new runs of a configuration (10,000 draws, 95 % percentile interval). H7 is supported if the lower bound exceeds 0. It is a single test, uncorrected.
- **Secondary contrasts, without a decision rule:** D time-matched ([[H7 secondary: X [L, U]]]), global_full against the hybrid ([[H7 secondary: X [L, U]]]) and pairwise against the GNN ([[H7 secondary: X [L, U]]]).

[[H7: N of 28 episodes completed, X tipped; configurations dropped: none / list]] D was [[H7: X [L, U]]], so H7 is [[supported / not supported]]. A confirmation would show only that the lead holds on new seeds of these 14 critical-band configurations, not on new configurations. Percentile intervals over 14 configurations are also anti-conservative.

The planned arm with agents fine-tuned for persistence was dropped after its canary episode. In that episode 44 % of the fine-tuned 4B model's replies were invalid JSON. A mechanical repair would have made 91 % of them valid (post hoc), but its agents wrote a message in only 2 % of valid turns, against 18–19 % for the other models. We replaced the arm with a pre-registered side study without a swarm, judged blind by Claude Haiku 5.5. Under hand-written peer-pressure probes, the fine-tuned model held its position in 48 of 60 replies, against 36 of 60 for its base (sign test over 12 probes p = 0.73; Fisher test on replies p = 0.028). It also updated less often on decisive evidence (5 against 11 of 20, p = 0.11). The base model also rarely wrote messages on single turns (4 of 60, against 6 for the fine-tuned model). The near-silence in the swarm is therefore probably not an effect of the fine-tune.

## 5. Discussion and Limitations

**What this means for operators.** The alarm threshold was set on training data at 5% false positives per snapshot. At that threshold, the five primary monitors warned in 17–28 of 52 tipped held-out runs, a median 2–5.5 rounds before the tip. That is enough time to pause an agent or isolate a channel. They also raised false alarms in 10–20 of 48 untipped runs; the clock did so in all 48. Monitors should be tested against a clock that knows the deadline. Under the pre-specified time matching, no monitor beat the clock after Holm correction. When matching on the absolute round instead (sensitivity analysis), all five did (p ≤ 0.0002).

**Content beats structure.** In cross-validation (exploratory, one seed), randomly rewiring the graph left the GNN's AUROC unchanged (−0.004 [−0.032, +0.023]). Removing the jury's content ratings cost 0.06–0.08 AUROC and 0.10–0.13 time-matched AUROC. On held-out data the frozen GNN tied counted features (+0.004 [−0.036, +0.046]). In our teams the graph added nothing we could detect, which is a known risk for graph-level prediction (GRADE, 2026).

**A cheap zero-shot LLM monitor is a strong baseline.** The best held-out point estimate came from a monitor we never trained: the zero-shot LLM monitor reading single conversations (pairwise), at 0.855 [0.808, 0.899]. The GNN + tabular hybrid reached 0.832 and the frozen GNN 0.817, and no difference was significant after Holm correction. In the validation suite, the zero-shot LLM monitor reading the full transcript (global_full) had the highest AUROC in every block (0.85–0.95, descriptive). Post hoc, it led the frozen GNN by +0.08 [+0.05, +0.12].

Hypothesis H7 tests this lead on 28 runs that did not exist when it was pre-registered (ANALYSIS_PLAN.md, Nachtrag 3). The runs are replicates 2 and 3 of the same 14 configurations. The statistic is D = AUROC(global_full) − AUROC(frozen GNN) over all their labelled snapshots, with a paired bootstrap over configurations (10,000 draws). H7 is supported if the 95% interval lies above 0. [[H7: D = X [95% CI], N of 28 runs; supported / not supported]]. Either outcome applies only to new seeds of these configurations.

**The hard part is telling twin runs apart.** Outcomes were largely set by the configuration. Only 15 of 104 configurations with repeated runs had mixed outcomes (ICC 0.73), and configuration factors alone predicted tipping with grouped-CV AUROC 0.82. Within the nine held-out configurations with mixed outcomes, the trained monitors fell to 0.59–0.65, below the clock (0.68). The pairwise and global_full LLM monitors reached 0.82 and 0.75 there (secondary). In the pre-registered test H1 (29 run pairs from 6 configurations, partly blind), the frozen GNN scored 0.76 [0.45, 0.97]. H1 was therefore not supported, but the interval cannot rule it out. The oracle reached only 0.55 on these pairs.

**Replicate noise.** Re-running the 14 validation configurations changed only one outcome. Yet the clock's AUROC fell by 0.20 [0.09, 0.29], the monitors moved by −0.07 to +0.11, and tipping came later in 5 of 6 configurations (sign test p = 0.22). That replicate ran last in Part A, so run order may be a confound. Against this noise floor, no monitor dropped detectably under any of the four shifts (0 of 96 comparisons). That gives no evidence of a large degradation, at a resolution of about 0.2 AUROC (post hoc; the plan assumed 0.1).

**Limitations.**
- One simulated domain, 24 agents, two shortcut types and four Qwen and Gemma models with reasoning off; no comparison with real teams. The tipping rate reflects our calibration.
- 232 of 252 runs contained a seed. The peer-message association is observational (no isolation control) and limited to skip-checks. With binary exposures it cannot separate simple from complex contagion (Centola & Macy, 2007).
- Few positives: 45 tipped training runs, and seed noise up to 0.04 AUROC. The held-out splits are not blind, and the GNN was selected on the same cross-validation rows used to compare it.
- Unequal inputs: the LLM monitors read task words (e.g. `skip_checks`); global_full sees elapsed time (Spearman 0.83 with the round); Claude Haiku 5.5 is both a monitor and a judge.
- Monitors that read only messages miss silent violations and triggers that arrive in tool output.
- Only successful shortcut uses are labelled. Judge agreement and hand labels were not measured, and the leakage checks ran only on the earlier generator design.
- Validation suite: 14 configurations and anticonservative intervals. Three of the four arms only partly reached their aim, and the stored GNN holds 15 of 40 ensemble states.
- Not done: run-size baseline, GNN without message passing, held-out ablations, horizon variation, evaluation-awareness analysis, adversarial tests, and trained persistence in a swarm.

**Future work.** An isolation control would give causal evidence for contagion. Larger, more locally connected teams would show whether structure matters; a synthetic testbed without LLM agents suggests when it could ([[Appendix ref]]). Further steps: more domains, shortcuts and replicates, a label for false success claims, monitors that read tool outputs, and interventions triggered by warnings.

## 6. Conclusion

We built a simulator of 24-agent LLM teams that sometimes break a rule together, labelled from tool logs, and a dataset of 252 runs in 112 configurations, of which 101 tipped. On 36 held-out configurations, monitors reading only messages predicted tipping three rounds ahead with AUROC 0.800–0.855, against 0.781 for the clock (round number only). No pre-specified comparison survived Holm correction. The frozen GNN did not outperform counted features (gradient-boosted trees) or the zero-shot LLM monitor reading single conversations, and rewiring its graph cost nothing in cross-validation. What agents said carried the warning. [[H7: in the pre-registered replication, AUROC(global_full) − AUROC(frozen GNN) = X [95% CI]; supported / not supported.]] Monitoring cost cents per run. The hard parts are getting the data and telling which run of a risky setup will tip. We release the simulator, the dataset and the pre-registration.

## Code and Data

**Code:** https://github.com/mauricioneubecker-star/apart_hackathon_agentswarm_monitor. Branch `night-vx-validation` holds the simulator, labels, jury, features, zero-shot LLM monitors and analyses. Branch `gnn-opt-torch` holds the frozen GNN, and `gnn-opt` the evaluation harness and tabular baselines.

**Data:** [[TODO: data link]].

**Pre-registration:** `ANALYSIS_PLAN.md` was committed as `4e6e9986` (8 Nov, 19:25 CET) and has since changed only through dated addenda. The held-out comparison ran shortly before that commit; per Nachtrag 1, its results were read only afterwards. The validation inputs were frozen (`d083547d`) before the evaluation (`bb3f665d`), and the H7 addendum (`e319c9e7`) was pushed before any of its runs existed. The unchanged validation script was executed twice on the frozen inputs, once locally and once independently in a separate cloud session; all result files are byte-identical.

**Review artifacts:** `analysis/review/` and `paper/STORYLINE_CHECK.md`.

**Info-hazard note:** all exploits are file or merge manipulations inside a mock repository. Attack texts are plain and not optimised. We do not publish optimised injection prompts.

## LLM Usage Statement

We used Claude through Claude Code (mainly Claude Opus 5.5) to search and summarise literature, discuss design choices, write large parts of the code, run simulations and analyses, and draft sections of this report, including this one. Separate Claude agents re-computed the analyses from code and data without seeing our conclusions. Others checked our claims against their sources (`analysis/review/`, `paper/STORYLINE_CHECK.md`). [[team: state what each member verified by hand (design decisions, code, every number, every reference); keep only what is true]]
