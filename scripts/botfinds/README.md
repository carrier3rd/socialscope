# botfinds: Path 1 of docs/bot-publishing-plan.md

This feeds Bot Bouncer the bots our detector finds that it hasn't listed. Written Nov 11, 2026.

Everything these scripts write goes to `~/socialscope_data/botfinds/`, which holds usernames. None of it is ever
committed or pasted into chat.

| Step | Who | What |
|---|---|---|
| 1 | laptop | `python3 -I scripts/botfinds/build_packets.py` writes one evidence file per candidate to `packets/<hashed id>.md` and adds a blank row to each reviewer's file. Run with `--dry-run` for counts only. The scan of about 18 GB of history zips is a long job, so run it under nohup with a jobs.tsv entry. |
| 2 | user and cloud session, separately | Read each evidence file. Enter bot / not bot / unsure plus one line of reasons in **your own file only**: `review_user.csv` (user) or `review_cloud.csv` (cloud session). Don't open the other file before your own call is in. |
| 3 | laptop | `python3 -I scripts/botfinds/review_merge.py`: an account is submitted only if both reviewers called it bot. Any other pair of calls is a hold, and a row with a blank call waits. It writes `review.csv`, adds the accounts to submit to `tracker.csv`, and drafts the text in `submit_queue.md`. |
| 4 | user only | Submit through Bot Bouncer's normal Reddit process, then set `status=submitted` and `submitted_utc` in `tracker.csv`. Claude never posts. |
| 5 | laptop, weekly | `ops/botfinds_weekly.sh`, run by `botfinds-weekly.timer` on Mondays at 06:30 (units in `ops/laptop/`), pulls the recent r/BotBouncer posts once no other Arctic Shift pull is running. `weekly_check.py` then sets each submitted account to `banned` / `pending` / `cleared` / `gone`, along with the listing link and recheck date. Log: `~/socialscope_data/botfinds_weekly.out`. A row that stays pending for more than 14 days needs a check by hand, because Arctic Shift keeps a post's flair as it was when captured. |

| 6 | laptop, every site rebuild | `ops/publish_site.sh` runs `build_site_bots.py`, which writes `data/botfinds.json`. The site's Bots tab stays hidden until an account is banned, its Bot Bouncer status was checked in the last 7 days, and it has a listing link. Posts are shown only for a takeover break or an account with no earlier history, with handles, links and other users' names masked. |

Candidates are control accounts (Bot Bouncer had not listed them when the groups were built) flagged at the strict
setting:
- **Threshold:** 0.4828, which flags about 2 in 100 ordinary accounts.
- **Both runs must agree:** the two identical scoring runs agree on the account.
- **Listings check:** the account appears in none of the Bot Bouncer pulls on the laptop. Check the live listing
  before submitting, because those pulls are only as fresh as the last bb_* pull.

A flag is only a lead. The evidence files exist so a person can decide.
