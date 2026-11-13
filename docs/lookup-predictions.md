# Account lookup: predictions

Written Nov 13, 2026, before any history for the account below was pulled or scored. Never edited after the run;
additions go at the end as dated addenda. Results go in `docs/lookup-results.md`.

## What the lookup is

`scripts/lookup.py <username>` pulls one account's Reddit history from Arctic Shift (same cap as the re-pull: newest
1,000 posts and 1,000 comments, plus the oldest-item check), cuts it at its last item, and computes:

1. **The v7.1 score.** Same features as `scripts/repull_run/feats.py`, scored by the frozen full model
   (`repull/out/model_repull.pkl`). Read against the thresholds from `results_repull.md`: 0.4828 (1% target, strict),
   0.2525 (2%), 0.0632 (5%). No retraining, no new rules.
2. **Descriptive signals, not part of the score.** These are shown on the card for a person to weigh. They do not
   change the score and are not inputs to v7.1:
   - Default-name pattern (`signals.DEFAULT_NAME`).
   - Day-night rhythm and a time-zone estimate (method frozen below).
   - Local subreddits, language, top subreddits, top keywords.
   - Location mismatch (defined below).

## Time-zone method (frozen)

- Use the UTC hour of every item in the pulled history. Below 100 items, report "too few items" and give no estimate.
- **Quiet window:** the 6 consecutive hours, wrapping past midnight, with the fewest items. The quiet share is that
  window's share of all items.
- **No clear rhythm:** a quiet share above 12% means there is no clear rest period, so no time-zone estimate is
  made. That itself is a signal: posting round the clock fits a shared or automated account.
- **Offset:** assume the quiet window is local 01:00-07:00, centered on 04:00 local. Offset = 4 − (window center in
  UTC), wrapped into −11..+12. The estimate is a band, offset −1 to offset +1.
- **US-presenting:** at least 10% of items are in subreddits from the fixed US list in `scripts/lookup.py`. The
  list covers US cities and states plus US politics (for example r/nyc, r/texas, r/Conservative, r/democrats,
  r/politics, r/centrist, r/ezraklein, r/JoeRogan, r/PoliticalDiscussion).
- **Mismatch:** a US-presenting account whose whole band lies outside UTC−10 to UTC−3. This is a lead, never proof.
  Shift workers, people living abroad and scheduling tools all produce it.

## Predictions for acct_222078e054 (the account the user asked about)

I have seen a third-party tool's card for this account, which reads "Pretty sure: human". These predictions are
informed by that card, so this run isn't a blind test of either tool.

| # | Prediction | Confidence |
|---|---|---|
| 1 | v7.1 full score below 0.0632, so not flagged even at the loosest (5%) line | 85% |
| 2 | solicit_handle and solicit_broad are both off | 95% |
| 3 | Default-name pattern matches | 95% |
| 4 | Clear rhythm: quiet share at or below 5% | 80% |
| 5 | The offset band overlaps UTC−6 to UTC−4 | 80% |
| 6 | US-presenting yes, mismatch no | 80% |
| 7 | r/centrist and r/ezraklein are both in the top 3 subreddits | 75% |

A miss on 1 would not by itself mean the account is a bot: at the 5% line, about 7 in 100 ordinary accounts are
flagged (test FPR 7.5%).
