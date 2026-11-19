#!/bin/bash
# Bluesky 24-hour pilot: the Jetstream recorder. Copy to ~/socialscope_data/ and launch as in bluesky/RUNBOOK.md.
# The end time is fixed the first time this runs and stored in a file, so relaunching the same nohup line after
# a reboot or a kill carries on to the same end time. The recorder itself resumes from its saved cursor.
set -u
D="$HOME/socialscope_data"; R="$HOME/socialscope"; PY="$D/bskyenv/bin/python"
mkdir -p "$D/bluesky/state" "$D/bluesky_status"
END_FILE="$D/bluesky/state/pilot_end_epoch"
[ -f "$END_FILE" ] || echo $(( $(date +%s) + 24*3600 )) > "$END_FILE"
END=$(cat "$END_FILE")
echo "bsky_pilot start $(date -u +%FT%TZ), ends $(date -u -d @"$END" +%FT%TZ)"
while [ "$(date +%s)" -lt "$END" ]; do
  LEFT=$(( END - $(date +%s) ))
  "$PY" -I "$R/bluesky/collect/jetstream.py" --hours "$(awk "BEGIN{print $LEFT/3600}")"
  echo "recorder exited with $? at $(date -u +%FT%TZ)"
  [ "$(date +%s)" -lt "$END" ] && sleep 10
done
echo "bsky_pilot end $(date -u +%FT%TZ) (done: 24 hours reached)"
