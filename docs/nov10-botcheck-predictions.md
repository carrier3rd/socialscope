# Bot check of the Nov 10-16 week: design and predictions

Written Nov 19, 2026, 7:00 PM ET, before the shortlist is built or any history is pulled. The week's pull was only
checked for completeness (file counts, duplicates, hourly gaps, deleted share); no account, flag or score was read.
Never edit; addenda go at the end. Results go in `nov10-botcheck-results.md`.

## Design (frozen)

- **Data:** all posts and comments in the 18 panel subs, Nov 10-16, 2026 (Eastern days), pulled Nov 19.
- **Known bots:** accounts with a Bot Bouncer "banned" listing created before Nov 10, from the r/BotBouncer pulls on
  the laptop (Jul 1 - Nov 16). **Later bots:** first listed Nov 10-16.
- **Stage 1:** `screen.shortlist` with its defaults (rules new, ai_style, ai_lite, downvoted; up to 300 shortlisted
  by rule strength; a random control group of the same size, seed 7), plus every known bot active that week.
- **Stage 2:** each account's history across Reddit, newest first, up to 1,000 posts and 1,000 comments, ending
  Nov 16 (pull end date Nov 17, Eastern, exclusive). Every account is scored at its last item in that pull.
- **Score:** the frozen v7.1 full model exactly as the public lookup runs it (`socialscope/lookup_core.py`,
  `site/public/lookup/model.json`), with its lines: strict 0.4828 (1% target), 2% line 0.2525, 5% line 0.0632.
- **Gate:** "strict + solicitation" = at or above the strict line and a solicitation sign (contact-handle template
  or a turn to NSFW or soliciting), as on the lookup page since Nov 19.
- **Review:** shortlisted accounts that Bot Bouncer has not listed and that pass the gate go to the existing
  review queue (`scripts/botfinds`, Path 1): two separate reads, and only the owner submits. Nothing is published
  unless Bot Bouncer bans the account.
- **Privacy:** usernames stay in `~/socialscope_data/nov10_botcheck/` (never committed). This repo gets aggregates
  and hashed ids only.

## Predictions

| # | Prediction | Confidence |
|---|---|---|
| 1 | The week holds 40,000-80,000 distinct authors. | medium |
| 2 | 15-60 known bots (listed before Nov 10) were active in the 18 subs that week. | medium |
| 3 | Under 15 later bots (first listed Nov 10-16) were active that week. | medium |
| 4 | v7.1 flags 45-75% of the known bots at the strict line (repull test: 60%). | medium |
| 5 | v7.1 flags 0.3-3% of the random controls at the strict line (repull test: 1.15%). | medium |
| 6 | Strict + solicitation flags at most 1.5% of controls (repull test: 0.44%) and 25-55% of known bots (repull: 41%). | medium |
| 7 | Shortlisted accounts are flagged at the strict line at least 3 times as often as controls. | medium-low |
| 8 | 2-25 shortlisted, unlisted accounts pass the gate and go to review. | medium |

## Scoring

Each prediction is a hit or a miss on these numbers, with 95% Wilson intervals for rates, misses included.
