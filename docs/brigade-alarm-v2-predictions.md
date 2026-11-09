# Brigade alarm v2: predictions for the Nov 3-9 week (written Nov 5, 2026, before that week is pulled)

v1 was scored on the Oct 27 week (brigade-alarm-results.md). The changes below were built while looking at that week,
so Oct 27 is now a development week and cannot test them. The Nov 3-9 week is the clean test.

## v2 method (frozen)
- Home community from baseline weeks only (the test week can't define who counts as an outsider).
- Expected outsider activity scales with the sub's total comments that hour (absorbs site-wide surges, and partly the
  [deleted]-author difference between older and newer pulls).
- aug25 dropped from the baseline (14 of 18 comment files truncated).
- Alarm = outsider ACCOUNTS above the negative binomial 99.9th percentile AND at least 5 outsider accounts.
  Comment-count spikes from 3 or fewer accounts are logged separately as "argument" flags, not brigades.
- Baseline for the Nov 3-9 test: aug18, sep08, sep22, oct13, oct20, oct27.
- Script: scripts/brigade_alarm/brigade_alarm.py, defaults = v2; run with --test-week nov03.

## Development numbers (Oct 27 week, not a test)
Leave-one-week-out baseline rate for the v2 rule: 27 of 11,950 sub-hours (0.23%, 2.3x nominal; some are likely real
events). Oct 27 week under v2: 2 alarms (LivestreamFail Nov 1 22:00 UTC, 40 outsider accounts vs 16.8 expected, 88%
Destiny homes, 95% in one thread; neoliberal Nov 1 18:00 UTC, 22 vs 6.7, 51% Destiny homes, 53% in one thread).
Comment-only flags were mostly 1-3 accounts in long arguments (e.g. 22 comments from one account).

## Predictions for Nov 3-9
1. **Count.** 2-8 v2 alarms across the 17 subs with comment data. Confidence: medium.
2. **Threads.** In at least half of the alarms, one thread carries over half of the outsider accounts. Confidence:
   medium.
3. **Source.** Destiny is the top home sub in at least half of the alarms. Confidence: medium-low (one dev week).
4. **Arguments vs brigades.** Comment-only "argument" flags outnumber v2 alarms at least 3 to 1. Confidence: medium.
5. **People.** Bot Bouncer-listed accounts make up no larger a share of outsider accounts in alarm hours than in normal
   hours. Confidence: medium-high.
6. **Real brigades.** A blind read of the top thread in each alarm hour against an equal number of random busy-hour
   threads from the same subs (reader not told which is which) finds a cross-sub link, crosspost or "came from r/..."
   mention in most alarm threads and in under a third of random ones. Confidence: medium.

## Scoring
In brigade-alarm-v2-results.md, hit / miss / partial with numbers. Misses stay in.
