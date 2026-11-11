# Re-pull fix: results (predictions in repull-predictions.md, written Nov 5, 2026, unchanged)

Scored in parts. Only the piece of prediction 7 that needs no new data is scored so far; the rest waits on the
re-pull and rescoring run on the laptop.

## Prediction 7, Fisher part (scored Nov 9, 2026)

Blind read of accounts pending at Oct 28 vs random controls: 16 of 30 pending accounts judged bot-like, against 5 of
30 controls.

| | Bot-like | Not | Total |
|---|---|---|---|
| Pending at Oct 28 | 16 | 14 | 30 |
| Random controls | 5 | 25 | 30 |

Fisher's exact test: odds ratio 5.71, two-sided p = 0.0061 (one-sided p = 0.0031). The prediction asked for
p < 0.01. **Held.**

Caveat: the test is only as good as the blind read. 30 per arm is small; the 95% range on the pending share
(16/30, 53%) runs roughly 36-70%.

## Predictions 1-6 and the flagged-share part of 7 (scored Nov 10, 2026, laptop session)

Source: `~/socialscope_data/repull/out/results_repull.md` (scored Nov 6 15:19; a fresh run on Nov 9 reproduced
features, per-account scores and the results file byte for byte, which rules out the laptop's RAM fault for these
numbers). Test side: 189 positives (117 aged, 72 throwaway), 478 controls, 261 pending. Train side: 114 positives,
2,222 controls. Bootstrap CIs: 2,000 resamples over accounts, threshold recomputed in each.

Two thresholds appear below. The **CV threshold** (new method) is set from training controls' out-of-fold scores, so
the test FPR it reaches is whatever it is (1.7% for the full model at the 1% target). The **test-control threshold**
is the old method, the 1% quantile of the test controls, which is what the old 67% used. Where the two disagree on a
verdict, both are given.

| # | Prediction | Result | Verdict |
|---|---|---|---|
| 1 | Recall at 1% falls to 45-60% (best guess 55%); bootstrap CI does not reach 67% | Test-control threshold: 57% (Wilson 50-64%, bootstrap 44-72%). CV threshold: 62% (55-69%, bootstrap 52-72%) at 1.7% FPR | **Partial.** Like-for-like point estimate lands in range, 2 points from the best guess; the CV-threshold estimate is above it. The CI clause misses under both thresholds (upper ends 72%). |
| 2 | AUC 0.90-0.95; recall moves more than AUC | AUC 0.931 (0.908-0.952), from 0.97 published (0.959 on the old data here). Recall at 1% fell 10 points (67 to 57%, like for like) while AUC fell 0.03-0.04 | **Hit.** |
| 3 | items, log_items, hist_age leave the top 5 importances; true_age and solicit_broad move up | Re-pull top 5 (full): pw_new_subreddit_share, sb, pw_link_share_change, pw_window_items, sh. items, comments and hist_age are not in the top 15. sb rose from 3rd to 2nd; true_age rose from outside the top 15 to 12th | **Hit, with caveats.** On the old data here items (12th) and hist_age (7th) were already outside the top 5; the count feature that led was comments (2nd), and it is gone. One volume feature stays: pw_window_items (items in the 30-day window, dropped from the no-volume model) is 4th, as it was before. true_age's rise is small (0.002 AUC drop). |
| 4 | Recall drop concentrated in aged bans; throwaway recall changes by under 5 points | CV threshold, 1% target, full model. Aged: 71% (dry run) / 69% (old data here) to 65% (56-73%). Throwaway: 62% / 61% to 58% (47-69%) | **Partial.** Throwaway moved 3-4 points (holds). Aged fell 4-6 points, only slightly more than throwaway, and the CIs overlap heavily, so "concentrated in aged" is not shown. |
| 5 | Full vs no-volume gap at 1% shrinks to under 5 points | Old gap: 10 points published (67 vs 57), 11 on the old data here. Re-pull: CV threshold 62 vs 56 = 6 points (paired CI -1 to +13, full better in 94% of resamples); test-control threshold 57 vs 56 = 1 point. AUC gap 0.014 (0.005-0.025) | **Partial.** The gap shrank by about half or more under both thresholds; under 5 points with the old threshold, 6 with the CV threshold (whose FPR also differs: 1.7% vs 1.3%). |
| 6 | Bootstrap CI on recall at 1% at least 15 points wide, wider than the old Wilson 14 | CV threshold: 52-72%, 20 points. Test-control threshold: 44-72%, 28 points | **Hit.** |
| 7 (flagged share) | Share of pending flagged at 1% stays well above random controls | Pending: 27/261 = 10.3% (Wilson 7.2-14.6%). Test controls: 8/478 = 1.7% (0.9-3.3%). Fisher OR 6.8, p = 4e-7 | **Hit.** Together with the Fisher part above, prediction 7 **held**. |

Tally: 4 hits (2, 3, 6, 7), 3 partials (1, 4, 5), no outright misses. The one clause that clearly failed is the CI
part of prediction 1: the interval is wide enough to still include the old 67%.

### Old data vs re-pull (same evaluation code, CV threshold at the 1% target)

| data | model | AUC (95% CI) | test FPR | recall (CI) | aged | throwaway | recall, test-control threshold |
|---|---|---|---|---|---|---|---|
| old, last-item anchors* | full | 0.959 (0.941-0.974) | 0.6% | 66% (59-72%) | 69% | 61% | 72% |
| old, last-item anchors* | no-volume | 0.926 | 1.0% | 55% (48-62%) | 52% | 61% | 61% |
| old, matched anchors | full | 0.936 (0.914-0.955) | 0.4% | 54% (47-61%) | 56% | 52% | 59% |
| old, matched anchors | no-volume | 0.917 | 0.8% | 55% (48-62%) | 55% | 55% | 58% |
| re-pull | full | 0.931 (0.908-0.952) | 1.7% | 62% (55-69%) | 65% | 58% | 57% |
| re-pull | no-volume | 0.917 (0.888-0.942) | 1.3% | 56% (49-63%) | 58% | 53% | 56% |
| re-pull | age rule | 0.576 (0.521-0.628) | 4.4% | 26% (20-33%) | 0% | 68% | 12% |

*old_last ran once (Nov 6). Two repeat runs on Nov 9 failed while reading their input, which was corrupted in memory
(the file on disk is fine), so these rows are **not reproduced**. They agree closely with the cloud dry run in
RUNBOOK.md. old_matched was reproduced byte for byte.

### Cohorts (rebuilt with the Oct 20-27 gap pull vs documented)

| group | rebuilt | documented | in features |
|---|---|---|---|
| test_pos | 190 | 186 | 189 |
| test_pending | 263 | 259 | 261 |
| test_ctl | 478 | 483 | 478 |
| train_pos | 114 | 114 | 114 |
| train_ctl | 2,222 | 2,216 | 2,222 |

### Things that looked off

- **Thresholds run hot.** The 1% CV target reached 1.7% FPR on test controls, 2% reached 2.3%, 5% reached 7.5%
  (dry run: 9.2% at 5%). Training controls still score lower than the Nov 1 random test controls.
- **The age rule can't reach low FPRs.** Its 1% target lands at 4.4%, probably from ties in account age.
- **Removed-item share** in the window: positives 0.015, controls 0.001 (15x; the runbook expected about 3x). Kept
  out of the model.
- **true_age vs log(items)** on controls: +0.50 (expected +0.48).
- **fallback_last controls:** 2, against about 10 expected.
- **Missing accounts:** features cover 3,264 of 3,267; 1 positive and 2 pending dropped (one has no history).
- **pull.py batch-name bug (fixed Nov 6).** Test and train batches shared `repull_<day>` names, so the train run
  overwrote test-side zips for overlapping days. Test batches are now `repull_test_<day>`, rebuilt from the saved
  per-user parts without re-pulling.
- **Laptop RAM fault.** Bit flips and segfaults since Nov 5-6 (page-cache copies of zips differ from disk). Results
  above are only the ones a second run reproduced exactly, except the old_last rows, marked.

## Addendum, Nov 11 2026 (laptop session): old_last reproduced

A second old_last run on Nov 11 (`~/socialscope_data/oldlast_check_queue.sh`, tag `old_last_check`) matched the
originals byte for byte: `features_old_last.csv` (Nov 6), `accounts_old_last.csv` and `results_old_last.md` (rescored
Nov 9 from the Nov 6 features; results compared without the "scored 20…" line). So the old_last rows above are now
reproduced too, and every number in this file has been matched by a second run. The first four tries that morning
failed reading their input (cached CRC errors, one garbled UTF-8 byte); the run that worked had
`tools/badpage_hold` holding the 9 bad RAM pages it found. See docs/ram-fault-checks.md.
