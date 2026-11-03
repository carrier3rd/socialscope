# Forward test of the in-sub classifier: design and predictions (written Nov 2, 2026, 9:40 AM ET)

Model: gradient boosting from docs/insub-training-predictions.md, frozen at Nov 2 with model file sha256 prefix
a1978ad38af51414. Thresholds: the 1% and 5% false-alarm points on the in-sub test controls. Hijack rules unchanged.

Cohort: 2,000 random accounts active in our 18 subs Oct 27 - Nov 1. None had a Bot Bouncer listing through Nov 2, and
none were used in any earlier round (seed 20261102). Full histories get pulled now. Each account is scored at its last
activity on or before Nov 2, and every score is written down before any outcome is known.

Outcome: a Bot Bouncer listing ("banned") between Nov 3 and Nov 30, 2026, from a Bot Bouncer posts pull run after
Nov 30. Scheduled check: Dec 1.

Predictions:
1. 0.5-3% of the cohort (10-60 accounts) is banned by Nov 30.
2. Accounts above the 1% threshold are banned at 10x or more the rate of accounts below it.
3. Of the accounts that do get banned, 35-65% were above the 5% threshold on Nov 2.
4. The model flags 1-3% of the cohort at the 1% threshold. That is higher than 1%, because some flagged accounts are
   bots Bot Bouncer hasn't reached yet.
5. Among flagged accounts that are not banned by Nov 30, a hand check finds at least a third look like hijacked
   solicitation accounts. That would mean Bot Bouncer's coverage lags, not that the model is wrong.

## Scores frozen (Nov 3, 2026, 7:50 AM ET, before any outcome)
Histories pulled for 2,000 of 2,000 accounts (finished Nov 2, 11:33 PM). Scored with scripts/insub_run/score_fwd.py on
items before the Nov 3 00:00 ET cutoff, model sha prefix a1978ad38af51414 (checked).
- Flagged at the 1% threshold: 22 (1.1%). Prediction 4 (1-3%) **held**.
- Flagged at the 5% threshold: 108 (5.4%).
- scores_frozen.csv sha256: 7e21ced8ccab9e8f2c5f745f4732e03011af4566571f8f109e6c185a1d68aa85
The file stays private (account hashes only, kept off the repo). Any later change to it breaks this hash.
