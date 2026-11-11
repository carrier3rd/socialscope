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
| 5 | laptop, weekly (build step 2, not written yet) | Check each submitted account's Bot Bouncer flair. Status becomes `banned` or `cleared`. |

Candidates are control accounts (Bot Bouncer had not listed them when the groups were built) flagged at the strict
setting:
- **Threshold:** 0.4828, which flags about 2 in 100 ordinary accounts.
- **Both runs must agree:** the two identical scoring runs agree on the account.
- **Listings check:** the account appears in none of the Bot Bouncer pulls on the laptop. Check the live listing
  before submitting, because those pulls are only as fresh as the last bb_* pull.

A flag is only a lead. The evidence files exist so a person can decide.
