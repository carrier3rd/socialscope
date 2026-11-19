# socialscope findings as of Nov 19, 2026: results

Compiled Nov 19, 2026 from primary sources only: the repo's predictions and results files and git history (main at
`5e76825`), the private data folder on the laptop (`~/socialscope_data/`), the Google Drive `My Drive/reddit_pulls`
folder (file listing and the three `*_missing.txt` files only), and the cloned `../dgg-chat-site`. No new analysis was
run except counting: items inside every local pull zip, accounts per history batch, Wilson intervals on counts the docs
report, and first-seen subs in the existing talking-point cluster files. Every number cites its file. **MISSING** means
the number is not in any file I could open, with where I looked; it never means zero.

**About the commit hashes.** This repo's history was rewritten twice on Nov 19, 2026
(`docs/history-rewrite-2026-11-19.md`); every hash below is a current one. Commit dates were kept by the rewrite. DGG
files moved to `dgg-chat-site` the same day; their hashes are cited from this repo's history, where they were made.

## Lead

The one bot signal that has held on every honest test is account age: the v7.1 primary tier catches about a fifth to a
third of bots that Bot Bouncer bans later, at 3-7% of ordinary accounts. A gradient-boosting classifier trained on
in-sub bans does much better on the re-pulled, listing-date-anchored data: 62% recall (Wilson 55-69%) at 1.7% test
false alarms, AUC 0.931, with precision at an assumed 1% bot share of 27% (bootstrap 18-58%). It is driven by the hijack
signature (an established account turning to new subreddits and NSFW solicitation shortly before listing). Every
content, writing, timing-only and government-report rule failed or was too rare. The brigade alarm, claim check,
opinion bundles and talking-point work each ran once or twice and are preliminary. Several studies were committed in
the same commit as their results, or seconds before them, so git cannot confirm the predictions came first. These are
the Oct 26-29 bot rounds that landed in the repo's first commit (round 1, the Oct 6-12 version 2 test, stage 2, rounds
2-3), the claim check, the first two opinion-bundle runs, brigade v1 and election night. Round 4 and the bot-rich
results do show the predictions first. The forward test (Dec 1), Brigade Alarm v2 and the Bluesky window
(Nov 20-Dec 11) are still to run.

**Terms.** "v7.1" names two different things in the repo's files. This report keeps them apart:
- **v7.1 rule tier:** the account-age primary tier of `socialscope/history.py` (young_account, young_account_true,
  posts_only, tourist).
- **Re-pull classifier:** the gradient-boosting model `~/socialscope_data/repull/out/model_repull.pkl`, which the
  Lookup code calls the "frozen v7.1 full model".

## 1. Executive summary

Tags: **Confirmed** = scored against a prediction committed before its result in git, and reproduced or replicated on
fresh data. **Preliminary** = scored once, small n, or the commit order can't show the prediction came first.
**Planned** = designed or running, no result yet.

| Finding | Tag | Source |
|---|---|---|
| Account age (v7.1 primary tier) catches 21-33% of later-banned bots at 3-7% of random in-sub controls, across four fresh tests | Confirmed | `docs/bot-calibration-study.md` (aged_drift fresh test `8fa1f93`, checkpoint `d812f38`); `docs/insub-training-predictions.md` (`e5ad4fd`); `~/socialscope_data/repull/out/results_repull.md` |
| Re-pulled in-sub classifier: 62% recall (55-69%) at 1.7% test FPR, AUC 0.931 (0.908-0.952); precision at a 1% bot share 27% (bootstrap 18-58%) | Confirmed (predictions 1-6 committed `003d07e` Nov 9, scored `f5ebef3` Nov 10; reproduced byte for byte) | `docs/repull-results.md`; `results_repull.md` |
| The earlier headline (67% at 1%, AUC 0.97) was inflated by the 1,000-item history cap; like-for-like it is 57% after the fix | Confirmed | `docs/repull-results.md` |
| Hijack signature: solicit_broad fires for 74-75% of aged in-sub bans at 4-6% of controls; solicit_handle 54% at 2% | Confirmed (insub `f010a26` before `e5ad4fd`; repeated in the re-pull) | `docs/insub-training-predictions.md`; `results_repull.md` |
| The original behavioural detector caught 0 of 42 (Oct 20-26) and 0 of 34 (Oct 6-12) Bot Bouncer bots | Preliminary (predictions and results in the initial commit `a17cdd0`) | `docs/bot-calibration-study.md` |
| Content, writing, AI-style, karma-farm and government-report rules near zero on 398 Reddit-wide bans | Preliminary (one run; pre-registration `a17cdd0`, results `15b7f5a` 29 min later) | `docs/bot-calibration-study.md` |
| aged_drift fails as a monitor: 9% of bots before their ban vs 10% of random accounts flagged at least once | Confirmed (`4e0c09f` before `d812f38`); rule retired | `docs/bot-calibration-study.md` |
| Bot Bouncer's aged-account bans are mostly right: 83% show the hijack signature; label noise at most 17% for that group | Preliminary (one coder) | `docs/label-audit.md` (`17b16dc`) |
| Pending accounts at Oct 28 look bot-like: 16/30 vs 5/30 blind read (Fisher p = 0.0061); 10.3% flagged vs 1.7% of controls | Confirmed for the flagged share (`f5ebef3`); Fisher part committed 3 s after its prediction | `docs/repull-results.md` |
| Brigade alarm (v1): negative binomial still fires at 8.6x nominal; 22 alarm-hours in the Oct 27 week are **anomalous inflow**, none confirmed by cross-post account overlap | Preliminary (predictions `003d07e` and results `7a61ea7` 1 s apart) | `docs/brigade-alarm-results.md` |
| Claim check, Oct 13-19: 8 of 27 checked claims false or misleading; 19 asserts from 17 one-off accounts; 0 repeat spreaders | Preliminary (one week; initial commit) | `docs/claim-check-oct13-19.md` |
| Three political opinion pairs are structural, but their Oct 20-26 strength was inflated by the drama week | Preliminary | `docs/opinion-bundles.md` |
| Talking points: the v1 phrase method was void (22% real talking points); v2 embeddings reach 57% at cosine 0.80 and 71% at 0.85 (100 clusters) | Preliminary | `docs/talking-points-v2-predictions.md`, `docs/crossover-pooled-predictions.md` |
| No talking-point cluster reached 3+ subs within an hour (0 of 1,916) | Preliminary | `docs/talking-points-v2-predictions.md` |
| Forward test of the Nov 2 classifier on 2,000 accounts: 22 flagged (1.1%) at the 1% line; outcome Dec 1 | Planned (scores frozen `ecc58ed`) | `docs/forward-test-predictions.md` |
| Brigade alarm v2 test on Nov 3-9 | Planned: predictions committed `003d07e`, data pulled, never scored | `docs/brigade-alarm-v2-predictions.md` |
| Bluesky window Nov 20-Dec 11 | Planned: 24-hour pilot running; window dates not yet set | `docs/bluesky-politics-predictions.md`, `bluesky/config/targets.yaml` |

## 2. Data inventory

### 2.1 Subreddit week pulls on the laptop (Arctic Shift)

Counts are raw items inside each zip (`~/socialscope_data/reddit_pulls/<folder>/`), counted Nov 19 by reading every
line. They include `[deleted]`, AutoModerator and bot accounts, so they run higher than the filtered counts in the
study docs. All 318 zips passed a CRC check. Posts / comments:

| Folder | Window | Subs | Posts | Comments | Note |
|---|---|---|---|---|---|
| aug18 | Aug 18-24 | 18 | 6,605 | 285,253 | |
| aug25 | Aug 25-31 | 18 | 7,079 | 275,595 | 14 of 18 comment files truncated 0.5-4.5 days in (`docs/brigade-alarm-results.md`) |
| sep08 | Sep 8-14 | 18 | 7,472 | 294,388 | |
| sep22 | Sep 22-28 | 18 | 6,709 | 262,477 | |
| t1_oct13 | Oct 13-19 | 13 | 4,157 | 57,318 | tier 1 subs; comments only for some subs |
| tp_fill | Oct 13-19 | 5 | 0 | 104,809 | comments only, five streamer subs |
| tp_fill | Oct 20-26 | 13 | 0 | 220,570 | comments only, tier 1 subs |
| six_oct20 | Oct 20-26 | 5 | 18,006 | 299,524 | LSF, h3h3, Destiny, Hasan_Piker, atrioc |
| oct27 | Oct 27-Nov 2 | 18 | 14,080 | 416,389 | pull ran Nov 1 evening; Nov 2 mostly missing (`docs/brigade-alarm-results.md`) |
| h3fix_oct27 | Oct 27-Nov 2 | 1 | 0 | 95,537 | duplicate copy of the replacement h3h3 file already in `oct27` (same sha256); not additional data |
| nov03 | Nov 3-9 | 18 | 12,443 | 413,332 | |
| nov10 | Nov 10-16 | 5 so far | 3,063 | 48,932 | **in progress** at the time of counting (started Nov 19) |
| context | Aug 1-Nov 2 (4 files) | 6 | 63,547 | 734,026 | Fauxmoi, youtubedrama, DecodingTheGurus full; politics, worldnews, news posts only |

Per-sub counts for every window are in Appendix A.

**Not on the laptop:**
- The Oct 6-12 six-sub week (the version 2 fresh-week test and stage 2).
- The full Oct 13-19 six-sub week (round 2, claim check). Only comments for five subs are here, in `tp_fill`.
- Any h3snark file in any window.

A six-sub Oct 20-26 pull (`six_oct20`, the round 1 and round 3 week) is on the laptop. Whether it is the same pull those
rounds used is not recorded.

**h3h3 Oct 27 counted once:** `h3fix_oct27` holds a byte-identical copy (same sha256) of the replacement h3h3 comments
file that `oct27` also holds. The 416,389 `oct27` total counts it once, so don't add the `h3fix_oct27` row to it. Drive holds the Colab-era batches (below). The docs give the filtered size of the round 1 week: 294,475 posts
and comments from 61,500 accounts (`docs/bot-calibration-study.md`), and 98,790 comments for Oct 13-19
(`docs/claim-check-oct13-19.md`).

### 2.2 Bot Bouncer calibration pulls (r/BotBouncer posts)

| Folder | Window | Listing posts |
|---|---|---|
| bb_julaug | Jul 1-Aug 31 | 252,725 |
| bb_pre_oct20 | Sep 1-Oct 19 | 264,235 |
| bb_oct20_27 | Oct 20-27 | 40,410 |
| bb_nov | Oct 28-Nov 2 | 26,715 |
| bb_weekly | Oct 28-Nov 11 | 73,502 |
| bb_weekly | Nov 2-Nov 16 | 67,059 |

The first four combined: 569,112 distinct accounts, latest verdict banned 536,088, organic 218, pending 28,383, purged
2,007, unflaired 2,342, retired 31, service 30, inactive 13 (`~/socialscope_data/repull/out/groups_summary.md`).

### 2.3 User-history batches and the 1,000-item cap

Histories are capped at the newest 1,000 posts and the newest 1,000 comments per account. "At cap" = accounts with
1,000 or more items of that kind in the batch zip (counted Nov 19 from `reddit_pulls/histories/*.zip` and
`reddit_pulls/repull/*.zip`).

| Batch | Posts: accounts / at cap | Comments: accounts / at cap | Used for |
|---|---|---|---|
| round4 | 527 / 7 | 603 / 279 (46%) | round 4 |
| septest | 443 / 9 | 469 / 312 (67%) | aged_drift fresh test |
| augpanel | 960 / 16 | 1,032 / 702 (68%) | aged_drift checkpoint panel |
| train | 1,905 / 25 | 1,911 / 578 (30%) | sitewide training set |
| insub | 435 / 31 | 479 / 285 (60%) | in-sub rebuild |
| fwd | 1,863 / 32 | 1,993 / 1,067 (54%) | forward-test cohort |
| repull_test (listing-date anchored) | 908 / 19 | 1,038 / 530 (51%) | re-pull test side |
| repull train (`repull_<day>`) | 2,630 / 51 | 2,852 / 1,761 (62%) | re-pull train side |

Comments hit the cap far more than posts. Over half of the forward-test and re-pull accounts have truncated comment
histories, which is what the re-pull was designed around (`docs/repull-predictions.md`, prediction 4).

**On Drive only** (`My Drive/reddit_pulls`, listed Nov 19 through the Drive connector): `oct6_check`, `oct13_check`,
`oct20_check` and `botrich` histories (posts, comments and `_slim` zips, 5 MB-1.5 GB each), `oct6_check_overview.json`
and `users_to_pull_botrich.txt`. The zips are too large for the connector, so their item and cap counts are
**MISSING**. What the docs record: 616 of 617 histories (Oct 6-12 stage 2), 642 (round 2, Oct 13-19), 644 (round 3,
Oct 20-26) and 398 of 400 bots plus 200 controls (bot-rich), all "up to 1,000 items" (`docs/bot-calibration-study.md`).

### 2.4 Arctic Shift gaps (`*_missing.txt`)

Each file lists thread IDs whose context Arctic Shift did not return. Read from Drive, counts only:

| File | Missing threads |
|---|---|
| `oct13_check/oct13_check_missing.txt` | 445 |
| `oct20_check/oct20_check_missing.txt` | 319 |
| `botrich/botrich_missing.txt` | 186 |
| `oct6_check` | **MISSING**: no `_missing.txt` on Drive, the laptop or this PC |

For scale: thread context covered 263,971 threads (round 1 stage 2), 288,247 (round 2) and 92,610 (bot-rich)
(`docs/bot-calibration-study.md`).

## 3. Per-subreddit cross-sections

### 3.1 Bot density (Bot Bouncer-listed accounts active that week)

Wilson 95% intervals computed from the counts in the files. Bot Bouncer labels are positive-only, so these are
densities of listed accounts, not of all bots.

| Week and subs | Listed bots / active accounts | Density (95% CI) | Source |
|---|---|---|---|
| Oct 20-26, six streamer subs | 42 / 61,500 | 0.068% (0.051-0.092%) | `docs/bot-calibration-study.md` |
| Oct 6-12, six subs | 34 / 26,757 | 0.127% (0.091-0.178%) | same |
| Oct 20-26, 14 tier 1 subs (round 4) | 17 / 31,029 | 0.055% (0.034-0.088%) | same |
| Sep 8-14, 18 subs (banned Sep 1-Oct 28) | 70 / 49,978 | 0.140% (0.111-0.177%) | same; `docs/aged-drift-predictions.md` |
| Aug 18-24, 18 subs (banned Aug 25-Oct 28) | 58 / 50,424 | 0.115% (0.089-0.149%) | `docs/aged-drift-checkpoint-predictions.md` (32 used + 26 dropped for overlap) |

**By sub, Oct 20-26:** LivestreamFail 22, h3h3productions 11, atrioc 1, h3snark 0 (from the file). Destiny and
Hasan_Piker together: 8, by subtraction from 42 (the file says no bot posted in more than one sub); their split is
**MISSING**. **Round 4:** LeftoversH3 4, Asmongold 3,
PoliticalCompassMemes 3, thebulwark 2, neoliberal 2 (from the file); the remaining 3 by subtraction, subs not given. Right-leaning subs
7.5 per 10k active accounts (7 bots) vs 4.6 (10 bots), too few to tell apart. Per-sub active-account denominators,
and so per-sub Wilson intervals: **MISSING** (not in any doc; looked in `docs/bot-calibration-study.md` and
`docs/round4-predictions.md`).

h3snark: on break all of Oct 20-26 (only AutoModerator notices) and inactive since about Feb 2025
(`docs/opinion-bundles.md`, `docs/context-subs-results.md`). No h3snark file is on the laptop.

### 3.2 Brigade alarm events (anomalous inflow)

Pre-registered v1 (homes from all weeks, hourly-level model, negative binomial 99.9th percentile), Oct 27-Nov 2,
from `docs/brigade-alarm-results.md` (`7a61ea7`). None of these is confirmed as a brigade: the file gives the
outsiders' home subs but no cross-post link or account-overlap check tying them to a coordinating post, so all are
reported as **anomalous inflow**.

| Sub | Alarm-hours | Material (10+ outsider comments) | Read |
|---|---|---|---|
| neoliberal | 4 | 4 | Nov 1, 18:00-21:00 UTC; Destiny homes 41-75% |
| Destiny | 3 | 3 | Nov 1 surge; total volume 3-4x normal |
| Hasan_Piker | 3 | 3 | includes one LeftoversH3-home account posting 22 comments |
| LeftoversH3 | 1 | 1 | Oct 28 00:00, 64 outsider comments over 22 threads |
| thedavidpakmanshow | 1 | 1 | Nov 1 20:00, 83% Destiny homes |
| Asmongold | 1 | 1 | |
| IsraelPalestine, ukraine, dsa | 2 each | 0 | 2-9 comment hours with near-zero expectation |
| Conservative, TankieTheDeprogram, samharris | 1 each | 0 | same |
| LivestreamFail, h3h3productions, atrioc, h3snark | 0 | 0 | h3snark not in the pull |

False alarms on baseline weeks: Poisson 3.53% of hours (35x nominal), NB 0.86% (8.6x). Bot Bouncer-listed accounts: 0 of
277 outsider accounts in alarm-hours, 6 of 4,518 (0.13%) in normal hours. Post-hoc variants (homes from baseline weeks;
total-comment exposure) move alarms to r/atrioc Oct 29 18:00 UTC (34 outsider comments vs 1.5 expected, 71%
LivestreamFail homes, 91% in one thread) and LivestreamFail Nov 1 22:00. They are sensitivity checks, not scored.

### 3.3 Claim check (Oct 13-19, the six subs)

From `docs/claim-check-oct13-19.md` (`a17cdd0`):
- **Claim rate:** 15 of 150 random comments made a checkable claim, 10% (Wilson 6.2-15.8%). The keyword screen caught
  1.3%.
- **Ratings:** of 27 distinct claims checked, 14 were true or mostly true, 8 false or misleading, 5 can't be checked.
- **Spread:** 19 hand-checked asserts of false or misleading claims across 98,790 comments, 0.019% (0.012-0.030%),
  against 22 disputes.
- **By sub (asserts):** Destiny 11, LivestreamFail 8; Hasan_Piker, h3h3productions and atrioc 0. The h3snark week was
  in the data and has 0.
- **Accounts:** 17 asserted a false or misleading claim, all one-offs: 0 repeat spreaders, 0 one-directional. None is
  among the newest 3% of accounts or on the round 2 bot list.
- **Scores:** asserting comments scored a median of 9; comments mentioning true claims, 2.

Per-sub false-claim *rates* (asserts per sub comment): **MISSING**. The doc gives asserts by sub but not each sub's
comment total for that week, and the Oct 13-19 six-sub pull isn't on the laptop.

### 3.4 Idea bundles and cross-pollination

From `docs/opinion-bundles.md` (`3bedb23`, `dd50651`, `a9cd994`) and `docs/crossover-pooled-predictions.md`
(`467036c`):
- **Pairs that held in every week** (z with account histories): anti_trump + anti_ice (6.6 Oct 20-26; 3.4 and 3.2 in the
  September weeks), hasan_neg + anti_tankie (5.5; 2.1, 2.7), gaza_genocide + anti_zionist (5.1; 3.6, 4.0).
  gaza_genocide + anti_tankie fell to 1.2 and 1.6 in September, so it is an event effect.
- **Carriers:** 104 of 2,496 position-taking accounts (4.2%) carried any position into another sub; 123 of 3,143
  position comments (4%). No heavy carriers: the median carrier did it once.
- **Where positions travel:** among 597 random six-sub accounts, 86% of mainstream anti-Trump, 79% of pro-Palestine,
  49% of anti-Hasan and 30% of h3-drama positions were voiced outside the six subs (politics, PublicFreakout, Fauxmoi
  and similar).
- **Crossings:** Destiny regulars are the largest outside group in r/thedavidpakmanshow in all five pooled weeks, 8-12%
  of its comments. 11 of 71 crossings with 100+ comments were hostile at the 1.5x bar, mostly into the h3 subs and
  r/neoliberal. In r/h3h3productions, Hasan regulars' comments in the Ethan week were 33-34% at or below 0, against
  10% for locals. Only 14 such comments came in the four quiet weeks.
- **Overlap from the drama subs, Oct 20-26:** pakman 24.2%, dsa 17.7%, LeftoversH3 17.0%, samharris 11.1%. In
  September: pakman 26.3% / 18.6% (structural), dsa 5.9% / 5.1% (event).
- **Coordination:** 0 seeder-to-amplifier pairs across 3+ threads.

### 3.5 Oct 20-26 expansion subs (tier 1)

The expansion covered 14 subs with 215,673 comments after removing mod and bot accounts (`docs/opinion-bundles.md`).
Six of the 13 regex position patterns fell under the 65% accuracy bar there and are excluded in those subs. Blind
Trump-stance cells (40 per sub; second coder kappa 0.78):

| Sub | Net (for minus against) |
|---|---|
| Conservative | +30 after the correction (+24 raw) |
| Asmongold | +33 on 6 side-takers |
| PoliticalCompassMemes | -89 |
| dsa | -88 after the correction |
| neoliberal | -100 |
| thebulwark | -100 |

Every cell has under 30 side-takers. The pooled opinion sheet (45 cells, 30 comments each, one coder) is in
`docs/opinion-pooled-predictions.md`.

## 4. News-sub topic-matched threads (politics, worldnews)

**Never ran, as far as any file shows.** The README lists "topic-matched news threads" as an `arctic.py` capability.
No results file, no predictions file and no `reddit_pulls` folder for it exist (searched the repo with `git grep` for
topic-matched, news threads and topic_threads, and searched `~/socialscope_data/reddit_pulls/`).

What did run is a **posts-only context pull** of r/politics, r/worldnews and r/news for Aug 1-Nov 2
(`docs/context-subs-results.md`, `scripts/pull_context_subs.py`, now in `archive/`). From the zip counts:

| Sub | Aug | Sep | Oct | Nov 1-2 |
|---|---|---|---|---|
| politics | 9,894 | 9,006 | 9,021 | 619 |
| worldnews | 4,659 | 5,128 | 4,979 | 251 |
| news | 2,839 | 2,672 | 2,517 | 106 |

No analysis of these context pulls has a results file: **MISSING** (looked in `docs/`).

## 5. Talking-point clustering

| Version | Method | Labeled sample | TP | COINCIDENCE | MEME | QUOTE | TEMPLATE | Source |
|---|---|---|---|---|---|---|---|---|
| v1 | exact 8-word phrases | 150 | 22% (33) | 59% | 11% | 7% | **MISSING** (not reported) | `docs/crossover-pooled-predictions.md` (`115cf89`) |
| v2, cosine 0.80 | embeddings (MiniLM), leader clustering | 150 | 86 (57%) | 62 (41%) | 2 | 0 | 0 | `docs/talking-points-v2-predictions.md` (`92f58f1`) |
| v2, cosine 0.85 | same | 100 (parts 1-2) | 71 | 23 | 4 | 2 | not reported | same (`6568c18`) |

- **v1:** found 559 (Aug 18), 608 (Sep 8), 471 (Sep 22), 549 (Oct 13) and 1,919 (Oct 20) phrase clusters. Its direction
  and first-seen results were voided by the labels.
- **v2 clusters** in `~/socialscope_data/tp_v2_mini/clusters_*.csv` (unlabelled):

  | Threshold | Aug 18 | Sep 8 | Sep 22 | Oct 13 | Oct 20 | Oct 27 (partial) | Total |
  |---|---|---|---|---|---|---|---|
  | 0.80 | 71 | 66 | 43 | 50 | 1,262 | 424 | 1,916 |
  | 0.85 | 4 | 5 | 1 | 3 | 255 | 61 | 329 |

- **First-seen sub, 0.85 (all weeks):** h3h3productions 173, LeftoversH3 78, LivestreamFail 34, Destiny 19,
  Hasan_Piker 9, neoliberal 6, others 1-2 each. At 0.80: h3h3productions 863, LeftoversH3 460, LivestreamFail 198,
  Destiny 143, neoliberal 74, Hasan_Piker 51. These are unlabelled cluster counts, dominated by the Oct 20 drama week.

**Label counts per sub: MISSING.** The labeled CSVs the doc names (`work/tp/gem_tp*.csv`, `gem_085_p3_run1`) are not
in the repo, not on the laptop (searched `~`), not on this PC and not on Drive (searched by title).

## 6. Calibration against Bot Bouncer

- **Labels:** Bot Bouncer listings are positive-only: a ban is a positive, an absence is not a negative. Precision
  is therefore reported with intervals, and recall only as recall *on listed accounts*, a bound on true recall.
- **Confirmed accounts available:** 536,088 accounts with latest verdict banned across the four Jul 1-Nov 2 pulls;
  in-sub cohorts 190 banned test positives, 263 pending, 114 train positives before dropping accounts without history
  (`groups_summary.md`). Scored: 189 positives and 261 pending. Features cover 3,264 of 3,267 accounts; 1 positive
  and 2 pending dropped, one of them because it has no history (`docs/repull-results.md`). The file does not say why
  the other two dropped. Bot Bouncer bots
  on the public site: 0. Submission tracker: 0 rows (`~/socialscope_data/botfinds/tracker.csv`,
  `socialscope-pages/data/botfinds.json`).
- **Chosen threshold:** full model, 1% CV target, threshold 0.4828 (`results_repull.md`).

| Measure (re-pull test side) | Value | 95% interval |
|---|---|---|
| Recall on listed positives | 62%, 118/189 | Wilson 55-69%; bootstrap 52-72% |
| Test false-alarm rate | 1.7% | bootstrap 0-3% |
| AUC | 0.931 | 0.908-0.952 |
| Precision at an assumed 1% bot share | 27% | bootstrap 18-58% |
| Precision at an assumed 5% bot share | 66% | bootstrap 53-88% |
| Pending accounts flagged | 10.3%, 27/261 | Wilson 7.2-14.6% |
| Same model, old threshold (1% quantile of test controls) | 57% recall, precision at 1% bots 36% | recall bootstrap 44-72% |

Precision here is modelled at an assumed base rate. It is not observed precision on a natural population. Observed
precision against Bot Bouncer, where the files give it: Oct 6-12 combined rule 22 of 813 flagged were listed, 2.7%
(1.8-4.1%); the newness rule 11 of 802, 1.4% (0.8-2.4%); the lookup rule 17 of 17 (`docs/bot-calibration-study.md`).
These are lower bounds, since unlisted flagged accounts may be bots.

- **Pre-ban leakage audit:** the re-pull cuts every history at its anchor (listing date for positives and pending,
  matched dates for controls). `accounts_repull.csv` shows the cut removed items for 116 of 189 test positives, 185 of
  261 pending, 137 of 478 test controls, 75 of 114 train positives and 870 of 2,222 train controls (`n_after_anchor >
  0`), so the cut ran. Removed-item share in the window: positives 0.015 vs controls 0.001, kept out of the model
  (`docs/repull-results.md`). The aged_drift test found and fixed a leak: checking at the last pulled item used days
  after the test week; the honest cut at Sep 15 gave 14% vs 5% (`docs/bot-calibration-study.md`). A written result of
  the five-check leakage audit: **MISSING** (no results file; the audit's checklist sits in the private
  `bluesky/RECON.md`).
- **kNN evidence** (`~/socialscope_data/repull/out/knn_repull.md`):
  - Coverage: 153 flagged accounts on test plus pending.
  - Flagged test positives: median nearest-ban distance 3.74, k=10 ban share 0.60 (12.3x base rate).
  - Flagged controls: 6.29, 0.20.
  - Flagged pending: 3.79, 0.40.
  - AUC of the k=10 ban share 0.882. At a 1% bot share, the 0.5-1.0 ban-share bin reweights to 32% bans.
- **Classifier status:**
  - The re-pull classifier `model_repull.pkl` (scikit-learn 1.9.1) is frozen and runs the public Lookup tab
    (`docs/lookup-results.md`).
  - The forward test uses the earlier Nov 2 in-sub model (sha prefix a1978ad38af51414), not the re-pull model
    (`docs/forward-test-predictions.md`).
  - The Bluesky transfer of the frozen model passed a plumbing check only (no scores read; commit `f2cca59`).
- **Listing-date re-pull:**
  - Applied to Bot Bouncer bans: test and train positives and pending, cut at the listing date.
  - Applied to random in-sub controls at matched anchor dates, with the same per-kind cap (`docs/repull-predictions.md`).
  - **Not applied** to Bot Bouncer "organic" verdicts. They are not a group in the re-pull cohorts (`groups_summary.md`
    lists test_pos, test_pending, test_ctl, train_pos, train_ctl). Organic accounts appear only in the Nov 1 sitewide
    training set, which cut histories at the listing date (`docs/bot-calibration-study.md`, training-set entry).

## 7. Predictions scorecard

"Commit check" compares the first commit of the prediction with the commit where its result first appears, on any
branch (`git log --all`). **Same commit** or seconds apart means git can't show the prediction came first; the doc's own
"written before" statement is then the only record.

| # | Study | Predictions (commit) | Result (commit) | Commit check | Score (from the file) |
|---|---|---|---|---|---|
| 1 | Bot calibration round 1, P1-P10 (Oct 20-26) | `a17cdd0` Oct 29 (doc says Oct 26) | `a17cdd0` | same commit | 4 right, 5 wrong, 1 untestable |
| 2 | Version 2 fresh week F1-F6 (Oct 6-12) | `a17cdd0` | `a17cdd0` | same commit | 3 right, 3 wrong |
| 3 | Stage 2 full-history rules | `a17cdd0` | `a17cdd0` | same commit | 0 of 8 rules passed; fast_replies passed after context |
| 4 | Round 2 v2 rules | `a17cdd0` | `a17cdd0` | same commit | reply_window, fast_replies passed; tourist precise but rare; hit_and_run failed |
| 5 | Round 3 (young_account) | `a17cdd0` | `a17cdd0` | same commit | young_account passed (41% vs 4%); combination failed |
| 6 | Bot-rich round, v4/v5/v6 rules | `a17cdd0` | `15b7f5a` (29 min later) | order holds, same day | young_account_true 87% vs 4%; content and report rules near zero |
| 7 | Round 4 (tier 1 subs) | `d0d62df` Oct 29 23:35 | `fa83063` Oct 30 08:28 | holds | 4 held (3 and 4 on the bot side only; controls understated by design), 1 missed, 1 inconclusive |
| 8 | September baseline | `dce597f` 08:34 | `a9cd994` 08:40 | holds (6 min) | 1 held, 1 partly, 1 split, 1 untestable, 2 missed |
| 9 | aged_drift fresh test | `8e69c71` | `8fa1f93` | holds | 1 held (5), 2 partly (2 bar call held, catch missed; 4 controls held, bots missed), 2 missed (1, 3) |
| 10 | aged_drift checkpoint | `4e0c09f` | `d812f38` | holds | 2 held (3, 4), 1 about held (5), 1 just under range (1), 1 missed (2) |
| 11 | Label audit | `9e89fab` 15:51 | `17b16dc` 15:54 | holds (3 min) | 1 held (2), 2 partly (1: bot share held, human share above range; 3 partly held) |
| 12 | Crossover pooled, task 1 | `8478c28` 16:05 | `467036c` 16:08 | holds (3 min) | 1 held, 3 missed |
| 13 | Crossover pooled, task 3 (direction) | `8478c28` | `115cf89` | holds | void: v1 clusters were mostly stock phrases |
| 14 | Opinion pooled sheet | `acff810` 16:09 | `acae700` 16:17 | holds (7 min) | 2 mostly held, 1 partly missed, 2 missed |
| 15 | Training set and hijack rules | `ed490ec` | `fb23480` | holds | 1 missed, 1 mostly missed, 1 half held, 2 recall-high/FPR-held |
| 16 | In-sub rebuild | `f010a26` 05:32 | `e5ad4fd` 09:14 | holds | 4 held, 1 beaten, 1 unscorable |
| 17 | Talking points v2 | `e1cab5a` | `92f58f1` | holds | 3 held, 1 half held, 1 missed |
| 18 | Sarcasm-aware prompt | `adbf57a` 16:08 | `5a88e2c` 16:15 | holds (7 min) | 1 held, 4 missed |
| 19 | Commentator valence (amended 7-10) | `98b13c2` | `3e1f8cd` | holds | 1 borderline, 1 missed, 1 held, 1 not run |
| 20 | Context subs | `f180e42` | `f180e42`, corrected `632b74b` | same commit | 1, 3, 4 held; 2 missed on corrected data |
| 21 | Opinion bundles, Oct 29 run | `3bedb23` | `3bedb23` | same commit | 1 held, 1 held/missed, 1 untestable |
| 22 | Tier 1 expansion | `dd50651` | `dd50651` | same commit | 1 held (3; fourth bundle untestable), 3 missed (1, 2, 4), 1 untestable/reversed (5) |
| 23 | Claim check Oct 13-19 | `a17cdd0` | `a17cdd0` | same commit | 4 right, 1 half right, 2 wrong |
| 24 | Brigade alarm v1 | `003d07e` Nov 9 09:48:47 (doc says Nov 5) | `7a61ea7` 09:48:48 | 1 s apart | 3 hits, 1 partial, 2 misses |
| 25 | Re-pull fix, predictions 1-6 and the flagged-share part of 7 | `003d07e` Nov 9 | `f5ebef3` Nov 10 | holds | 4 hits (2, 3, 6, 7 flagged share), 3 partials (1, 4, 5) |
| 26 | Re-pull, the Fisher part of prediction 7 | `003d07e` | `7f15e0b` 09:48:50 | 3 s apart | held (p = 0.0061); with row 25, prediction 7 held overall |
| 27 | Context-flip calibration | `6b6bfe8` | `6b6bfe8` | same commit (doc cites a sha256 of the frozen predictions) | 3 held, 4 missed, 1 uninformative |
| 28 | Hasan Israel-control conspiracy (chat) | `a54ca5f` 13:53 | `0bd70e0` 16:46 | holds | Opus 4 of 5, Fable 3 of 5, agreement held |
| 29 | Account lookup (one account; not a study finding) | `80aa244` | `a5786a7` | holds | 7 of 7, informed by a third-party card, so not independent |
| 30 | **Forward test** (Nov 2 model, 2,000 accounts) | `72a1c77` Nov 2; scores frozen `ecc58ed` Nov 3 | pending | holds so far | prediction 4 held (22 flagged, 1.1%); 1, 2, 3 and 5 **pending, check Dec 1** |
| 31 | **Brigade alarm v2** (Nov 3-9) | `003d07e` Nov 9 09:48 | none | holds: committed before the Nov 3-9 pull started (Nov 9 17:25 ET, `~/socialscope_data/nov03_week_queue.out`) | **pending**: data pulled (`reddit_pulls/nov03`, 18 subs), never scored |
| 32 | **Bluesky politics** | `3055ded` Nov 19 | none | n/a | **pending**: window Nov 20-Dec 11; pilot days are development data |

Tally: no single hit rate is given. The files score outcomes on different scales ("partly", "split", "beaten",
"untestable"), and a combined count of individual predictions across all 29 scored rows is not in any file. See each
row. Misses are kept in every file.

## 8. DGG side study

Moved to `../dgg-chat-site` on Nov 19 (cloned; read from its `docs/`). Hashes are this repo's, where the work was
committed.

| Study | Predictions | Results | Commit check | Score and main result |
|---|---|---|---|---|
| OverRustle archive, first 12 channels | `a375f8f` Nov 2 | `76114be` Nov 3 | holds | Mixed; DGG messages per month rose from 0.87M (2014) to 2.06M (2020) at a flat 6-9k monthly chatters |
| OverRustle deeper cuts | `292dd7c` Nov 3 22:59:07 | `0b353e8` 22:59:07 | same second | 5 held, 1 partly, 1 missed narrowly; of 13,453 accounts in both Destiny's and Hasan's Twitch chats in early 2019, 31.5% were still in Hasan's by spring 2020 vs 19.0% in Destiny's |
| Chat-to-Reddit crossover | `673a2a2` 07:54 | `c2d1cc2` 07:58 | holds (4 min) | the nick filter zeroed ordinary words; most scores wait for a rerun |
| DGG live glossary | `e90db9c` Nov 2 | `7266402` Nov 3 (provisional file scored Nov 9) | holds | 2 held, 1 partly, 2 missed, 4 not scorable |
| Election night | `48371e1` Nov 10 (doc says Nov 5, 2:10 PM) | `7a61ea7` Nov 9 | **prediction file's first commit is after the result's** | 6 held, 1 failed, 1 untestable, 1 held with caveat |
| DGG vs Hasan chat, keyword | `ba2cfc1` 09:20 | `d6e9509` 09:27 | holds | 3 hits, 1 partial, 9 misses: both chats are mostly short reactions |
| Antisemitism keyword coding (paid models) | `711746a` 10:53 | `8996202` 11:16 | holds | Opus 3 of 7, Fable 4 of 7; models agree 87.2% on stance (kappa 0.64) |
| Israel-control conspiracy (in socialscope) | `a54ca5f` | `0bd70e0` | holds | endorsed control or dual-loyalty talk 2.0-3.7% of on-topic Hasan-chat messages vs 0.5-0.7% in DGG |
| Local GPU coder vs paid coders | `d193e53` (dgg-chat-site) Nov 19 | running | n/a | pending |

All chat results are aggregates. The live logger stores DGG nicks raw since Nov 5 by the owner's decision; nothing
here names a chatter.

## 9. X and Bluesky

- **X:** no X data has been collected. The skill's loader accepts X records (`scripts/analyze.py`; synthetic tests only,
  `test/make_fake_x.py`), and the ground rules forbid scraping X directly (`README.md`, rule 6). Status: not
  collected.
- **Bluesky:** predictions committed `3055ded` (Nov 19). The test window is Nov 20-Dec 11, but `window.start` and
  `window.end` are still null in `bluesky/config/targets.yaml` until the pilot passes. Everything so far is pilot
  development data (`docs/bluesky-politics-predictions.md`: "Nothing from them is scored").
- **Collected as of Nov 19, about 19:45 UTC** (`~/socialscope_data/bluesky_status/status.json`, counts only):
  - **Recorder:** connected since 17:01 UTC. Counters restarted at 18:01:56 after the required kill test. Since then:
    2,832,511 events seen, 190,329 kept, 2,853 live repliers, 25,405 other authors.
  - **Disk:** 174 MB in `~/socialscope_data/bluesky`.
  - **First hourly pass:** 1,010 target posts (21 targets), 33,017 replies, 16,096 thread repliers; 2,000 profiles; 200
    full histories with 255,536 records; 1,221 PLC logs.
  - **Label replay:** running. Cursors at 12,204,082 (Bluesky moderation) and 6,088,189 (Skywatch).
- **Transfer plumbing check:** 200 of 200 accounts ran through the frozen v7.1 code with 0 errors. 26 of 39 model
  inputs carry values; 13 need subreddit or karma and are blanked. No scores were read (`f2cca59`).

## 10. Methods and caveats

- **Commit order.**
  - **First commit:** the repo starts at `a17cdd0` (Oct 29, 14:44 ET). The Oct 26-29 bot rounds through round 3 and
    the bot-rich pre-registration, the claim check and the first opinion-bundle run landed together with their
    results, so their "before" claims rest on the docs alone. The bot-rich results (`15b7f5a`) and round 4
    (`d0d62df` before `fa83063`) do show the predictions first.
  - **Nov 9 batch:** brigade v1 and re-pull prediction 7 were committed seconds before their results.
  - **Election night:** its predictions file first appears a day after its results file.
  - **Later studies:** predictions come first, often by only 3-7 minutes.
- **The history rewrite did not change the order.** In the pre-rewrite mirror (`~/repo-backups-2026-11-19/socialscope.git`,
  made before either Nov 19 rewrite), the same commits carry identical author and commit times:
  - brigade v1, v2 and re-pull predictions `a90344c` 09:48:47;
  - brigade v1 and election-night results `f03880a` 09:48:48;
  - re-pull Fisher part `03892a0` 09:48:50;
  - election-night predictions `9cdf019` Nov 10 11:26:29.

  So the one-second gaps are original. The laptop session committed the cloud session's files in one batch. The
  `a90344c` message says the three predictions were written Nov 5 in the claude.ai project docs (brigade v1 17:49Z,
  re-pull 17:55Z, v2 18:30Z). That project's file history, not git, is the record that could confirm those times.
- **Labels.** Bot Bouncer is incomplete, positive-only ground truth that skews to fresh accounts sitewide and to
  hijacked aged accounts in these subs. Label noise for aged bans is at most 17% (`docs/label-audit.md`).
- **Populations.** Sitewide bans vs in-sub regulars confounded the Nov 1 training set (AUC 0.99 was the confound).
  Round 4's controls excluded young accounts by construction. Both are documented in the study doc.
- **History cap.** Over half of the in-sub accounts hit 1,000 comments (section 2.3). The re-pull fixed the
  anchor-date problem, not the cap.
- **Data integrity.** The laptop had RAM faults from about Nov 5-11. Only results a second run reproduced are reported
  in `docs/repull-results.md`; the old_last rows were reproduced on Nov 11.
- **Coders.** Most stance and talking-point labels come from one human-or-model coder per item. Second-coder checks:
  Trump sheet kappa 0.78, sarcasm prompt kappa 0.735. Model labelers drifted between chats (talking points 0.85 part
  3 set aside).
- **Arctic Shift.** No votes or creation dates in week dumps. Removed content partly missing. Gaps are listed in 2.4.
- **Raw vs filtered counts.** Section 2 counts are raw zip items. Study docs report filtered counts.

## 11. Open questions and next steps

**The three biggest gaps:**
1. **Many early "pre-registered" results can't be verified from git.** Rounds 1-3 (with the Oct 6-12 test and stage
   2), the claim check, the first two bundle runs, brigade v1 and election night all have predictions committed with or
   after their results. The rewrite didn't cause this (section 10). The claude.ai project docs where the Nov 5
   predictions were written may hold earlier timestamps. The forward test on Dec 1 is the first clean, out-of-time
   test of the classifier.
2. **The Drive-only batches are uncounted.** The Oct 6/13/20 checks and botrich are on Drive only and too large for the
   connector, so their item and cap counts are MISSING, as are the Oct 6-12 and Oct 13-19 six-sub weeks. A laptop
   download and count would close this.
3. **The labeled talking-point files are gone.** Per-sub TP/QUOTE/MEME/TEMPLATE/COINCIDENCE counts can't be rebuilt from
   anything on disk; only the totals in the doc remain.

**Also open:**
- Per-sub denominators for bot density and false-claim rates.
- A written result of the pre-ban leakage audit.
- Brigade v2, which has data and predictions but no score.
- The context pulls (politics, worldnews, news, Fauxmoi, youtubedrama, DecodingTheGurus), which have no analysis.
- The aged-account bot type that no rule catches except the hijack signature.

**Next scheduled:**
- **Forward test** check after Nov 30 (Bot Bouncer pull, Dec 1).
- **Bluesky:** pilot check Nov 20 17:01 UTC, then the 21-day window.
- **Weekly Reddit pull:** Thursdays, first Nov 26. The Nov 10-16 week was pulling at the time of writing.

## Appendix A. Items per sub and window (raw zip counts, posts / comments)

Counted Nov 19 from `~/socialscope_data/reddit_pulls/`. "–" = no file for that sub and window. nov10 was still
downloading. Two checks:
- **h3fix_oct27:** a byte-identical copy of the `oct27` h3h3 comments file (same sha256); don't add it to `oct27`.
- **Hasan_Piker 8,853:** `tp_fill` Oct 13 and `sep08` both show 8,853 comments. They are different files (different
  sha256; items dated Oct 13-20 vs Sep 8-15), recounted directly, so the match is a coincidence.

| Sub | aug18 2026-08-18 | aug25 2026-08-25 | sep08 2026-09-08 | sep22 2026-09-22 | t1_oct13 2026-10-13 | tp_fill 2026-10-13 | tp_fill 2026-10-20 | six_oct20 2026-10-20 | oct27 2026-10-27 | h3fix_oct27 2026-10-27 | nov03 2026-11-03 | nov10 2026-11-10 | context 2026-08-01 | context 2026-09-01 | context 2026-10-01 | context 2026-11-01 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Asmongold | 589 / 7,659 | 896 / 10,503 | 1,070 / 10,377 | 1,146 / 12,125 | 976 / 8,169 | – | – / 6,532 | – | 921 / 6,392 | – | 797 / 4,725 | 867 / 5,026 | – | – | – | – |
| atrioc | 60 / 930 | 50 / 670 | 86 / 739 | 74 / 1,030 | – | – / 1,181 | – | 80 / 1,778 | 364 / 2,363 | – | 1,021 / 5,460 | – | – | – | – | – |
| Conservative | 456 / 12,092 | 477 / 15,791 | 641 / 18,506 | 388 / 11,017 | 519 / 11,005 | – | – / 4,873 | – | 509 / 4,090 | – | 849 / 8,368 | 410 / 3,798 | – | – | – | – |
| DecodingTheGurus | – | – | – | – | – | – | – | – | – | – | – | – | 108 / 5,009 | 97 / 2,652 | 97 / 2,426 | 7 / 145 |
| Destiny | 1,040 / 36,472 | 1,249 / 39,711 | 1,111 / 38,038 | 985 / 33,405 | – | – / 36,498 | – | 1,313 / 34,623 | 1,302 / 34,975 | – | 2,037 / 35,799 | 1,127 / 29,779 | – | – | – | – |
| dsa | 136 / 4,344 | 135 / 4,757 | 137 / 4,679 | 117 / 2,673 | 108 / 2,462 | – | – / 2,413 | – | 120 / 1,601 | – | 237 / 2,932 | – | – | – | – | – |
| Fauxmoi | – | – | – | – | – | – | – | – | – | – | – | – | 3,016 / 214,285 | 3,357 / 256,561 | 3,610 / 217,029 | 278 / 15,214 |
| h3h3productions | 840 / 11,421 | 913 / 11,884 | 853 / 11,092 | 695 / 8,560 | – | – / 9,400 | – | 15,511 / 186,856 | 5,923 / 95,537 | – / 95,537 | 2,504 / 44,272 | – | – | – | – | – |
| Hasan_Piker | 502 / 9,418 | 592 / 10,432 | 580 / 8,853 | 564 / 9,747 | – | – / 8,853 | – | 736 / 11,638 | 705 / 11,831 | – | 964 / 14,017 | 614 / 10,329 | – | – | – | – |
| IsraelPalestine | 89 / 10,266 | 81 / 7,304 | 86 / 8,673 | 156 / 14,018 | 119 / – | – | – / 8,089 | – | 88 / 7,004 | – | 58 / 5,033 | 45 / – | – | – | – | – |
| LeftoversH3 | 185 / 7,631 | 196 / 8,605 | 240 / 10,593 | 257 / 11,541 | 199 / – | – | – / 67,168 | – | 1,392 / 47,040 | – | 644 / 25,221 | – | – | – | – | – |
| LivestreamFail | 428 / 36,265 | 360 / 28,423 | 397 / 27,487 | 302 / 27,712 | – | – / 48,877 | – | 366 / 64,629 | 370 / 54,862 | – | 298 / 57,482 | – | – | – | – | – |
| neoliberal | 300 / 81,532 | 312 / 71,589 | 365 / 78,217 | 258 / 77,538 | 323 / – | – | – / 67,900 | – | 358 / 86,556 | – | 580 / 127,916 | – | – | – | – | – |
| news | – | – | – | – | – | – | – | – | – | – | – | – | 2,839 / – | 2,672 / – | 2,517 / – | 106 / – |
| Palestine | 485 / 3,693 | 406 / 4,430 | 393 / 5,023 | 396 / 4,204 | 325 / 2,950 | – | – / 2,764 | – | 335 / 3,010 | – | 291 / 2,607 | – | – | – | – | – |
| PoliticalCompassMemes | 248 / 33,130 | 232 / 28,732 | 274 / 40,921 | 165 / 22,854 | 203 / – | – | – / 31,989 | – | 211 / 24,353 | – | 376 / 41,040 | – | – | – | – | – |
| politics | – | – | – | – | – | – | – | – | – | – | – | – | 9,894 / – | 9,006 / – | 9,021 / – | 619 / – |
| samharris | 19 / 1,563 | 24 / 1,648 | 46 / 3,492 | 27 / 2,091 | 36 / 3,230 | – | – / 1,791 | – | 30 / 1,280 | – | 33 / 1,693 | – | – | – | – | – |
| TankieTheDeprogram | 396 / 5,884 | 406 / 6,535 | 372 / 4,710 | 419 / 4,920 | 421 / 4,942 | – | – / 4,941 | – | 452 / 4,981 | – | 456 / 4,728 | – | – | – | – | – |
| thebulwark | 243 / 10,103 | 254 / 13,051 | 276 / 10,636 | 282 / 9,989 | 283 / 8,520 | – | – / 8,725 | – | 434 / 20,522 | – | 670 / 20,026 | – | – | – | – | – |
| thedavidpakmanshow | 72 / 3,850 | 85 / 5,367 | 85 / 3,393 | 87 / 2,420 | 72 / 2,374 | – | – / 1,857 | – | 87 / 2,608 | – | 165 / 4,676 | – | – | – | – | – |
| ukraine | 517 / 9,000 | 411 / 6,163 | 460 / 8,959 | 391 / 6,633 | 573 / 13,666 | – | – / 11,528 | – | 479 / 7,384 | – | 463 / 7,337 | – | – | – | – | – |
| worldnews | – | – | – | – | – | – | – | – | – | – | – | – | 4,659 / – | 5,128 / – | 4,979 / – | 251 / – |
| youtubedrama | – | – | – | – | – | – | – | – | – | – | – | – | 408 / 5,671 | 433 / 7,599 | 422 / 7,196 | 23 / 239 |
