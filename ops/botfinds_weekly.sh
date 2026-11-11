#!/bin/bash
# Weekly Bot Bouncer status check for Path 1 (docs/bot-publishing-plan.md, build step 2). Written Nov 11, 2026.
# Run by the botfinds-weekly.timer (systemd --user; unit copies in ops/laptop/). Pulls r/BotBouncer posts from the
# last 14 days (or from the earliest still-open submission, if older) into reddit_pulls/bb_weekly/, checks the zip,
# then updates the private tracker with scripts/botfinds/weekly_check.py. Logs to ~/socialscope_data/botfinds_weekly.out
# (jobs.tsv line "botfinds_weekly"). No usernames reach the log: both scripts print counts only.
set -u
D=/home/probs/socialscope_data
R=/home/probs/socialscope
OUT=$D/botfinds_weekly.out
exec >>"$OUT" 2>&1
echo "botfinds_weekly start $(date '+%Y-%m-%d %H:%M:%S')"
START=$(/usr/bin/python3 -I - <<'EOF'
import csv, os
from datetime import date, timedelta
s = date.today() - timedelta(days=14)
p = os.path.expanduser("~/socialscope_data/botfinds/tracker.csv")
if os.path.exists(p):
    for r in csv.DictReader(open(p)):
        if r.get("status") in ("submitted", "pending") and r.get("submitted_utc"):
            s = min(s, date.fromisoformat(r["submitted_utc"][:10]))
print(s.isoformat())
EOF
)
END=$(date -d tomorrow +%F)
echo "pulling r/BotBouncer posts $START to $END (end exclusive, Eastern)"
mkdir -p "$D/reddit_pulls/bb_weekly"
# One Arctic Shift pull at a time: wait (up to 12 h) while another pull runs. Patterns are anchored to the start of
# the command line so a shell that only mentions a script doesn't match (CLAUDE.md rule 6).
for i in $(seq 1 144); do
  pgrep -f '^(/usr/bin/)?python3 .*(from socialscope import arctic|scripts/reddit_pull.py|pull_user_histories)' >/dev/null || break
  [ "$i" = 1 ] && echo "another Arctic Shift pull is running; waiting"
  sleep 300
done
# Nov 11: first version used reddit_pull.py, which treats Arctic Shift's 422 "Timeout" as permanent and exits 0.
# arctic.pull_subreddits waits those out and resumes from its .jsonl; up to 6 tries, 5 min apart.
LBL="$START"_to_$(date -d "$END -1 day" +%F)
Z="$D/reddit_pulls/bb_weekly/$LBL/r_BotBouncer_posts_$LBL.zip"
rc=1
for try in $(seq 1 6); do
  echo "pull try $try $(date '+%H:%M:%S')"
  cd "$R" && PYTHONUNBUFFERED=1 /usr/bin/python3 -I -c "
import sys; sys.path.insert(0, '$R')
from socialscope import arctic
arctic.pull_subreddits(['BotBouncer'], '$START', '$END', kinds=('posts',), out_dir='$D/reddit_pulls/bb_weekly')
" 2>&1 | tr '\r' '\n' | grep -v '^\s*$' | tail -3 | /usr/bin/python3 -I "$D/stamp.py" "$D/reddit_pulls/bb_weekly/pull_log.txt"
  if [ -f "$Z" ] && [ ! -f "${Z%.zip}.jsonl" ]; then rc=0; break; fi
  sleep 300
done
echo "pull rc=$rc"
# RAM fault (Nov 2026): test the new zip's CRC before anything reads it.
if [ "$rc" -ne 0 ] || [ -z "$Z" ] || ! unzip -tqq "$Z"; then
  echo "pull or zip check failed, tracker not updated rc=1"
  echo "botfinds_weekly end $(date '+%Y-%m-%d %H:%M:%S')"
  exit 1
fi
/usr/bin/python3 -I "$R/scripts/botfinds/weekly_check.py"
echo "check rc=$?"
echo "botfinds_weekly end $(date '+%Y-%m-%d %H:%M:%S')"
