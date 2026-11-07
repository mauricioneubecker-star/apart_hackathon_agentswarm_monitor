#!/usr/bin/env bash
# Overnight batch (DECISIONS.md section 15): simulation with auto-restart, jury in parallel, error guard, then
# labels + features + a report. Keeps the Mac awake. Start in tmux/screen or with nohup and close nothing:
#   nohup bash tools/night_run.sh > night.out 2>&1 &
# Stop: kill the PID in runs_night/_logs/night.pid (finished episodes are kept; a restart resumes).
set -u
cd "$(dirname "$0")/.."
PY=${PY:-.venv/bin/python}
OUT=${OUT:-runs_night}
WHERE=${WHERE:-"split.str.startswith('night')"}
MAX_ERRORS=${MAX_ERRORS:-8}          # guard: stop the batch when this many episodes failed (error.txt)
EXTRA=${EXTRA:-}                     # e.g. EXTRA="--persistent-model <ft-id>" for the fine-tuned arm
mkdir -p "$OUT/_logs"
LOG="$OUT/_logs"
echo $$ > "$LOG/night.pid"
ts() { date "+%Y-%m-%d %H:%M:%S"; }

caffeinate -dimsu -w $$ &            # no sleep while this script runs (display may still turn off)

$PY runner/run.py jury --watch --out "$OUT" >> "$LOG/jury.log" 2>&1 &
JURY=$!
echo "$(ts) jury --watch pid $JURY" >> "$LOG/night.log"

( # guard: abort when episodes keep failing instead of burning tokens all night
  while sleep 600; do
    n=$(ls "$OUT"/*/rep*/error.txt 2>/dev/null | wc -l | tr -d ' ')
    if [ "$n" -ge "$MAX_ERRORS" ]; then
      echo "$(ts) GUARD: $n episodes with error.txt -> stopping simulate" >> "$LOG/night.log"
      pkill -f "runner/run.py simulate.*--out $OUT" ; touch "$LOG/ABORTED"; exit 0
    fi
  done ) &
GUARD=$!

for attempt in 1 2 3 4 5 6; do
  [ -f "$LOG/ABORTED" ] && break
  echo "$(ts) simulate attempt $attempt" >> "$LOG/night.log"
  $PY runner/run.py simulate --where "$WHERE" --replicates 0 --order replicate --out "$OUT" $EXTRA >> "$LOG/sim.log" 2>&1 \
    && { echo "$(ts) simulate finished" >> "$LOG/night.log"; break; }
  echo "$(ts) simulate exited with $? - restarting in 60 s (finished episodes are skipped)" >> "$LOG/night.log"
  sleep 60
done
kill $GUARD 2>/dev/null

echo "$(ts) final jury pass" >> "$LOG/night.log"
kill $JURY 2>/dev/null; sleep 5
$PY runner/run.py jury --out "$OUT" >> "$LOG/jury.log" 2>&1
echo "$(ts) labels + features" >> "$LOG/night.log"
$PY runner/run.py labels --out "$OUT" >> "$LOG/labels.log" 2>&1
$PY runner/run.py features --out "$OUT" >> "$LOG/features.log" 2>&1 || \
  $PY runner/run.py features --no-nli --out "$OUT" >> "$LOG/features.log" 2>&1
$PY tools/night_report.py "$OUT" > "$LOG/report.md" 2>> "$LOG/night.log"
echo "$(ts) done -> $LOG/report.md" >> "$LOG/night.log"
