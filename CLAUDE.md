# CLAUDE.md

## Working with the cloud session

Two Claude sessions work on this project: the laptop session (Claude Code on the laptop, which runs every job) and
a cloud session that reads and writes files in ~/socialscope and ~/socialscope_data through a file bridge but
cannot run commands. To keep the two from overwriting each other:

1. **Never discard uncommitted work.** Never checkout, reset, stash or restore a file in the working tree without
   first running `git status` and `git diff` on it. Uncommitted changes may be the cloud session's work. If a file
   differs from git, commit it or ask; don't discard it. (On the night of Nov 2-3, 2026,
   docs/orl-archive-results.md was reset to an older version this way.)
2. **Commit promptly.** Commit and push in small commits by topic. Commit any file the cloud session changes as
   soon as you notice it.
3. **Predictions are timestamped records.** Commit a `*-predictions.md` file before running or reading the data it
   predicts. Never edit an existing prediction; additions go at the end as dated addenda. Results go in a separate
   `*-results.md` file, misses included.
4. **Check before editing the other session's scripts.** Read a script's current contents before editing it. Fix
   bugs in place with a short comment saying what was wrong and when (like the websocket ping comment in
   scripts/dgg_live_logger.py), so the other session can see why it changed.
5. **Privacy.** Changed Nov 5 2026 by Joseph: DGG chat nicks are now kept raw. The live logger stores "nick" next
   to the hash "u" (HMAC-SHA256 with ~/socialscope/.socialscope_salt, first 16 hex chars), and the public site
   shows DGG handles in its chatter tables (message counts and activity only). Still in force: never print the
   salt; Reddit usernames stay hashed; chat accounts are never linked to Reddit accounts or to real-world
   identities; no per-person hostility, raid or harassment labels are published; private sample files
   (samples_*.jsonl) are never committed or published.
   **Exception, added Nov 10 2026 by the user: confirmed bots can be named, including on the public site.**
   - "Confirmed" means Bot Bouncer has banned the account, rechecked within 7 days before it is published. If a
     listing is reversed, the name comes off the site at the next rebuild.
   - Pending accounts, detector flags and the v7.1 high tier are leads, not confirmations. They stay hashed.
   - Hijacked or bought accounts: only posts from the bot period (from the takeover break on) appear next to the
     name. The earlier history was a real person's and stays hashed and aggregate.
   - The label is attributed as "listed as a bot by Bot Bouncer", with a link to the listing, not as our own verdict.
   - Everything else in this rule still applies to every other account, and never link a bot to a real-world identity.
   **Bots Bot Bouncer hasn't found (added Nov 10 2026 by the user; plan in docs/bot-publishing-plan.md).** Two
   paths, and nothing else puts our own finds on the site:
   - *Path 1, feed Bot Bouncer.* Detector flags plus their evidence packets are reviewed by a person and submitted
     to Bot Bouncer by the user (Claude never posts or submits on Reddit). An account Bot Bouncer bans is published
     under the rule above, with "found by socialscope".
   - *Path 2, our own standard.* An account may be published as "suspected bot (socialscope)" only if all of these
     hold:
     - it meets the strict evidence bar as frozen in docs/bot-publishing-predictions.md;
     - that bar has passed its blind test (see the plan);
     - a person has read the account;
     - the page shows the evidence and how to dispute it.
     If the bar has not passed, or later fails, nothing goes up this way.
   - Packets, review notes and the submission tracker contain usernames: they live in ~/socialscope_data/botfinds/
     and are never committed.
6. **Long jobs.** Every long job runs under nohup with systemd-inhibit, uses absolute paths, gets a line in
   ~/socialscope_data/jobs.tsv, and writes progress where status.sh can see it. For "wait until job X ends" loops,
   use a PID file or a pattern anchored to the start of the command line, e.g.
   `pgrep -f '^python3 -I scripts/orl_aggregate.py'`. An unanchored pattern such as `pgrep -f orl_aggregate.py`
   (or `"python3 .*orl_aggregate"`) also matches any shell whose command text merely mentions the script, such as
   a leftover `bash -c` from a launch or status check, and the loop never exits. That is what stalled orl2 on
   Nov 2-3.
7. **Servers serve only status folders.** Progress and status servers serve only their own status folder
   (`python3 -m http.server --directory <dir>`), never a data folder. Current ports: 8765 dgg_progress,
   8766 orl_progress, 8767 dgg_live_status.
8. **Standing service: dgg-live** (systemd --user, unit copy in ops/laptop/dgg-live.service). Restart it after any
   change to scripts/dgg_live_logger.py, then check that status.json shows plausible messages per minute and far
   fewer distinct users than messages.
9. **Say how jobs ended.** When you finish or stop a job, say so in STATUS.txt and jobs.tsv in plain terms (done /
   stopped / failed, and why), so the next session doesn't have to guess.
