#!/bin/bash
# Bluesky label replay (RUNBOOK step 7), after the 200-frame test passed on Nov 19 2026. Copy to ~/socialscope_data/
# and launch under nohup + systemd-inhibit. labels.py resumes each labeler from its cursor.json and stops once the
# stream has been quiet for 30 s (caught up). Prints counts only (no DIDs), so the .out file is safe to show.
set -u
D="$HOME/socialscope_data"; R="$HOME/socialscope"
echo "bsky_labels start $(date -u +%FT%TZ)"
"$D/bskyenv/bin/python" -I "$R/bluesky/collect/labels.py"
rc=$?
echo "bsky_labels end $(date -u +%FT%TZ) rc=$rc"
