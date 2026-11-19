#!/bin/bash
# Bluesky 24-hour pilot: hourly AppView, PLC and Constellation passes while the recorder runs.
# Stops at the end time written by bsky_pilot_queue.sh (a file, not a pgrep pattern: CLAUDE.md rule 6).
# Every command prints counts only, so passes.txt is safe in the status folder.
set -u
D="$HOME/socialscope_data"; R="$HOME/socialscope"; PY="$D/bskyenv/bin/python"; C="$R/bluesky/collect"
END_FILE="$D/bluesky/state/pilot_end_epoch"
until [ -f "$END_FILE" ]; do sleep 5; done
END=$(cat "$END_FILE")
OUT="$D/bluesky_status/passes.txt"
echo "bsky_pilot_passes start $(date -u +%FT%TZ)"
while [ "$(date +%s)" -lt "$END" ]; do
  {
    echo "--- pass $(date -u +%FT%TZ)"
    "$PY" -I "$C/appview.py" threads
    "$PY" -I "$C/appview.py" profiles --limit 2000
    "$PY" -I "$C/plc.py" --limit 1000
    "$PY" -I "$C/appview.py" histories --limit 200
    "$PY" -I "$C/backlinks.py" --limit 20
  } >> "$OUT" 2>&1
  tail -n 6 "$OUT"
  sleep 3600 &
  wait $!
done
echo "bsky_pilot_passes end $(date -u +%FT%TZ) (done: pilot end time reached)"
