# Brigade alarm

Flags hours where unusually many accounts from other tracked subs pile into a sub.
Results and predictions live in the claude.ai project (claude/brigade-alarm-*.md).

## Steps (laptop)
1. Pull the week as usual: `scripts/reddit_pull.py` for all 18 subs (comments), keep the zips under
   `~/socialscope_data/reddit_pulls/<week>/`.
2. Compact each week: `python3 -I scripts/brigade_alarm/load_week.py <week_name> <week_dir_with_zips> <compact_dir> <salt_file>`
   (keeps author hash, sub, time, thread only). Use the SAME salt file for every week; a new salt means recompacting
   all weeks, or homes won't match across weeks. Keep the salt file out of git.
3. Ban list: `python3 -I scripts/brigade_alarm/load_bb.py <compact_dir>/bb_banned.npy <salt_file> <bb zips...>`
   (check the output name the main script expects: bb_banned.npy in compact_dir).
4. Run: `python3 -I scripts/brigade_alarm/brigade_alarm.py <compact_dir> <out_dir> --test-week <week_name>`.
   Defaults are v2: homes from baseline weeks, exposure = sub total comments, aug25 excluded, NB alarm.
   v2 alarms = rows in alarms_nb with "oa" in triggered and outsider_accounts >= 5.

