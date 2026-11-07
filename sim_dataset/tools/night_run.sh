#!/usr/bin/env bash
# Overnight run (DECISIONS.md section 15). Built to keep going whatever happens and to leave usable data:
#   - stage 1: the night batch (232 runs, replicate-major; runs to completion even after STOP_AT),
#     stage 2: one more replicate of every non-branch night config until STOP_AT (more data for the GNN;
#     workers take no new episode after STOP_AT; finished episodes are never re-run)
#   - every episode that raises an error is retried from scratch (2x in-process, then again in the next pass);
#     API outages re-queue the episode and wait for the API (50x); a pass that ends early is restarted after 60 s
#   - watchdog: no episode log written for STALL_MIN minutes -> the simulation process is killed and restarted
#   - jury runs in its own restart loop; labels, incremental features and report.md are refreshed every hour,
#     so the morning has data even if the simulation is still running
#   - caffeinate keeps the Mac awake (on power, lid open)
# Start (from sim_dataset/):  nohup bash tools/night_run.sh > night.out 2>&1 &
# Watch:  tail -f runs_night/_logs/night.log   |   Stop: kill $(cat runs_night/_logs/night.pid)  (restart resumes)
set -u
cd "$(dirname "$0")/.."
PY=${PY:-.venv/bin/python}
OUT=${OUT:-runs_night}
WHERE=${WHERE:-"split.str.startswith('night')"}
STAGE2_WHERE=${STAGE2_WHERE:-"split.str.startswith('night') and split != 'night_branch'"}
STAGE2_REPS=${STAGE2_REPS:-3}          # replicates per config after stage 2 (planned: 2)
STOP_AT=${STOP_AT:-0730}               # HHMM: no new stage / pass starts after this time (running ones finish)
STALL_MIN=${STALL_MIN:-30}             # watchdog: minutes without any episode progress
WATCH_EVERY=${WATCH_EVERY:-300}        # watchdog check interval (s)
EXTRA=${EXTRA:-}                       # e.g. EXTRA="--persistent-model <ft-id> --persistent-base qwen3.8-27b"
JURY_EXTRA=${JURY_EXTRA:-}             # tests only: JURY_EXTRA=--fake
LOG="$OUT/_logs"
mkdir -p "$LOG"
echo $$ > "$LOG/night.pid"
ts() { date "+%Y-%m-%d %H:%M:%S"; }
say() { echo "$(ts) $*" | tee -a "$LOG/night.log"; }
before_stop() { [ "$(date +%H%M)" -lt "$STOP_AT" ] || [ "$(date +%H%M)" -gt 1800 ]; }   # evening counts as before
CHILDREN=()
cleanup() { for p in "${CHILDREN[@]:-}"; do kill "$p" 2>/dev/null; done; pkill -f "runner/run.py jury --watch --out $OUT" 2>/dev/null; }
trap 'say "stopped by signal"; cleanup; pkill -f "runner/run.py simulate.*--out $OUT"; exit 1' INT TERM

caffeinate -dimsu -w $$ &
CHILDREN+=($!)

( while true; do                                                   # jury, restarted if it dies
    $PY runner/run.py jury --watch --out "$OUT" $JURY_EXTRA >> "$LOG/jury.log" 2>&1
    echo "$(ts) jury exited ($?), restart in 30 s" >> "$LOG/night.log"; sleep 30
  done ) &
JURY_LOOP=$!
CHILDREN+=($JURY_LOOP)

( while sleep "$WATCH_EVERY"; do                                   # watchdog against hangs
    if pgrep -f "runner/run.py simulate.*--out $OUT" > /dev/null; then
      idle=$($PY tools/night_util.py idle "$OUT" 2>/dev/null || echo 0)
      if [ "${idle:-0}" -ge "$STALL_MIN" ]; then
        echo "$(ts) WATCHDOG: no progress for $idle min -> killing simulate (it restarts)" >> "$LOG/night.log"
        pkill -f "runner/run.py simulate.*--out $OUT"
      fi
    fi
  done ) &
CHILDREN+=($!)

postproc() {                                                       # labels, features (incremental), report
  $PY runner/run.py labels --out "$OUT" >> "$LOG/labels.log" 2>&1
  $PY runner/run.py features --missing-only --out "$OUT" >> "$LOG/features.log" 2>&1 || \
    $PY runner/run.py features --missing-only --no-nli --out "$OUT" >> "$LOG/features.log" 2>&1
  $PY tools/night_report.py "$OUT" > "$LOG/report.md.tmp" 2>> "$LOG/night.log" && mv "$LOG/report.md.tmp" "$LOG/report.md"
}
( while sleep 3600; do postproc; echo "$(ts) hourly report refreshed" >> "$LOG/night.log"; done ) &
POST_LOOP=$!
CHILDREN+=($POST_LOOP)

run_stage() {   # $1 name, $2 where, $3 replicates (0 = planned), $4 extra simulate args
  local name="$1" where="$2" reps="$3" more="${4:-}" pass=0 stuck=0 before after left rc
  while true; do
    left=$($PY tools/night_util.py remaining "$OUT" "$where" "$reps")
    [ "${left:-1}" -eq 0 ] && { say "$name complete"; return 0; }
    if [ -n "$more" ] && [ "$pass" -gt 0 ] && ! before_stop; then say "$name: $left left, STOP_AT $STOP_AT reached"; return 1; fi
    [ "$stuck" -ge 3 ] && { say "$name: 3 passes without progress, $left episodes left - giving up on them"; return 1; }
    pass=$((pass + 1)); before=$($PY tools/night_util.py finished "$OUT")
    say "$name pass $pass: $left episodes to go"
    $PY runner/run.py simulate --where "$where" --replicates "$reps" --order replicate --out "$OUT" \
        --episode-retries 2 --max-aborts 50 $more $EXTRA >> "$LOG/sim.log" 2>&1
    rc=$?
    say "$name pass $pass ended with exit code $rc"
    after=$($PY tools/night_util.py finished "$OUT")
    # only a clean pass without any new episode counts as 'no progress' (killed by the watchdog / API waits do not)
    if [ "$after" -gt "$before" ] || [ "$rc" -ne 0 ]; then stuck=0; else stuck=$((stuck + 1)); fi
    [ -n "$more" ] && ! before_stop && { say "$name: STOP_AT $STOP_AT reached"; return 1; }
    sleep 60
  done
}

say "night run started (pid $$), out=$OUT, stop new work after $STOP_AT"
run_stage "stage 1 (night batch)" "$WHERE" 0
if before_stop; then
  run_stage "stage 2 (replicate $STAGE2_REPS)" "$STAGE2_WHERE" "$STAGE2_REPS" "--stop-at $STOP_AT"
fi

say "simulation done - final jury, labels, features, report"
kill "$JURY_LOOP" "$POST_LOOP" 2>/dev/null; sleep 2
pkill -f "runner/run.py jury --watch --out $OUT"
for i in 1 2 3; do $PY runner/run.py jury --out "$OUT" $JURY_EXTRA >> "$LOG/jury.log" 2>&1 && break; sleep 60; done
postproc
cleanup
$PY runner/run.py status --out "$OUT" | tee -a "$LOG/night.log"
touch "$LOG/DONE"
say "done -> $LOG/report.md"
