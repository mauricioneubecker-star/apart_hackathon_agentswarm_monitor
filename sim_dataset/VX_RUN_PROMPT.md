# Claude Code prompt: run the validation suite `night_vx_*`

Paste everything below the line into Claude Code on the Mac that ran the night batch (macOS sandbox, `.venv`,
`secrets.local.json` with the Adaption keys and the Anthropic key). Fill in the two model ids first.

---

You are running the validation suite of our hackathon project (Apart Swarm Alignment Hackathon, deadline
Sun 8 Nov 23:59 AoE). The repository is `mauricioneubecker-star/apart_hackathon_agentswarm_monitor`, branch
`night-vx-validation`. Work in `sim_dataset/` unless stated otherwise. Design and protocol are in
`sim_dataset/VALIDATION.md`; read §0, §2.3, §2.5 and §2.6 before you start. Your job is to **run** the suite and
deliver clean data. It is **not** to change the design or evaluate any monitor.

**Persistence fine-tune (Part C):**
- `SWARM_FT_MODEL` = `<FILL IN: provider id of the fine-tuned persistent 4B model>`
- `SWARM_FT_BASE_MODEL` = `<FILL IN: provider id of its 4B base model, or NONE if the base is not hosted>`

If either is still a placeholder, ask me once. If I don't answer, run without Part C and say so.

## Rules
- Never change the generator design, `dataset/vx_selection.json`, scenario files, labels config or θ/Δ. Do not
  re-run `tools/vx_select.py`. Code changes are allowed only for clear infrastructure bugs that block running (crash,
  API parameter rejected). Keep them minimal, commit them separately and tell me.
- Never delete or overwrite `runs_night/` or finished episodes in `runs_vx/`. Restarts resume, because finished
  episodes (with `meta.json`) are skipped.
- Never print, log or commit API keys (`secrets.local.json` stays untracked).
- Do not train or evaluate the GNN or any monitor on `runs_vx`. The protocol requires one evaluation after the models
  are frozen. Only descriptive checks.
- When a gate below fails, take the stated fallback, log it in `runs_vx/_logs/vx_decisions.md` and keep going. Stop
  and ask me only for something not covered here.
- Use `.venv/bin/python` for everything. Long waits: poll with `sleep` in steps of ≤ 9 minutes.

## Steps
1. **Branch and environment**
   - Run `git fetch origin && git checkout night-vx-validation && git pull`.
   - `.venv` must exist with `requirements.txt` installed (Python ≥ 3.11); install what is missing.
   - Check that `secrets.local.json` exists, without printing it.
   - Check power with `pmset -g batt`: the Mac must be on AC with the lid open. If it is on battery, tell me and
     wait a few minutes.
2. **Determinism and checks.** Every check must pass; otherwise stop and report.
   - Run `generator/generate.py core`. After that, `git status --porcelain sim_dataset/dataset` must be empty. A
     changed `index.parquet` is fine if pyarrow wrote it.
   - Run `tools/vx_check.py`: 0 errors. Notes about `topo` are expected.
   - Run `generator/validate.py core --smoke 0.1`: 0 errors. This uses the real macOS sandbox.
   - Run `CANARY=0 bash tools/preflight.sh`: all OK. This covers keys, judges and the fake end-to-end run.
3. **GLM gate**
   - Run `tools/check_endpoint.py` and check that `glm-5.2` answers.
   - Run one real suite episode:
     `runner/run.py simulate --where "split=='night_vx_pop'" --replicates 1 --limit 1 --out runs_vx`.
   - Then `runner/run.py labels --out runs_vx` and `tools/vx_summary.py runs_vx`.
   - Pass if: no `error.txt`, invalid JSON of the `glm-5.2` agents < 15 %, and the GLM agents sent messages.
   - Fallback: exclude `night_vx_pop` and run the reserve `night_vx_pop_bal` (balanced 6/6/6/6 mix) instead.
4. **Fine-tune gate** (skip if there are no ids)
   - Run `tools/ft_check.py --model $SWARM_FT_MODEL --base $SWARM_FT_BASE_MODEL --runs runs_night
     --out runs_vx/_logs/ft_check.json` (create the folder first). If there is no base, leave out `--base`.
   - If the endpoint rejects `reasoning_effort`, rerun with `--no-reasoning-flag` and set
     `SWARM_FT_OMIT_PARAMS=reasoning_effort` for all later steps.
   - Pass if:
     - API 200;
     - valid JSON ≥ 90 % for the fine-tune and (if present) the base;
     - HOLD clearly above the base;
     - UPDATE not far below the base.
   - Canary: with the variables exported, run one episode of `night_vx_ft` (`--limit 1 --replicates 1 --out runs_vx`)
     and, if the base is present, one of `night_vx_ft_base`. Pass if: no `error.txt`, invalid JSON of the 4B agents
     (`ft4-persistent` / `base4` in `vx_summary.py`) < 15 %, and the 4B agents act and send messages.
   - Fallbacks:
     - fine-tune fails → drop both `night_vx_ft*` splits;
     - base not hosted or fails → keep only `night_vx_ft` and note "Part C = population shift only, not
       attributable to persistence".
5. **Full run.** Build `WHERE` from the gates. The default is
   `split.str.startswith('night_vx') and split != 'night_vx_pop_bal'`, with the exclusions from steps 3 and 4.
   If GLM failed, use `STAGE2_WHERE="split=='night_vx_pop_bal'" STAGE2_REPS=1`; otherwise
   `STAGE2_WHERE="split == '__none__'"`. Start everything in one shell, so the variables reach the background job:
   ```
   export SWARM_FT_MODEL=... SWARM_FT_BASE_MODEL=... [SWARM_FT_OMIT_PARAMS=reasoning_effort]
   OUT=runs_vx WHERE="..." STAGE2_WHERE="..." STAGE2_REPS=1 STOP_AT=2359 nohup bash tools/night_run.sh > runs_vx_night.out 2>&1 &
   ```
   Expected: up to 121 episodes, about 4 h on 4 sim keys. Check how many keys `secrets.local.json` has; all except
   the jury keys simulate.
6. **Monitoring** every ~15 min until `runs_vx/_logs/DONE` exists:
   - `tail runs_vx/_logs/night.log`, `tools/night_util.py finished runs_vx`, and the number of `error.txt` files.
   - If ≥ 3 errors pile up in the same split, read them. If one model or arm fails systematically (format, 4xx), kill
     with `kill $(cat runs_vx/_logs/night.pid)`, restart with that split excluded and log it. Restarting resumes.
   - Send me a one-line status every hour.
7. **Completion**
   - Run `runner/run.py status --out runs_vx`. Every planned episode of the chosen splits must be finished, with
     jury ≥ 95 % per run and features present. Otherwise rerun
     `runner/run.py jury --out runs_vx`, `labels --out runs_vx` and `features --missing-only --out runs_vx`.
   - Run `tools/vx_summary.py runs_vx > runs_vx/_logs/vx_summary.md`. `report.md` and `dynamics.md` come from
     `night_run.sh`.
   - Sanity checks, report only, do not fix:
     - the time arm has 36 rounds;
     - the enf arm has `sanction` events;
     - the glm arm has GLM calls;
     - the 4B arms have calls by `ft4-persistent` / `base4`;
     - Part B runs are `rep0` and `rep1` of the `night_vx_rep` copies.
8. **Commit and push.** Commit `sim_dataset/runs_vx/` (incl. `_logs`), the updated `dataset/reports/` and
   `vx_decisions.md` on `night-vx-validation`, and push. If the push is rejected for size, commit and push per
   split, in several steps. End the commit messages with the usual co-author line.
9. **Final report to me:**
   - the gate results;
   - what was excluded and why;
   - the per-arm table from `vx_summary.md`;
   - the paired outcome flips vs. the id noise floor;
   - for Part C, violators among the 4B agents;
   - the Part B grid;
   - errors and invalid-JSON problems;
   - wall time;
   - the commit hash.

   No interpretation of monitor performance.
