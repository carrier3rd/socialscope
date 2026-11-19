# Bluesky module: Phase 0 recon

Written Nov 19, 2026 by the cloud session, from the repo at commit 925f8a7. Spec: `docs/BLUESKY_POLITICS_SPEC.md`.
No code has been written. Nothing here read any Bluesky data. Section 5 lists the decisions I need from the owner
before Phase 1.

What I could not see: anything under `~/socialscope_data` (the trained model, feature files, jobs.tsv, status.sh),
the installed `research-findings-infographic` skill file, and `scripts/lookup.py` (described in
`docs/lookup-predictions.md` but not committed). This container also cannot reach Bluesky: requests to
public.api.bsky.app, plc.directory, constellation.microcosm.blue and the Jetstream host are refused by the network
policy (403 at the proxy). So every endpoint, DID and handle in the spec is unverified until Phase 1 runs on the laptop.

## 1. What the spec asks for, and where it lives today

| Spec term | What exists | Where |
|---|---|---|
| Account-feature schema | Per-account metrics and rule flags from `history.score`, plus anchor-relative `pw_*` features | `socialscope/history.py` (`_flags`), `socialscope/prewindow.py`, `scripts/repull_run/feats.py` |
| Tier / naming implementation | No A/B/C tiers. Three separate things are called "tier" (section 3.1). Naming rule is CLAUDE.md rule 5, implemented for Reddit in `scripts/botfinds/` | `scripts/analyze.py` (`Ids.show`, `--reveal`), `history.score(reveal=)`, `scripts/botfinds/build_site_bots.py` |
| BotBouncer calibration | Latest-verdict-per-account inventory; recall of a detector run against it; rule rates per group with precision at 1% and 5% bot share | `scripts/bb_inventory.py`, `scripts/calibrate.py`, `history.score` (comparison.md), `analyze.load_known_bots(before=)` |
| CI | Wilson interval; 2,000-resample stratified bootstrap with the threshold recomputed in each resample; paired model comparisons | `scripts/repull_run/common.py` (`wilson`), `scripts/repull_run/score.py` |
| Leakage audit | Not one function. It is a set of practices from the re-pull fix (section 2.3) | `scripts/repull_run/{pull,anchors,feats,score}.py`, `RUNBOOK.md` |
| Poisson alarm | Hourly anomaly alarm. Plain Poisson failed its own test; the current rule is negative binomial (section 3.6) | `scripts/brigade_alarm/brigade_alarm.py` |
| kNN | Nearest confirmed-ban neighbours for flagged accounts, plus a calibration table | `scripts/repull_run/knn_evidence.py` |
| Report templates | `docs/<topic>-predictions.md` and `docs/<topic>-results.md`; explainer pages from the `explain-analysis` skill | `docs/repull-*.md`, `docs/brigade-alarm-*.md`, `.claude/skills/explain-analysis/` |
| social-coordination skill inputs | `analyze.py` normalizes each record to one row shape and detects the platform per record | `SKILL.md` (repo root), `scripts/analyze.py` (`_norm_reddit`, `_norm_x`, `load`) |

## 2. Reuse

### 2.1 Reuse as-is

| File | Use in the Bluesky module |
|---|---|
| `socialscope/salt.py` | One project salt. Bluesky ids hash as `acct_` + sha256(salt + DID)[:10], the same scheme as `history.score` and `common.H` |
| `socialscope/signals.py`: `interval_cv`, `hour_entropy`, `dormancy_then_burst`, `entropy_share`, `ai_style_score` | Take plain timestamps or text, so they work on Bluesky posts unchanged. (`account_id_number`, `DEFAULT_NAME`, `FARM_SUBS` are Reddit-only) |
| `socialscope/sources.py`: `find`, `DOMAINS` | State-media link matching on post text and facet links |
| `scripts/repull_run/anchors.py`: `assign_control_anchors` | Matched anchors for unlabeled accounts. It only needs group names and timestamps |
| `scripts/repull_run/common.py`: `wilson` | Intervals on rates |
| `scripts/dgg_live_logger.py` | Pattern for `collect/jetstream.py`, not an import: reconnect loop, the silent-connection watchdog, `sessions.jsonl` gap log, `status.json`, gzip at rollover, the systemd unit. Its two bug comments (pings, the 13-hour silent hang) apply to any websocket recorder |
| `socialscope/arctic.py`: `_get`, `_busy`, `Throttled`, `_resume` | Pattern for `collect/appview.py`: backoff on 429 and 5xx, resume from part files, `.done` markers |
| `.claude/skills/explain-analysis/` | Explainer page after Phase 7, as for every other analysis |
| Doc formats | Predictions: numbered, each with a confidence, plus a Scoring section. Results: Lead, then a `# / Prediction / Result / Verdict` table, a tally, Data used, caveats |

### 2.2 Generalize (make platform-agnostic, then both platforms call it)

| Today | Problem | Proposed shared home |
|---|---|---|
| `history._flags(items, thread_ts, as_of, first_ever, name)` | Reads Reddit keys directly: `subreddit`, `body`/`title`, `link_id`, `parent_id`, `score`, `author_fullname` | Keep `_flags` untouched (frozen v7.1). Add an adapter in `bluesky/features/shared.py` that maps a Bluesky post to this item shape, so the same code computes the same columns. Fields with no Bluesky meaning stay empty (section 3.4) |
| `prewindow.compute_prewindow_features(items, anchor)` | Same Reddit keys | Same adapter. Function is already pure |
| `repull_run/feats.py`: cut at anchor, `prewindow_features(exclude_removed=)` | `main()` is tied to cohort files and zips | Lift "cut history at anchor, compute features" into `socialscope/anchored.py` |
| `repull_run/score.py`: `oof_scores`, `fit_full`, bootstrap block, `prec`, `ci`, `pct` | One 190-line `main()`, group names hard-coded (`train_pos`, `test_ctl`...) | `socialscope/evalstats.py`: `bootstrap_recall_at_fpr(scores, labels, threshold_scores)`, `precision_at(rec, fpr, share)`, plus `wilson` moved here |
| `repull_run/knn_evidence.py` | Reads `accounts_<tag>.csv` and `model_<tag>.pkl`, same group names | `socialscope/knn.py`: `neighbours(Z_ref, ref_is_pos, Z_query, k)` and the calibration table |
| `brigade_alarm.py`: `cell_of`, `fit_profile`, `expected`, `thresholds`, `nb_sf`, leave-one-week-out loop | Closures inside `main()`, 18 subs hard-coded, "outsider" and "home sub" logic mixed in | `socialscope/alarm.py`: baseline profile fit, NB threshold, leave-one-out false-alarm rate, over any `(unit, hour) -> count` table. The home-community step stays in the Reddit script and is **not** ported: a per-account home would be a per-account faction label |
| `bb_inventory.build_inventory` (latest verdict per account wins) | Parses r/BotBouncer posts | Same idea for labels: latest `(src, subject, val)` event wins, `neg: true` clears it. New code in `bluesky/collect/labels.py`; the rule is shared, the parser is not |
| `analyze.py` `load()` | Detects Reddit vs X per record | Add `_norm_bsky` producing the same row. This is the skill's input adapter (spec section 9) |

Moving code out of `scripts/repull_run/` risks changing published numbers. Rule for Phase 1 onward: the Reddit
scripts keep working byte-for-byte (the Nov 9 rerun reproduced `results_repull.md` exactly; the refactor must too),
checked on the laptop before any Bluesky code depends on the shared module.

### 2.3 The "leakage audit" is these five checks

1. **Cut at the anchor.** Features for a labeled account use only items at or before its listing time. On Bluesky:
   the label's first `cts`.
2. **Same cap on the same side of the anchor.** The Reddit bug was a newest-first pull with a cap and no end date.
   See 3.5: `getAuthorFeed` has exactly this shape.
3. **Matched anchors for controls**, drawn from the positives' anchor dates.
4. **Never model what the label causes.** `pw_removed_share` is recorded but kept out of the model, because removals
   follow the listing. Bluesky equivalents: deletions, takedown state, label-driven hiding, blocks received after a
   label.
5. **Thresholds from training-side cross-validation**, never from the test controls; and the `NOVOL` ablation with
   the Spearman coupling table, to catch features that only measure how much history the cap let through.

## 3. Conflicts with the spec

Existing convention wins unless I argue otherwise. Where I argue, it says so.

### 3.1 Tiers: three meanings already exist; A/B/C is a fourth

| Existing "tier" | Values | Meaning |
|---|---|---|
| `analyze.py` | lead / likely / high | How many signal families fired |
| `history.score` | primary / primary+secondary | Which frozen rules fired |
| Bot Bouncer verdict | banned / pending / organic / unflaired / purged | The outside label |

The spec's A/B/C is a label-source grade, closest to the Bot Bouncer verdict. Proposed mapping, stored in a column
named `label_tier` (never plain `tier`, which is already a column in `accounts.csv`):

| Spec | Reddit analogue | Group name in code |
|---|---|---|
| A | banned | `pos` |
| B | pending: a lead, scored separately, never a positive | `pending` |
| C | detector flags, shortlist | not a label; a feature at most |
| Control | unlisted random in-sub accounts | `ctl` |

### 3.2 Naming: the spec is looser than CLAUDE.md rule 5

Rule 5 was written for Reddit and says a bot is named only when Bot Bouncer has banned it, rechecked within 7 days,
attributed to Bot Bouncer with a link, and removed if the listing is reversed. The spec makes all of Tier A nameable.
Three gaps:

- **Hijacked accounts.** Rule 5: only bot-period posts appear next to a name; the earlier history was a real
  person's. The Matryoshka accounts are hijacked dormant accounts, so this applies to exactly the set the spec most
  wants to name. Keep the rule.
- **Attribution and recheck.** Name as "labeled `spam` by Bluesky moderation" or "named in the Clemson report",
  with a link, never as our verdict. Labels can be retracted (`neg`), so the 7-day recheck carries over.
- **"No longer resolving with takedown error"** is weaker than a label: it does not say why. I would keep those in
  Tier A for scoring and not name them.

Rule 5 does not mention Bluesky at all. It needs a line from the owner before anything is named (decision 1). Until
then every DID and handle is hashed in outputs, as Reddit usernames are. Target accounts are named as targets.

### 3.3 Cross-platform links vs "no identity work"

README rule 5, SKILL.md rule 5 and CLAUDE.md rule 5 all forbid linking an account to accounts on other platforms.
The spec records Reddit/X links and says "only domain handles or bio cross-links count" as identity. Proposed: keep
`facet_links` (domains and URLs, needed for the link-share features) and `domain_handle` as a boolean. Build no
table that maps a Bluesky account to a Reddit or X account in v1.

### 3.4 "Shared features (same names as Reddit)": five of eight have no Reddit column

| Spec feature | Existing column | Note |
|---|---|---|
| Account age | `true_age` (days from first item ever to anchor), `hist_age` (first pulled item to anchor) | Bluesky: PLC creation date gives `true_age` directly |
| Posts/day | none | Nearest: `items`, `log_items`, `pw_posting_rate_ratio`. New column needed |
| Inter-post interval mean and variance | `interval_cv`, `share_gaps_under_60s` | CV only. Mean and variance separately would be new |
| Reply share | `top_level_share` (share of comments that are top-level), `n_comments` / `n_cut` | Different quantity. Bluesky reply share maps to comments / items |
| Replies to higher-follower accounts | none | Reddit has no followers. Bluesky-only |
| Original-post count | `n_posts` | |
| Longest dormant gap | `longest_gap_days`, `pw_longest_silence_before_window` | |
| Low-credibility domain share | none | Only `state_media_links` (18 outlets) and the retired `scam_domain` rule. A domain list has to be chosen and cited |

The full existing schema, for `features/shared.py`:

- **Identity and bookkeeping:** `account`, `group`, `cohort_source`, `flair`, `anchor_utc`, `anchor_src`, `n_cut`,
  `n_posts`, `n_comments`, `n_total_pulled`, `n_after_anchor`, `tier`, `flag_list`, `home_sub`, `insub_items`.
- **Model inputs, history (`feats.NUM`):** `bot_score`, `items`, `comments`, `subs`, `longest_gap_days`,
  `interval_cv`, `share_gaps_under_60s`, `farm_share`, `self_repeat`, `ai_style_share`, `top_sub_share`,
  `sub_spread`, `threads_revisited`, `top_level_share`, `words_median`, `words_cv`, `quoted_share`,
  `ai_vocab_share`, `md_share`, `sentence_cv`, `state_media_links`, `political_early`, `political_late`.
- **Model inputs, other:** `hist_age`, `true_age`, `sh`, `sb`, `primary`, `log_items`.
- **Model inputs, 30 days before the anchor:** `pw_window_items`, `pw_earlier_items`, `pw_new_subreddit_share`,
  `pw_distinct_subs_per_item`, `pw_posting_rate_ratio`, `pw_median_length_ratio`, `pw_link_share_change`,
  `pw_short_comment_share`, `pw_score_median_change`, `pw_longest_silence_before_window`. Recorded, not modeled:
  `pw_removed_share`.
- **Computed by `history.score` but not in the current model:** `median_reply_minutes`,
  `share_replies_under_10min`, `first_seen`, `last_seen`, `first_ever`, `top_subs`. Use these two reply-timing names
  for Bluesky reply latency so starter prediction 4 compares like with like.

**The subreddit problem.** Thirteen model inputs depend on subreddits (`subs`, `farm_share`, `top_sub_share`,
`sub_spread`, `pw_new_subreddit_share`, `pw_distinct_subs_per_item`, `sh`, `sb`, `political_*` in part, `primary`
through the tourist rule, `bot_score`). `pw_new_subreddit_share` and `sb` were the top two importances in the
re-pull. Bluesky has no subreddit. Four more need per-item scores. So "apply the Reddit model" has two readings,
and I propose reporting both:

- **(a) Frozen model**, unmappable inputs left empty (the model accepts missing values). Mostly measures how much
  the model leaned on subreddits.
- **(b) Retrained on Reddit using only columns that exist on both platforms**, then applied to Bluesky. This is
  the fair answer to question 3 of the spec.

Starter prediction 6 says "karma-like features have no replacement and their loss costs the most recall". The
re-pull importances suggest the subreddit-novelty features will cost more. The owner's call whether to edit it before
it is frozen.

The model file is `~/socialscope_data/repull/out/model_repull.pkl` on the laptop. It is a pickle and loads only
under the scikit-learn version that wrote it; record that version in Phase 1.

### 3.5 History cap

`history_posts_per_account`: the Reddit cap is the **newest 1,000 posts and newest 1,000 comments ending at the
anchor** (`pull.py`, `--max-items 1000`). Proposed for Bluesky: 1,000 top-level posts and 1,000 replies, ending at
the anchor.

`getAuthorFeed` pages newest-first with no end date. That is the pull that produced the Reddit cap artifact: a
labeled account that kept posting loses pre-label items to the cap. To check in Phase 1: `com.atproto.repo.
listRecords` on the account's PDS pages by record key, which is time-ordered, so a pull can start at the anchor.
If that works it should replace `getAuthorFeed` for histories.

### 3.6 block_surge: "Poisson baseline, p < 0.001" already failed here

`docs/brigade-alarm-results.md`: plain Poisson fired on 3.5% of normal hours, 35 times its nominal rate. The frozen
v2 rule is: negative binomial 99.9th percentile on distinct accounts, at least 5 accounts, expected count scaled by
total activity that hour, baseline from an hour-of-day by weekday/weekend profile, false-alarm rate measured
leave-one-week-out. Proposed: block_surge uses that rule on distinct blockers per target per hour. A 7-day baseline
gives 7 points per hour-of-day cell, so the first usable alarms come in week 2 at the earliest, and with a 3-week
window there are about two test weeks.

### 3.7 Predictions: timing and file names

- CLAUDE.md rule 3: commit predictions **before running or reading the data**. The spec puts predictions at Phase 5,
  after the pilot (Phase 1) and after features and detectors run on pilot data (Phases 3-4). Proposed: commit
  predictions before the pilot is read, and declare the pilot days development data, outside the test window.
- Names: `docs/bluesky-politics-predictions.md` and `docs/bluesky-politics-results.md`, not `reports/PREDICTIONS.md`.
  The `*-predictions.md` / `*-results.md` pair is what rule 3 and the explainer skill expect.
- The six starter predictions carry no numbers or confidence. Existing predictions give ranges and a confidence
  each, which is what makes them scorable.

### 3.8 The window starts tomorrow and no collector exists

Window: Nov 20 to Dec 11. Today is Nov 19. Threads, author feeds, profiles, PLC logs and labels can be fetched
afterwards. The Jetstream part cannot be recovered beyond the stream's short replay buffer (length to confirm in
Phase 1): likes, follows, blocks and deletes outside it are gone. `like_farm`, `follow_burst` and `block_surge`
depend on it unless Constellation can backfill them, and the delete rule depends on it entirely. Options are in
decision 2.

### 3.9 Environment and layout

| Spec | Existing convention | Proposed |
|---|---|---|
| Collect on Victoire (Windows) or the Linux HP | The laptop runs every job; long jobs under nohup + systemd-inhibit with a jobs.tsv line (rule 6); standing loggers as systemd --user services (rule 8) | Linux laptop for collection. Rule 6 cannot be met on Windows. Paths still use pathlib |
| `data/bluesky/{raw,processed,exports}` in the repo, gitignored | Data lives in `~/socialscope_data`, outside the repo. Repo `data/` holds small committed files. `.gitignore` does not cover `.parquet`, `.jsonl.gz` or `.csv` | `~/socialscope_data/bluesky/`, via the `SOCIALSCOPE_DATA` override in `common.py`. Add the missing ignore patterns anyway |
| `bluesky/tests/`, pytest | `test/`, unittest, plus `test/make_fake*.py` synthetic generators | `test/test_bsky_*.py` written as unittest classes (pytest runs them too) and `test/make_fake_bsky.py` for the planted-pattern detector tests |
| pandas, pyarrow, duckdb, atproto, httpx | Stdlib csv/json plus numpy, scipy, scikit-learn. No requirements file exists. The laptop is on Python 3.14 after two forced OS upgrades that broke every venv | Add `bluesky/requirements.txt` with pinned versions and its own venv. Confirm each library installs on 3.14 before committing to it. Jetstream is plain JSON, so the recorder needs only `websockets`, which `liveenv` already has |
| `bluesky/` top-level tree | Library in `socialscope/`, run scripts in `scripts/<run>/` | Keep the spec's `bluesky/` tree for platform code; shared code goes to `socialscope/` (2.2); docs go to `docs/` |
| Status | Status servers serve only their own status folder; ports 8765-8767 taken (rule 7) | Recorder writes `status.json` to its own folder; port 8768 if a page is wanted |

### 3.10 Validity risks carried over from the Reddit lessons

- **Takedowns leave no history.** A `!takedown` account's posts are no longer served, so most of Tier A as defined
  will have nothing to score unless the recorder caught it first. The scorable Tier A is the labeled accounts
  still online, a biased subset. Report both counts, as `comparison.md` reports "accounts with no history found".
- **Positives and controls from the same population** (the failed sitewide test). The primary test should be Tier A
  accounts that replied in the target threads against random unlabeled repliers from the same threads. Labeler-wide
  known-bad sets and Bluesky-verified accounts are a different population: useful as reference rows, wrong as the
  main positive and negative classes. Verified accounts would be separated by follower count alone.
- **Expect few in-thread positives.** With 3,000-5,000 repliers and moderation-label recall near 0.22, in-thread
  Tier A may be in the tens. The re-pull had 189 test positives and still got a 20-point interval on recall.
  Decide in advance what count is too few to report a recall at all.
- **Unlabeled is not human.** Same caveat as "unlisted by Bot Bouncer"; the spec already says this for Tier A recall.
- **Account-level vs post-level labels.** Bluesky labels attach to an account or to single posts. The rule for
  when post labels make an account Tier A needs fixing before any label is read.

## 4. Things the spec gets right that are new to socialscope

Honoring deletes; whitelisting behavioral label values so faction does not leak into bot labels; aggregate-only
blocks and list memberships; side as a thread-level grouping variable only; bridged accounts as their own class;
subtracting starter-pack joins from follow bursts. None conflict with existing rules.

## 5. Decisions for the owner

1. **Naming rule for Bluesky** (3.2). Recommended: add a Bluesky line to CLAUDE.md rule 5: nameable only when an
   outside labeler or published report names the account; attributed and linked; rechecked within 7 days; hijacked
   accounts show bot-period posts only; takedown-without-label accounts are scored, not named. Everything else hashed.
2. **Window** (3.8). Recommended: move the window to start the day the recorder passes its 24-hour pilot, and keep
   it 3 weeks. Alternatives: keep Nov 20 and accept that early days have threads and histories but no likes, follows,
   blocks or deletes; or start a bare recorder now and treat everything before the pilot passes as best-effort.
3. **Predictions timing and file names** (3.7). Recommended: commit `docs/bluesky-politics-predictions.md`, with
   numbers and confidence levels, before the pilot data is read; the pilot is development data.
4. **Transfer test** (3.4). Recommended: report both the frozen model and the shared-columns retrain.
5. **Primary comparison** (3.10). Recommended: in-thread Tier A vs in-thread unlabeled repliers with matched
   anchors; labeler-wide sets and verified accounts as reference rows.
6. **block_surge rule** (3.6). Recommended: the frozen v2 negative-binomial rule, not Poisson.
7. **Where it runs and where data lives** (3.9). Recommended: Linux laptop, `~/socialscope_data/bluesky/`, own venv.
8. **Cross-platform links** (3.3). Recommended: keep links and domains, build no account-to-account mapping.
9. **Shared-module refactor** (2.2). Recommended: yes, with the byte-for-byte check on the Reddit results first.
   The alternative is that Bluesky code imports nothing from `scripts/` and reimplements the statistics, which the
   spec forbids.
