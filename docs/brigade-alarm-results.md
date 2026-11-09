# Brigade alarm: results (run Nov 5, 2026; predictions in brigade-alarm-predictions.md, unchanged)

## Lead

The alarm works as a statistical object and fails as a brigade detector in its pre-registered form. Plain Poisson
fires on 3.5% of normal hours (35x its nominal 0.1%); a negative binomial cuts that to 0.86% (still 8.6x). Applied to
the Oct 27 - Nov 1 test week it raised 22 alarm-hours in 12 subs, but the biggest ones (Destiny, neoliberal, Hasan,
Nov 1 18:00-21:00 UTC) sit on 3-4x surges in each sub's total volume, and alarm hours are no more thread-concentrated
than normal hours. Two post-hoc variants fix much of this and are reported as sensitivity, not as results: (a) model
the outsider count against the sub's total comments that hour (false alarms fall to 6x nominal and the volume-surge
alarms vanish), and (b) define home communities on baseline weeks only (the pre-registered "all weeks" rule assigns
heavy test-week brigaders to the sub they brigaded, hiding the clearest event in the data: r/atrioc, Oct 29 18:00 UTC,
34 outsider comments vs 1.5 expected, 71% from LivestreamFail homes, 91% in one thread).

Scorecard: 3 hits, 1 partial, 2 misses.

## Scorecard (primary = pre-registered: homes from all weeks, hourly-level model, NB threshold)

| # | Prediction | Result | Score |
|---|---|---|---|
| 1 | Plain Poisson fails; dispersion well above 1, likely 5+ in big subs; NB needed | Poisson false-alarm rate 3.53% of baseline hours (leave-one-week-out), 35x nominal. Comment-count dispersion phi > 1 in 18/18 subs (min 1.22), 5+ in 3 (h3h3 22.1, LivestreamFail 19.3, atrioc 9.6); Destiny 3.1, neoliberal 2.3, PCM 2.3. NB cuts false alarms 4x but is still 8.6x nominal | **Hit** (the "5+ in big subs" detail only for 2 of the 5 largest subs) |
| 2 | Counting accounts cuts dispersion but stays above 1 | Account-count phi lower than comment phi in 18/18 subs (e.g. h3h3 22.1 -> 12.9, LSF 19.3 -> 11.4, Destiny 3.1 -> 1.6); above 1 in 15/18 (Asmongold barely, 1.08); under 1 in Conservative 0.88, IsraelPalestine 0.96, Tankie 0.98 (all low-volume, ~0.6-1.3 outsider comments/hr) | **Hit** |
| 3 | Most alarm-hours in h3h3productions, LeftoversH3, neoliberal; Destiny the top home sub of outsiders there | 5 of 22 alarm-hours in those three (h3h3 0, LeftoversH3 1, neoliberal 4); 5 of 13 among alarms with 10+ outsider comments. Destiny was the top home in all 4 neoliberal alarms (41-75%) but not in LeftoversH3 (h3h3 36%, Hasan 34%) | **Miss** on location, partial on Destiny |
| 4 | thedavidpakmanshow stays quiet despite the highest outsider share | Highest baseline outsider share of any sub (21.7%); 1 alarm-hour out of 141 covered (Nov 1 20:00 UTC, 24 vs 1.9 expected, 83% Destiny homes) | **Hit** |
| 5 | In most alarm-hours one thread carries over half the outsider activity, vs well under half in normal hours | 9 of 22 alarm-hours over half, but 8 of those 9 are 2-9 comment hours. Among the 13 alarm-hours with 10+ outsider comments: 1 of 13 over half, mean biggest-thread share 0.38, vs 0.32 (14% over half) in normal hours with 10+ outsider comments | **Miss** |
| 6 | Bot Bouncer-listed accounts under 5% of outsider accounts in alarm-hours, no higher than normal hours | 0 of 277 outsider accounts in alarm-hours are on any ban list (500,286 listed accounts); 6 of 4,518 (0.13%) in normal hours | **Hit** |

## Data used

- Baseline weeks (all before Oct 27): aug18 (18 subs, full), aug25 (18 subs; 14 are partial pulls truncated 0.5-4.5
  days in, neoliberal has 12 hours), sep08 (full), sep22 (full), oct13 (13 subs: no atrioc, Destiny, h3h3, Hasan,
  LSF), oct20 (5 subs: atrioc, Destiny, h3h3, Hasan, LSF). Partial files are counted only over their covered hours.
- Test week: oct27, 17 subs (thebulwark comments failed), covered Oct 27 04:00 to Nov 2 ~02:00 UTC (141 hours/sub).
- 1,647,509 comments kept. Excluded: 75,657 [deleted]/[removed], 18,821 AutoModerator, 7,165 names ending in "bot".
- Home communities: 175,584 accounts; 48,711 (27.7%) get a home. 72.2% of accounts have under 5 comments; only
  0.04% have 5+ but no sub at 40%, so the 40% rule barely bites. No-home accounts write 12.9% of comments.
- Bot Bouncer: 500,286 accounts flaired "banned" across the three pulls (Jul 1 - Nov 2).
- Usernames were hashed (sha256, random per-run salt) on load and never written anywhere.

## Model

For each sub and measure (outsider comments; distinct outsider accounts), hourly expectation
mu = level[sub, week] x profile[sub, hour-of-day x weekday/weekend], fit by iterative proportional fitting on the
baseline weeks; the week level is the week's own mean, so a sub-wide surge is absorbed and only within-week shape
is tested. Dispersion phi = sum (y - mu)^2 / sum mu. NB extra variance alpha (var = mu + alpha mu^2) by moments.
Alarm when y exceeds the 99.9th percentile. False-alarm rate by leave-one-week-out over the 6 baseline weeks.

## Dispersion (baseline weeks, hourly outsider counts)

| Sub | Outsider share | Comments: mean/hr | phi | alpha | Accounts: mean/hr | phi | alpha |
|---|---|---|---|---|---|---|---|
| Asmongold | 5.5% | 2.3 | 1.49 | 0.18 | 2.0 | 1.08 | 0.03 |
| atrioc | 17.6% | 1.1 | 9.63 | 3.99 | 0.9 | 4.70 | 2.70 |
| Conservative | 2.3% | 0.7 | 1.22 | 0.26 | 0.6 | 0.88 | 0.00 |
| Destiny | 4.8% | 10.2 | 3.13 | 0.18 | 7.8 | 1.62 | 0.07 |
| dsa | 8.1% | 1.8 | 3.42 | 0.96 | 1.3 | 1.53 | 0.30 |
| h3h3productions | 2.0% | 6.0 | 22.12 | 0.93 | 4.0 | 12.88 | 0.83 |
| Hasan_Piker | 11.5% | 6.4 | 3.38 | 0.31 | 5.1 | 1.92 | 0.16 |
| IsraelPalestine | 2.3% | 1.4 | 2.67 | 0.79 | 0.9 | 0.96 | 0.00 |
| LeftoversH3 | 3.5% | 2.0 | 2.47 | 0.62 | 1.6 | 1.43 | 0.23 |
| LivestreamFail | 9.7% | 21.1 | 19.25 | 0.59 | 15.4 | 11.41 | 0.47 |
| neoliberal | 0.9% | 4.0 | 2.29 | 0.25 | 3.0 | 1.27 | 0.07 |
| Palestine | 7.8% | 1.6 | 1.82 | 0.42 | 1.4 | 1.32 | 0.19 |
| PoliticalCompassMemes | 1.8% | 3.3 | 2.34 | 0.31 | 2.3 | 1.21 | 0.07 |
| samharris | 10.3% | 1.4 | 3.10 | 1.00 | 1.0 | 1.69 | 0.48 |
| TankieTheDeprogram | 5.6% | 1.6 | 1.38 | 0.21 | 1.3 | 0.98 | 0.00 |
| thebulwark | 7.9% | 4.5 | 3.89 | 0.50 | 3.2 | 1.71 | 0.18 |
| thedavidpakmanshow | 21.7% | 3.7 | 4.83 | 0.73 | 2.5 | 2.12 | 0.35 |
| ukraine | 2.4% | 1.2 | 1.56 | 0.34 | 1.1 | 1.18 | 0.13 |

## False-alarm rates (leave-one-week-out on baseline weeks, 13,416 sub-hours; nominal 0.10%)

| Measure | Poisson | NB |
|---|---|---|
| Outsider comments | 3.53% (474 alarms, 35x nominal) | 0.86% (115, 8.6x) |
| Outsider accounts | 1.88% (252, 19x) | 0.66% (88, 6.6x) |

Per sub the NB comment rate runs 0.36% (Palestine) to 1.78% (h3h3); Poisson reaches 13.6% in LivestreamFail and 8.4%
in h3h3. Sensitivity, exposure = total comments that hour: Poisson 1.68% / 0.46%, NB 0.60% / 0.34%.

## Test week alarms (NB, pre-registered model; 22 hours of 2,396; Poisson would give 119 and 61)

| Sub | Hour (UTC) | Trigger | Outsider comments obs/exp (NB thr) | Accounts obs/exp | Total comments | Top home subs | Biggest thread | Share | Threads | BB |
|---|---|---|---|---|---|---|---|---|---|---|
| Asmongold | Nov 1 16:00 | accounts | 10 / 2.2 (10) | 9 / 1.5 | 56 | Conservative 40%, PCM 30%, LSF 20% | t3_1xl57ts | 0.40 | 6 | 0/9 |
| Conservative | Oct 31 08:00 | both | 3 / 0.0 (0) | 1 / 0.0 | 7 | PCM 100% | t3_1xjjc36 | 0.33 | 3 | 0/1 |
| Destiny | Nov 1 18:00 | comments | 44 / 10.8 (35) | 19 / 7.5 | 892 | LSF 27%, pakman 18%, IsraelPalestine 16% | t3_1xl95se | 0.32 | 11 | 0/19 |
| Destiny | Nov 1 19:00 | both | 55 / 11.6 (38) | 30 / 9.5 | 731 | LSF 42%, PCM 15%, dsa 11% | t3_1xl95se | 0.22 | 23 | 0/30 |
| Destiny | Nov 1 20:00 | both | 49 / 9.1 (31) | 30 / 8.1 | 545 | dsa 22%, LSF 20%, samharris 14% | t3_1xl92bz | 0.18 | 19 | 0/30 |
| Hasan_Piker | Oct 30 08:00 | comments | 22 / 4.9 (21) | 1 / 3.5 | 30 | LeftoversH3 100% | t3_1xibcg4 | 0.32 | 7 | 0/1 |
| Hasan_Piker | Nov 1 17:00 | accounts | 34 / 10.9 (43) | 27 / 7.2 | 243 | LeftoversH3 50%, thebulwark 12%, dsa 9% | t3_1xl96gg | 0.53 | 5 | 0/27 |
| Hasan_Piker | Nov 1 18:00 | accounts | 29 / 8.1 (33) | 24 / 6.0 | 302 | LeftoversH3 62%, LSF 14%, Destiny 7% | t3_1xl96gg | 0.41 | 9 | 0/24 |
| IsraelPalestine | Oct 27 09:00 | comments | 6 / 0.3 (4) | 1 / 0.3 | 46 | PCM 100% | t3_1xfvg4d | 1.00 | 1 | 0/1 |
| IsraelPalestine | Oct 29 04:00 | comments | 7 / 0.4 (5) | 3 / 0.2 | 76 | PCM 71%, dsa 14%, Destiny 14% | t3_1xi9uqt | 0.86 | 2 | 0/3 |
| LeftoversH3 | Oct 28 00:00 | both | 64 / 8.7 (49) | 40 / 7.8 | 833 | h3h3 36%, Hasan 34%, LSF 22% | t3_1xh8cct | 0.45 | 22 | 0/40 |
| TankieTheDeprogram | Nov 1 09:00 | comments | 4 / 0.2 (3) | 3 / 0.2 | 18 | Palestine 75%, LeftoversH3 25% | t3_1xkxngh | 1.00 | 1 | 0/3 |
| dsa | Oct 30 12:00 | both | 5 / 0.3 (4) | 4 / 0.3 | 9 | Hasan 100% | t3_1xizp9p | 0.80 | 2 | 0/4 |
| dsa | Nov 1 15:00 | both | 9 / 0.8 (8) | 6 / 0.5 | 28 | Hasan 33%, atrioc 33%, thebulwark 22% | t3_1xl4swh | 0.67 | 4 | 0/6 |
| neoliberal | Nov 1 18:00 | both | 41 / 2.7 (12) | 23 / 2.1 | 1571 | Destiny 56%, IsraelPalestine 10%, samharris 7% | t3_1xkwhvl | 0.39 | 5 | 0/23 |
| neoliberal | Nov 1 19:00 | both | 29 / 2.7 (12) | 16 / 1.8 | 1441 | Destiny 41%, PCM 17%, h3h3 14% | t3_1xla98t | 0.45 | 7 | 0/16 |
| neoliberal | Nov 1 20:00 | accounts | 15 / 3.6 (16) | 12 / 2.7 | 1057 | Destiny 47%, thebulwark 20%, PCM 13% | t3_1xla98t | 0.47 | 3 | 0/12 |
| neoliberal | Nov 1 21:00 | comments | 12 / 2.3 (11) | 6 / 1.9 | 790 | Destiny 75%, h3h3 25% | t3_1xla98t | 0.50 | 3 | 0/6 |
| samharris | Oct 28 11:00 | both | 5 / 0.3 (4) | 5 / 0.3 | 44 | ukraine, neoliberal, h3h3 20% each | t3_1xhkfbi | 0.60 | 2 | 0/5 |
| thedavidpakmanshow | Nov 1 20:00 | both | 24 / 1.9 (14) | 13 / 1.9 | 100 | Destiny 83%, thebulwark 8%, samharris 4% | t3_1xlagti | 0.29 | 10 | 0/13 |
| ukraine | Oct 29 11:00 | comments | 8 / 0.6 (5) | 3 / 0.5 | 90 | neoliberal 75%, Destiny 25% | t3_1xifpjk | 0.88 | 2 | 0/3 |
| ukraine | Nov 1 07:00 | both | 2 / 0.0 (0) | 1 / 0.0 | 26 | Destiny 100% | t3_1xkwfy8 | 1.00 | 1 | 0/1 |

Reading it: 9 of the 22 are hours with 2-9 outsider comments where the expected count is near zero (the 99.9th
percentile of a Poisson with mean 0.03 is 0, so a single comment alarms). The 13 material alarms (10+ comments)
form three clusters: a Sunday-afternoon surge on Nov 1 (Destiny x3, Hasan x2, neoliberal x4, pakman, Asmongold) in which
total comment volume was 3-4x normal in Destiny and neoliberal, so the outsiders rose with everyone else; the
LeftoversH3 hour on Oct 28 00:00 UTC (64 outsider comments across 22 threads, split between h3h3 and Hasan homes);
and r/Hasan_Piker on Oct 30 08:00 UTC, which is one LeftoversH3-home account posting 22 comments.

## Sensitivity variants (post hoc; not scored)

| Variant | NB false alarms (comments / accounts) | Test alarm-hours | Where the material ones land |
|---|---|---|---|
| Pre-registered (homes all weeks, hourly level) | 0.86% / 0.66% | 22 (13 material) | Destiny 3, Hasan 3, neoliberal 4, LeftoversH3 1, pakman 1, Asmongold 1 |
| Homes from baseline weeks only | 0.81% / 0.60% | 32 (23) | adds atrioc Oct 29 18:00 (34 vs 1.5, LSF 71%, one thread 91%), LeftoversH3 Oct 31 09:00 (46 vs 7, LSF 52%), Hasan Oct 30 07:00, ukraine Oct 30-31 (one PCM account) |
| Exposure = total comments that hour | 0.60% / 0.34% | 16 (10) | LivestreamFail Nov 1 22:00 (53 vs 21, 42 accounts, Destiny homes 81%, one thread 92%), h3h3 Oct 30-31 x2 (LeftoversH3 homes 67-83%), LeftoversH3 Oct 28 19:00 (Hasan 71%), PCM Oct 30 19:00 (LSF 65%), neoliberal Nov 1 18-19 only; the Destiny/Hasan/pakman Nov 1 alarms disappear |
| Both | 0.58% / 0.29% | 21 (16) | h3h3 x4, atrioc x2, LSF Nov 1 22:00, LeftoversH3 Oct 31 09:00, Palestine Oct 28 02:00 (IsraelPalestine 75%, 92% one thread); 8 of 16 material alarms have one thread over half |

In the "both" variant prediction 5 would have held (8 of 16 material alarm-hours over half vs 14% of normal hours)
and prediction 3's h3h3 half would have held; this is reported for the next pre-registration, not as a score.

## Limitations

- Home community from all weeks (pre-registered) includes the test week, so an account that makes 5+ comments in a
  sub while brigading it is counted as a local. Fixing homes on baseline weeks only is the right rule next time, at the
  cost of losing accounts first seen in the test week (12.9% of comments have no home as it is; 72% of accounts have
  under 5 comments in these pulls).
- The hourly-level model tests within-week shape only; it cannot tell an outsider surge from a sub-wide surge. Model
  the outsider count against total comments in the hour (or test the outsider share directly) to separate them.
- Per-hour expectations under 0.5 make the 99.9th percentile degenerate; a minimum-count floor (10 outsider
  comments) or a longer window for small subs should be part of the rule.
- Deletion bias: older pulls have 5-14% of comments with [deleted] authors (excluded), the two freshest pulls under
  0.3%. Comments that get removed, which brigade comments disproportionately are, survive in the test week and are
  gone from the baseline, inflating test-week outsider counts relative to baseline.
- Partial weeks: aug25 is truncated in 14 subs; oct13 lacks the five streamer subs; oct20 has only those five. Each
  (sub, week) counts only over covered hours, but the 48-cell profile for the streamer subs rests on 4 full weeks plus
  oct20, and oct20 h3h3 (185k comments) and oct27 h3h3 (83k) are a drama surge against a 8-11k/week baseline.
- The test week ends around 02:00 UTC Nov 2 (pull ran Nov 1 evening ET), so Nov 2 is missing and the Nov 1 alarms
  were pulled 4-8 hours after posting; moderator removals had not yet happened.
- Hours are UTC; the weekday/weekend split uses UTC days, so Friday 20:00-24:00 ET falls on the UTC weekend. The
  audience is mostly US, so the daily cycle is modeled correctly but the weekend boundary is off by 4-5 hours.
- One account posting many comments inflates the comment measure (Hasan Oct 30 08:00, ukraine Oct 30-31 in the
  baseline-homes variant); the account measure is the safer primary alarm.
- The ban-list share is near zero everywhere (0.13% in normal hours), so prediction 6 is confirmed but the test has
  little power: Bot Bouncer lists bots that spam, not accounts that brigade.
- Only 6 baseline weeks and one test week; the leave-one-week-out rates have wide uncertainty (115 alarms over 13,416
  hours gives roughly 0.7-1.0% for the NB comment rate).

## Reproduction

Scripts (workspace): `scripts/load_week.py` (compacts a staged week to hashed npz, deletes raw files),
`scripts/load_bb.py` (hashes Bot Bouncer ban posts), `scripts/brigade_alarm.py` (everything else;
`--home-from {all,baseline}`, `--exposure {hours,total}`). Full per-hour output for each variant is in
`out/results_<home>_<exposure>.json`. No usernames appear in any output.
