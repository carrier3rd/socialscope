# Account lookup: results

Predictions: `docs/lookup-predictions.md` (commit 925f8a7, written before the pull). Script: `scripts/lookup.py`.

## acct_222078e054 (Nov 13, 2026)

This is the account the user asked about. It was pulled Nov 13 at 21:22 UTC with the re-pull cap (1,000 per kind). The
pull got 1,002 items: 2 posts and 1,000 comments, so the comment history was cut at the cap. The account is 1.2 years
old. Scored twice from the same pull and got the same numbers both times (RAM-fault check).

| # | Prediction | Result | Hit? |
|---|---|---|---|
| 1 | v7.1 score below 0.0632 | 0.0004 | hit |
| 2 | solicit_handle and solicit_broad off | both off | hit |
| 3 | Default-name pattern matches | matches (v7.1 rule flag `stock_name`, the only flag) | hit |
| 4 | Quiet share at or below 5% | 0.9% (quietest hours 06:00-12:00 UTC) | hit |
| 5 | Offset band overlaps UTC−6 to UTC−4 | UTC−6 to UTC−4 | hit |
| 6 | US-presenting yes, mismatch no | 92% of items in US subs, no mismatch | hit |
| 7 | r/centrist and r/ezraklein in the top 3 | r/centrist 35%, r/ezraklein 26%, r/Askpolitics 14% | hit |

7 of 7. These predictions were informed by the third-party card, so this agreement shows that the lookup reproduces
that tool's reading. It is not an independent test of either tool.

Where the score sits: 0.0004 is higher than 44% of the 478 test controls. Most ordinary accounts score near zero, so
this is an unremarkable score. It is about 1/1000 of the strict line (0.4828).

Fix during the build: the first card placed the meter dot by control percentile. That put this account mid-bar,
which read as "uncertain". The meter now uses a log scale with the 5%, 2% and strict lines marked. The keyword list
also split curly apostrophes ("don’t" became "don"); fixed. Neither change touches the score.

Not built: an interactions view. It would list other users' names, so it is left out.

## Shared core, site Lookup tab and parity checks (Nov 13, 2026)

The scoring and signals moved into `socialscope/lookup_core.py`, which both `scripts/lookup.py` and the site's Lookup
tab (Pyodide in the visitor's browser) run.

| Check | Result |
|---|---|
| Exported trees vs sklearn `predict_proba`, all 3,264 study accounts (`scripts/export_lookup_model.py`) | identical (largest difference 0) |
| `lookup_core.features` vs the re-pull pipeline, 400 random study accounts at their pipeline anchors (`scripts/lookup_parity.py`) | every feature identical; scores within 5e-7, which is the 6-decimal rounding in `accounts_repull.csv` |
| acct_222078e054, laptop (shared core) vs the first lookup | same score, 0.000354 |
| acct_222078e054, browser (live Arctic Shift + Pyodide) vs laptop | same 1,002 items, same score, rating 1.78 |

Rating added at the user's request: 1-10, piecewise in log10(score), with the 5% line at 5, the 2% line at 7 and the
strict line at 9. It's shown to two decimals, truncated rather than rounded. acct_222078e054 rates **1.78 / 10**.

Bug caught in testing: a lookup submitted before lookup.js had loaded fell back to a normal form submit and put the
username in the page URL (local test server only). Fixed. The input has no `name`, the form blocks native submits,
and the button stays disabled until the script is ready.

## Reddit official API: built, then dropped (Nov 13, 2026)

Live account facts from Reddit's API (suspended or not, exact creation date, karma, items newer than the archive)
were built for the laptop card and as an optional "Sign in with Reddit" on the site. They were tested only on mock
answers. When the user tried to register the app, Reddit refused: its Responsible Builder Policy requires approval
before any API use. The user chose to stay on Arctic Shift only, so the code was removed the same day. It never made
a real request. The score was never affected, because it always came from Arctic Shift data.

## Laptop re-pull bug, and a fresh read of acct_222078e054 (Nov 14, 2026, 01:51-02:00 UTC)

Testing the site after the Reddit removal, the browser rated acct_222078e054 **1.03**, not 1.78. A laptop re-pull
gave 1.78 again, but it hadn't really re-pulled. `arctic.pull_user_histories` resumes from the `_parts/*.done`
files of an earlier pull, so `scripts/lookup.py` kept reusing the first pull of an account. Fixed: a lookup without
`--no-pull` now clears the old pull first. The first pull is kept, unchanged, in the private folder
`acct_222078e054_pull_nov13_1517`.

| | Pull ending | Score | Rating | Above controls |
|---|---|---|---|---|
| First pull (results above) | Nov 13 15:17 UTC | 0.000354 | 1.78 | 44% |
| Fresh laptop pull, scored twice | Nov 13 22:28 UTC | 0.000107 | 1.03 | 15% |
| Site, live, run twice | Nov 13 22:28 UTC | 0.0001 | 1.03 | 15% |

About 7 hours of new comments moved the 1,000-comment window, and that lowered the score. Both reads are far below
every flag line, so the 7 predictions above still hold as scored. The laptop and the site agree on the same data.
