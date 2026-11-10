#!/bin/bash
# Re-pull queue for the in-sub bot study (scripts/repull_run). Copy to ~/socialscope_data/repull_queue.sh and launch:
#   cd ~/socialscope_data && nohup systemd-inhibit --what=idle:sleep --mode=block --who=socialscope \
#       --why="repull histories" ./repull_queue.sh > repull_queue.out 2>&1 &
#   nohup ~/socialscope_data/status.sh > ~/socialscope_data/status_loop.out 2>&1 &
# Add to ~/socialscope_data/jobs.tsv (tab-separated) before launching:
#   repull_gap	reddit_pull	repull_queue.sh	repull_queue.out	repull_gap start	repull_gap end	reddit_pulls/bb_oct20_27/pull_log.txt
#   repull	history	repull_queue.sh	repull_queue.out	repull start	repull end	reddit_pulls/repull_history_log.txt
# Steps: 1) Bot Bouncer listings Oct 20-27 (the inventory gap), 2) cohorts, 3) histories ending at the anchor, test
# side first. Every step resumes if re-run. Usernames never reach the logs (pull.py masks them).
set -u
D=$HOME/socialscope_data
R=$HOME/socialscope
GAP=$D/reddit_pulls/bb_oct20_27/2026-10-20_to_2026-10-27/r_BotBouncer_posts_2026-10-20_to_2026-10-27.zip

echo "repull_gap start $(date)"
if [ -f "$GAP" ]; then
  echo "gap pull already present, skipping"
else
  mkdir -p "$D/reddit_pulls/bb_oct20_27"
  cd "$R" && PYTHONUNBUFFERED=1 python3 scripts/reddit_pull.py --subs BotBouncer --kinds posts --start 2026-10-20 --end 2026-10-28 \
      --out "$D/reddit_pulls/bb_oct20_27" 2>&1 | python3 -I "$D/stamp.py" "$D/reddit_pulls/bb_oct20_27/pull_log.txt"
fi
echo "repull_gap end $(date) rc=$?"

echo "repull start $(date)"
mkdir -p "$D/repull"
cd "$R" && python3 -I scripts/repull_run/groups.py > "$D/repull/groups_run.txt" 2>&1
rc=$?
cat "$D/repull/groups_run.txt"
if [ $rc -ne 0 ]; then echo "repull end $(date) rc=$rc (groups.py failed; see repull/groups_run.txt)"; exit $rc; fi
cd "$R" && python3 -I scripts/repull_run/pull.py --only test  > "$D/reddit_pulls/repull_history_log.txt" 2>&1
rc1=$?
cd "$R" && python3 -I scripts/repull_run/pull.py --only train >> "$D/reddit_pulls/repull_history_log.txt" 2>&1
rc2=$?
rc=$(( rc1 > rc2 ? rc1 : rc2 ))
echo "repull end $(date) rc=$rc"
