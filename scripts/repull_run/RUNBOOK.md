# Re-pull run: steps for the laptop Claude Code session

Written Nov 5, 2026 by the cloud session, which cannot reach Arctic Shift. Everything below runs on the laptop.
Read `scripts/repull_run/common.py`'s docstring first; each script's docstring says what it changes and why.

## What this fixes

`scripts/insub_run` pulled every history newest-first with a 1,000-per-kind cap and no end date, then cut positives
at their Bot Bouncer listing. A positive that kept posting after listing (98% of test positives did; median 80
post-listing items) lost pre-listing items to the cap, while controls kept all 1,000 and were cut at their own last
item. So `items`, `comments`, `log_items`, `hist_age`, `pw_window_items`, `pw_earlier_items` and the primary tier
(young_account reads "first item in the pulled history") carried a class artifact, the "without volume" ablation
still kept `hist_age` and count-coupled features, the control pre-window always ended on an active day, prewindow.py
counted `[removed]`/`[deleted]` as 9-character text, the 1% threshold was read off the test controls, and no number
had a CI. The fix: same cap for everyone, pulled with `end = anchor`; matched anchors for controls; removed text
left out; thresholds from training-side CV; bootstrap CIs; a cleaner ablation.

## What could and could not be reconstructed

The cloud session's cohort files (`groups.csv` for insub/train/augpanel/sep_test/round4, `bbinv/private_all.csv`,
`bbnov/private_nov.csv`, `seen_all.pkl`) are not on the laptop. `groups.py` rebuilds them from:

- the Bot Bouncer posts pulls under `reddit_pulls/bb_*` (latest verdict per account, as `bb_inventory.py` does);
- the five user lists (`users_to_pull_insub.txt`, `train/`, `augpanel/`, `septest/`, `round4/`);
- the block order of the panel lists (`screen.shortlist` wrote each group as a sorted block): augpanel
  [32 bots, 1000 controls], septest [53 later bots, 17 known bots, 400 controls], round4 [300 shortlist,
  300 controls, 17 known bots]. The script verifies the block lengths and stops if they differ.

One thing is missing: **Bot Bouncer listings from Oct 20-27, 2026.** The laptop holds Jul 1-Aug 31, Sep 1-Oct 19 and
Oct 28-Nov 2; the cloud inventory ran "through Oct 28". Without that week, 27 of the 480 insub accounts and about
100 of the 2,217 train-list accounts (sitewide bans and organic verdicts) look unlisted, and 10 panel bots
(3 augpanel, 7 septest) drop out of train_pos. Step 1 pulls that week (about 6 minutes). Its flairs are as of
today rather than Oct 28, so a few insub accounts that were pending on Oct 28 and banned since will land in
test_pos instead of test_pending; `groups.py` prints the listing source per group (`flair_source`) so the count is
on record. Nothing else changes cohorts. Dry-run on the laptop's data without the gap pull, counts before dropping
accounts without history: test_pos 182 (documented 186), test_pending 244 (259), test_ctl 479 (483), train_pos 104
(114), train_ctl 2222 (2216).

The `seen_all.pkl` check (account seen in the six pulled weeks) is not rebuilt: every panel account was drawn from
a pulled week's in-sub activity, so it holds by construction.

## Steps

All commands from `~/socialscope`. Nothing here touches git; commit when you choose (CLAUDE.md rule 2).

### 0. Dry run (2 minutes, no network)

```
python3 -I scripts/repull_run/groups.py            # expect exit 2 and the gap WARNING until step 1 is done
python3 -I scripts/repull_run/groups.py --allow-gap
python3 -I scripts/repull_run/pull.py --dry-run    # batch plan and time estimate; writes repull/work/anchors_private.csv
```
`pull.py --dry-run` draws and saves the control anchors (seed 20261105). If you run it before step 1 and then rerun
`groups.py` after step 1, **delete `~/socialscope_data/repull/work/anchors_private.csv`** so the anchors are redrawn
for the final cohort; the pull must start from the anchors file that matches `groups_private.csv`.

### 1-3. Gap pull, cohorts, histories (queued, about 16 hours)

```
cp scripts/repull_run/repull_queue.sh ~/socialscope_data/ && chmod +x ~/socialscope_data/repull_queue.sh
printf 'repull_gap\treddit_pull\trepull_queue.sh\trepull_queue.out\trepull_gap start\trepull_gap end\treddit_pulls/bb_oct20_27/pull_log.txt\n' >> ~/socialscope_data/jobs.tsv
printf 'repull\thistory\trepull_queue.sh\trepull_queue.out\trepull start\trepull end\treddit_pulls/repull_history_log.txt\n' >> ~/socialscope_data/jobs.tsv
cd ~/socialscope_data && nohup systemd-inhibit --what=idle:sleep --mode=block --who=socialscope --why="repull histories" ./repull_queue.sh > repull_queue.out 2>&1 &
nohup ~/socialscope_data/status.sh > ~/socialscope_data/status_loop.out 2>&1 &
```
The queue runs, in order:
1. `reddit_pull.py --subs BotBouncer --kinds posts --start 2026-10-20 --end 2026-10-28` into
   `reddit_pulls/bb_oct20_27/` (bb_nov did 6 days in 4.5 min; expect 5-8 min). Skipped if the zip exists.
2. `groups.py` -> `~/socialscope_data/repull/work/groups_private.csv` (usernames; never leaves the laptop) and
   `repull/out/groups_summary.md` (counts). Its output is copied into `repull_queue.out`.
3. `pull.py --only test` then `pull.py --only train`. Test side first (test_pos, test_pending, test_ctl, train_pos:
   about 1,010 accounts, ~4 h), then the 2,220 train controls (~12 h). Rates come from the Nov 1-2 logs: 18-22 s per
   capped control, ~9 s per positive; the oldest-item calls are skipped because the old `*_oldest.json` files
   already cover every account. Expect 15-17 h total; Arctic Shift throttling can add a few hours.

Where things land:
- `~/socialscope_data/reddit_pulls/repull/repull_<YYYYMMDD>_{posts,comments}.zip` and `_oldest.json`, one set per
  anchor day (about 117 days, Jul 1 - Nov 1), plus `.complete` markers and `_parts/` (per-user part files).
- `~/socialscope_data/reddit_pulls/repull_history_log.txt`: one `user histories: n/N users` line (status.py reads
  it), `batch ... done` lines, and `repull test|train: n/N accounts finished`.

Checking: `cat ~/socialscope_data/STATUS.txt` (status.sh rewrites it every minute while a job runs) or
`~/socialscope_data/status.sh --once`. The `repull` row shows accounts done out of the phase total. If the queue
dies (reboot, throttling), relaunch the same `nohup ... ./repull_queue.sh` line: every step resumes, and finished
batches are skipped by their `.complete` marker. When it ends, `repull_queue.out` has `repull end ... rc=0`; rc=1
means some accounts never finished (the log's last line counts them); rerun the queue once more.

### 4. Features and scores on the re-pulled data (about 15 minutes)

```
python3 -I scripts/repull_run/feats.py --mode repull --anchors ~/socialscope_data/repull/work/anchors_private.csv
python3 -I scripts/repull_run/score.py --tag repull
python3 -I scripts/repull_run/knn_evidence.py --tag repull
```
Outputs under `~/socialscope_data/repull/out/` (hashed ids only):
- `features_repull.csv/.pkl`: every feature per account.
- `results_repull.md`: rules, CV thresholds, test recall at 1/2/5% FPR with bootstrap CIs, AUC CI, precision at 1%
  and 5% bot share, aged vs throwaway recall, paired full vs no-volume vs age-rule, permutation importances, the
  count-coupling table, and the removed-share diagnostic.
- `accounts_repull.csv`: MATLAB export. Columns: account (hashed), group, split, label, label_source, bot_type
  (aged/throwaway), anchor_date, home_sub, score_full, score_novol, score_age, oof_score_full (train side),
  flag_1pct/2pct/5pct, then every feature column.
- `model_repull.pkl`: the fitted model with its thresholds (same shape as the forward-test model file).
- `knn_repull.md/.csv`: nearest confirmed-ban neighbours for every flagged account and the calibration table.
Private intermediates (usernames) stay in `~/socialscope_data/repull/work/repull/` (cut chunks, groups_k.csv,
scores_k/). Both folders are under `socialscope_data`, outside the repo.

### 5. The same evaluation on the OLD data, for the before/after comparison (about 10 minutes each)

```
python3 -I scripts/repull_run/feats.py --mode old --control-anchor last     # old anchors, new evaluation
python3 -I scripts/repull_run/score.py --tag old_last
python3 -I scripts/repull_run/feats.py --mode old --control-anchor matched  # old data, matched control anchors
python3 -I scripts/repull_run/score.py --tag old_matched
```
The cloud session ran both on Nov 5 on copies of the laptop's zips (gap pull missing, so cohorts a few accounts
smaller); the numbers are in docs or the hand-off message. Rerunning here after step 1 gives the same evaluation on
the full cohorts. `--keep-removed` reproduces the old prewindow text handling if you want that effect alone.

### 6. Score the committed predictions

`claude/repull-predictions.md` in the Botting Project (Projects tool, `project_read`) holds the predictions written
before this run. Do not edit it. For each numbered prediction, take the matching number from `results_repull.md`
(point estimate and 95% CI), mark held / missed / unscorable, and write `docs/repull-results.md` in the repo with
the table, the cohort counts next to the documented ones (from `repull/out/groups_summary.md`), the old-data
numbers from step 5 beside the re-pull numbers, and misses included (CLAUDE.md rule 3). Then commit.

## Optional: the prewindow flag inside the library

`feats.py` leaves removed text out by calling prewindow's component functions on filtered lists, so
`socialscope/prewindow.py` is untouched and every old result stays reproducible. If you prefer the flag inside the
library, `git apply scripts/repull_run/prewindow_exclude_removed.patch` adds `exclude_removed=False` to
`compute_prewindow_features`; the cloud session checked that the patched function and `feats.prewindow_features`
agree on 300 real accounts. Default behaviour is unchanged either way.

## Things to look at in the results that are not the headline number

- The 5% CV threshold reached 9.2% FPR on the test controls in the old-data dry run: training controls (mostly the
  Aug/Sep/Oct panels) score lower than the Nov 1 random controls, so a threshold set on train runs hot on test.
  If that persists on the re-pull, the two control pools differ, and the threshold should be reported with its
  achieved FPR, not its target.
- `removed_share` in the window is three times higher for positives than controls (0.018 vs 0.005). It is kept
  out of the model because removals can follow the listing itself.
- `true_age` correlates +0.48 with log(items) on controls; it stays in the no-volume model because it comes from
  `*_oldest.json`, not from the capped history, but it is the one age feature that survives the ablation.
- `anchor_src` in `accounts_*.csv`: controls marked `fallback_last` (10 accounts) were younger than every positive
  anchor and kept their own last item as anchor.

## Cloud dry run on the old data (Nov 5, 2026; gap pull missing, so cohorts a few accounts short)

Test: 178 positives (113 aged, 65 throwaway), 479 controls, 239 pending. Train: 104 positives, 2,221 controls.
Thresholds from training-side 5-fold out-of-fold scores; 2,000 bootstrap resamples. Old published numbers for the
same data: AUC 0.965, 67% recall at 1% (test-control threshold), 57% without volume.

| data, control anchor | model | AUC (95% CI) | 1% target: test FPR | recall (CI) | precision @1% bots (CI) | aged recall | throwaway recall |
|---|---|---|---|---|---|---|---|
| old, last item | full | 0.960 (0.943-0.975) | 0.8% | 67% (58-75%) | 45% (27-78%) | 71% | 62% |
| old, last item | no-volume | 0.922 (0.895-0.947) | 0.8% | 55% (47-66%) | 40% (22-74%) | 52% | 60% |
| old, last item | age rule | 0.572 (0.517-0.627) | 2.3% | 23% (15-30%) | 9% (4-23%) | 0% | 63% |
| old, matched | full | 0.927 (0.901-0.950) | 1.0% | 57% (48-68%) | 36% (19-73%) | 57% | 58% |
| old, matched | no-volume | 0.923 (0.895-0.947) | 1.3% | 54% (44-64%) | 30% (18-59%) | 55% | 54% |
| old, matched | age rule | 0.560 (0.507-0.613) | 4.0% | 21% (13-28%) | 5% (3-11%) | 0% | 57% |

Paired (same resamples): with last-item anchors, full beats no-volume in 100% of resamples (AUC difference
0.023-0.053; recall difference 3-19 points). With matched anchors the gap closes (AUC difference -0.005 to 0.014,
full better in 80%; recall difference -3 to +11 points). Both beat the age rule in 100% of resamples either way.
Old test-control threshold on the same models: full 72% at 1% (last anchors), 58% no-volume.
Reading: about a third of the old 67% -> 57% volume effect, and most of the full model's edge over no-volume, came
from the anchor asymmetry and the cap, not from behaviour. The re-pull is the clean test of what remains.
