# aged_drift: fresh test design and predictions (written Oct 30, 2026, 9:05 AM ET, before any test history is pulled)

Rule: `socialscope/aged.py`, frozen as committed with this file. Development numbers are in its docstring.

Test week: Sep 8–14, 2026, the 18 subs. Bots: accounts active that week that Bot Bouncer listed as banned from Sep 15
to Oct 28 (53 accounts; not known at the time of the week, so this tests prediction rather than lookup), reported
apart from the 17 listed Sep 1–14. Controls: 400 accounts drawn at random from all 49,978 active accounts, with no
screening exclusions (fixing the round 4 control-pool flaw). Full histories, up to 1,000 items. Check date: each
account's last pulled item, as in development. Intervals 95% Wilson.

Predictions:
1. About a quarter of the later-listed bots are aged (100+ items over a year or more): 10–20 of 53.
2. aged_drift fires for 20–35% of aged bots and 4–7% of aged controls. It fails the pass bar (5x and controls under
   5%), as it did in development.
3. Across all accounts (aged or not), aged_drift fires for under 3% of controls.
4. v7.1's primary tier catches 40–60% of the later-listed bots (mostly young accounts) and 3–5% of random controls,
   the first round where controls are truly random.
5. Combining primary OR aged_drift adds under 10 points of catch over primary alone.
