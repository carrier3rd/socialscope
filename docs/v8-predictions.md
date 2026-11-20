# v8 bot model: design and predictions

Written Nov 20, 2026, 12:45 AM ET, before any young-control account is chosen or pulled and before any v8 model is
built. Never edit; addenda go at the end. Results go in `v8-results.md`.

## Why

Two problems with v7.1 (the frozen model behind the Lookup page), both seen in data already read, so they shape the
design but are not tests:

1. **Young and light accounts get flagged.** In the repull test, the ordinary accounts v7.1 wrongly flags at the
   strict line are young (median 317 days) and light (median 216 items), while unflagged ones are old (5.9 years,
   1,013 items). The "new subreddits" signal (share of the last 30 days spent in subreddits the account never used
   before) was built to catch taken-over accounts, but an account with little earlier history has nearly everything
   "new". The Nov 10-16 review candidate fits too: a 2019 account, almost silent until 2024, with personal posts, that
   the owner and Claude judged human.
2. **Aged bots get missed.** In the Nov 10-16 bot check (`nov10-botcheck-results.md`), v7.1 flagged 21% of known
   bots at the strict line, against 60% in the repull test. Those bots were old accounts (median about 7.5 years)
   with long histories, the profile of hijacked or bought accounts. v7.1's window features already compare the last
   30 days with the earlier history, but its whole-history features (account-level flags and tiers) read all of it.

## Design (frozen)

**Data.**
- The repull data and its frozen train/test split, unchanged.
- **New young and light controls:** 1,000 accounts drawn at random (seed 7) from the authors of the 18 panel subs in
  the Oct 27 and Nov 3 weekly pulls whose Reddit account ID is among the newest 25% of those authors' IDs (IDs are
  issued in order, and the pull records carry no creation date), with no Bot Bouncer listing of any kind. Not from
  the Nov 10-16 week, which has been read. Histories pulled from Arctic Shift with the usual cap (newest 1,000 posts
  and 1,000 comments). After the pull, an account counts as **young/light** if its oldest item is under a year old
  or it has fewer than 300 items; the rest count with the other controls. Split 70/30 into train and test (seed 7);
  the test part is never used while building.

**Model changes (only these three).**
1. **Conditioned "new subreddits".** The share is computed only when the history before the 30-day window has at
   least 100 items spanning at least 180 days; otherwise it is set to missing, with a separate yes/no feature saying
   so.
2. **Bot-period features.** When the takeover check used for the review packets
   (`scripts/botfinds/build_packets.py`, `takeover()`: 50+ earlier items and more than half the last 30 days in
   never-used subreddits) finds a break, the account-level text and solicitation features are also computed on the
   items from the break on, as extra features. Without a break those features are missing.
3. **Training adds the young-control training part** as ordinary accounts.

Same learner and settings as v7.1. Flag lines set as before, as the 1%, 2% and 5% points of the training controls'
scores.

**Evaluation**, on the frozen repull test split plus the young-control test part, v7.1 and v8 on the same accounts:
- wrong-flag rate at the strict line, separately for young/light controls and for the other controls;
- known-bot recall at the strict line overall, and separately for aged (account a year or older) and young bots;
- the same with the solicitation gate (strict line plus a solicitation sign).

**Bar for shipping v8 to the Lookup page** (all must hold; the recall limit is the 10 points proposed on Nov 19):
- wrong flags on young/light controls at the strict line cut by at least half;
- overall known-bot recall at the strict line no more than 10 points below v7.1's;
- aged-bot recall at the strict line not below v7.1's;
- the browser and laptop give identical scores (the existing parity check).

If the bar fails, v7.1 stays live and the results say why. The next weekly bot check (Nov 17-23) is the first
fresh test of whichever model is live; Nov 10-16 is not reused as a test.

## Predictions

| # | Prediction | Confidence |
|---|---|---|
| 1 | v7.1 wrongly flags 4-12% of the young/light test controls at the strict line. | medium |
| 2 | v8 cuts that rate by at least half. | 60% |
| 3 | v8's overall known-bot recall at the strict line is within 10 points of v7.1's. | 70% |
| 4 | v8's aged-bot recall at the strict line is at least 5 points above v7.1's. | 40% |
| 5 | v8's wrong-flag rate on the other (older) test controls stays at 0.5-2%. | medium |
| 6 | At least 20% of known bots in the test split have a takeover break by the packet rule. | medium |
| 7 | v8 passes the whole shipping bar. | 40% |

## Scoring

Each prediction is a hit or a miss; rates get 95% Wilson intervals; misses are reported. Usernames stay private.

## Addendum, Nov 20 2026, before the young-control sample is drawn

- The young-control histories are pulled with an end date of Nov 10, 2026 (Eastern, exclusive), so they hold
  nothing from the Nov 10-16 week that has already been read. Accounts in the Nov 10-16 bot check are excluded from
  the draw. Selection script: `scripts/v8_young_controls.py`.
