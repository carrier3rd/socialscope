# Bot check of the Nov 10-16 week: results

Scores `nov10-botcheck-predictions.md` (design and predictions committed Nov 19, 2026, 7:00 PM ET, before the
shortlist was built or any history pulled). Scored Nov 20, 2026, 12:20 AM ET with `scripts/nov10_botcheck_score.py`.
Aggregates only; usernames stay private.

**Score: 3 of 8 hit.** The strict line flagged only one in five known bots this week, far below the repull test,
so the gate sent just one new account to review.

## How it ran

- **Stage 1** (`screen.shortlist`, defaults): 6,671 of the week's accounts matched a rule; the 300 with the strongest
  signals were shortlisted (rules: new 171, ai_style 159, ai_lite 128, downvoted 40), plus 300 random controls and
  every known bot active that week (82).
- **Stage 2:** all 682 histories pulled from Arctic Shift (newest 1,000 posts and 1,000 comments each, ending Nov 16),
  5.5 hours. All 682 accounts had items and were scored.
- **Scoring** ran twice as a check against hardware errors; the two runs' outputs were byte-identical.

## Results

| Group | n | Strict line (1%) | Strict + solicitation (gate) | 2% line | 5% line |
|---|---|---|---|---|---|
| Known bots (listed before Nov 10) | 82 | 17 (20.7%, 13.4-30.7%) | 16 (19.5%, 12.4-29.4%) | 19 (23.2%) | 32 (39.0%) |
| Random controls | 300 | 8 (2.7%, 1.4-5.2%) | 3 (1.0%, 0.3-2.9%) | 10 (3.3%) | 20 (6.7%) |
| Shortlist | 300 | 18 (6.0%, 3.8-9.3%) | 1 (0.3%, 0.1-1.9%) | 34 (11.3%) | 81 (27.0%) |

Intervals are 95% Wilson. Week totals: 61,055 distinct authors (the shortlist step counted 61,024 with its own
author filter), 83 known bots active, 8 later bots (first listed Nov 10-16) active. None of the 8 later bots was in
the shortlist or the controls.

## Predictions

| # | Prediction | Result |
|---|---|---|
| 1 | 40,000-80,000 distinct authors | **Hit** (61,055) |
| 2 | 15-60 known bots active | **Miss** (83) |
| 3 | Under 15 later bots active | **Hit** (8) |
| 4 | v7.1 flags 45-75% of known bots at the strict line | **Miss** (20.7%) |
| 5 | v7.1 flags 0.3-3% of controls at the strict line | **Hit** (2.7%) |
| 6 | Gate: at most 1.5% of controls and 25-55% of known bots | **Miss** (controls 1.0% within; known bots 19.5% below) |
| 7 | Shortlist flagged at the strict line at least 3 times as often as controls | **Miss** (2.25 times) |
| 8 | 2-25 shortlisted, unlisted accounts pass the gate | **Miss** (1) |

## What went wrong (read after scoring, so a lead, not a finding)

The known bots this week look unlike the repull test's. They are old accounts: median age about 7.5 years, 77% older
than a year, with full histories (median 1,038 items). Those the strict line caught were even older (median about
8.5 years) than those it missed (about 6.4 years). An old account with a long history that now behaves as a bot is
most likely hijacked or bought, so most of the 1,000-item window the model reads is the original owner's. v7.1 scores
the whole window, so the bot period gets drowned out. If this holds, two changes follow, both needing new
predictions before use:

- score only the items after a takeover break (the takeover check in `socialscope/hijack.py` already finds the break);
- report recall separately for young and aged known bots, as the level 3 plan proposes.

The shortlist rules also add little at the strict line (2.25 times the control rate). Most shortlisted accounts are
young (median 80 days) with short histories, the group where v7.1 already gives false positives, and the gate's
solicitation signs removed nearly all of them.

## Review queue

One shortlisted account passed the gate and has no Bot Bouncer listing of any kind. It is in a private review
file for the owner to read. Nothing was submitted. Per the publishing rules, it is a lead only
and is not named anywhere.
