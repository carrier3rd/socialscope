# Training set and hijack-rule test: design and predictions (written Nov 1, 2026, 5:00 PM ET, before any pull)

Sample (scripts/build_training_sample.py, seed 1101, cutoff Oct 1, 2026): up to 1,000 accounts Bot Bouncer banned
Jul 1-Oct 28 (latest verdict), every account it ruled organic in that span, and 1,000 random accounts active Oct 20-26
in the 18 subs. Every account used in any earlier round, test, audit or development set is excluded. Split by listing
date: train = listed before Oct 1, test = Oct 1 onward. Random accounts carry their last activity date. Full histories,
up to 1,000 items.

Frozen today, before the pull: `socialscope/hijack.py` (solicit_handle, solicit_broad).

Predictions, scored on the test split (October listings) and random accounts:
1. About 25-45% of banned accounts are aged (100+ items over a year or more).
2. solicit_handle fires for 40-65% of aged banned accounts, 15-35% of all banned accounts, under 2% of random and
   under 5% of organic-verdict accounts.
3. solicit_broad fires for 65-85% of aged banned accounts and 5-12% of random accounts.
4. The v7.1 primary tier (account age) catches 45-65% of banned accounts (mostly the young ones) and 3-5% of random.
5. primary OR solicit_handle catches 60-80% of banned accounts at under 7% of random.
