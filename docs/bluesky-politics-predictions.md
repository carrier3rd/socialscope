# Bluesky politics module: predictions

Written Nov 19, 2026 by the cloud session; approved by the owner the same day. Never edited after this commit;
additions go at the end as dated addenda. Results go in `docs/bluesky-politics-results.md`, misses included.

Written before any Bluesky reply thread, like, follow, block, label or account history was read. What had been
read: the spec, RECON.md, the socialscope Reddit results, and config lookups made on Nov 19 (handle resolution,
labeler DID documents, the public profiles of candidate target accounts, including their follower and post
counts). Those follower counts inform prediction 1 and are stated there.

Predictions 1 to 6 are the spec's starter predictions (section 10), made scorable. The confidence is mine in
the statement as the spec words it. Where I expect the spec's version to miss, I say so and give my own.

## Data and terms (frozen)

- **Pilot days are development data.** Detector thresholds may be tuned on them. Nothing from them is scored.
- **Test window:** 21 days, starting the day the recorder passes its 24-hour pilot (`window` in
  `bluesky/config/targets.yaml`).
- **Sides:** the target lists in `targets.yaml` as committed when the window starts. Side is a property of the
  thread, never of an account.
- **In-thread replier:** an account with at least one reply, in the window, in a thread started by a target or
  directly to a target. Targets themselves are excluded.
- **Tier A:** a Bluesky moderation label `spam`, `impersonation` or `!takedown` on the account, not negated; or
  an account named in the Clemson, ISD, AFP or CheckFirst reports. Labels on single posts do not make an account
  Tier A. Accounts that stopped resolving without a label are counted separately. antibot4navalny list
  membership is not Tier A unless the owner rules it in before the window starts.
- **Tier B:** a whitelisted Skywatch behavioral label on the account, not negated (list in `targets.yaml`).
- **Labeled:** Tier A or Tier B, as the labels stand 7 days after the window ends.
- **Primary comparison:** in-thread Tier A against in-thread unlabeled repliers with matched anchors
  (`assign_control_anchors`). A labeled account's features use only activity before its first label.
- **Too few to score:** with fewer than 30 in-thread Tier A accounts that still have a history, no recall or AUC
  is reported for Tier A; counts only, and the predictions that need them are scored "not testable".
- **block_surge:** the frozen v2 rule from `docs/brigade-alarm-v2-predictions.md` applied to distinct blockers
  per target per hour: negative binomial 99.9th percentile, at least 5 accounts, hour-of-day by weekday/weekend
  baseline. Week 1 of the window is baseline only; alarms are counted in weeks 2 and 3.
- **Transfer:** two models, both reported. (a) Frozen v7.1 (`model_repull.pkl`) with inputs that don't exist on
  Bluesky left empty. (b) A retrain on the Reddit re-pull training set using only columns that exist on both
  platforms, scored on the Reddit re-pull test set and on Bluesky.

## Predictions

| # | Prediction | Range | Confidence |
|---|---|---|---|
| 1 | **Side.** The share of distinct in-thread repliers who are labeled is higher in progressive threads than in government/right threads. | Progressive 0.3% to 2.0%; government/right 0.1% to 1.5%; ratio between 1.2 and 4. | 60% for the direction; 35% that both shares and the ratio land in range |
| 2a | **Block surges, count.** The alarm fires on few target-hours. | 3 to 25 alarms across all targets in weeks 2 and 3. | 50% |
| 2b | **Block surges are organic.** Most alarm hours follow a big post: the alarm hour falls within 6 hours after a post by that target that is in the target's top 10% by reply count for the window. | At least 70% of alarms. | 65% |
| 2c | **Not label clusters.** Labeled accounts are no larger a share of blockers in alarm hours than in that target's other hours. | Difference in share under 1 percentage point, or lower in alarm hours. | 75% |
| 3a | **Like-farm signature appears.** At least one group of 50 or more accounts whose likes of target posts overlap almost completely: every pair in the group has Jaccard overlap of 0.8 or more over the target posts they liked, each account liked at least 5 target posts, and the posts span at least 3 targets. | At least 1 such group. | 40% |
| 3b | **Smaller than claimed.** The largest such group is well under the 8,515 accounts of the unverified Leaflet claim. | Largest group under 2,000 accounts (true by default if none is found). | 90% |
| 4a | **Reply bots are missed most.** Among in-thread labeled accounts, split into reply-only accounts (at least 90% of their pre-label posts are replies) and the rest, the frozen model's recall at the 5% line is lower for the reply-only group. | Lower by 10 points or more. | 45% |
| 4b | **Reply latency is the strongest new feature.** In a Bluesky model built from shared columns plus Bluesky-only features, a reply-latency feature (`median_reply_minutes` or `share_replies_under_10min`) has the largest permutation importance among the features the Reddit model does not use. | Rank 1 among those features. | 30% |
| 5 | **Dormant hijacks are rare.** In-thread repliers matching the dormant_hijack rule: at least 180 days of silence, then a handle, PDS or key change in the PLC log within 30 days before posting resumes, then at least 10 replies in target threads. | 10 to 99 accounts, and under 1% of in-thread repliers. | 50% for the range; 85% for under 1% |
| 6a | **Shared features keep most of their value.** Model (b), on the Reddit re-pull test set, keeps most of the full model's recall at the 1% line (CV threshold; the full model's was 62%). | Model (b) recall 37% to 55%, which is 60% to 89% of the full model's. | 50% |
| 6b | **Karma-like features cost the most** (the spec's wording). Dropping the score-based inputs (`pw_score_median_change` and any other input that needs per-item scores) from the full Reddit model loses more recall at 1% than dropping the subreddit-based inputs. | Score group loss greater than subreddit group loss. | 20% |

**Where I disagree with the spec's version.**

- **6b.** I expect the opposite: the subreddit-based inputs cost more. In the re-pull, the top two importances
  were `pw_new_subreddit_share` and `sb`, both subreddit-based. My prediction: dropping the subreddit group loses
  at least 8 points of recall at 1% on the Reddit test set, and at least twice what dropping the score group
  loses. Confidence 65%.
- **1.** The two sides are not comparable in size: on Nov 19 the progressive targets had 105k to 2.2M followers
  and the government/right candidates 400 to 16,500. A difference in labeled share may be a difference in thread
  size. Alongside prediction 1 the results will report the same comparison restricted to threads with 20 to 500
  replies on both sides. I expect the direction to hold there too, at 50%.

## Also recorded (not in the spec's six)

| # | Prediction | Range | Confidence |
|---|---|---|---|
| 7 | **Few positives.** In-thread Tier A accounts that still have a history to score. | 10 to 150. Under 30 means no Tier A recall is reported. | 60% for the range; 40% that it is under 30 |
| 8 | **Takedowns leave nothing.** Of in-thread accounts that become Tier A through `!takedown` or stop resolving, the share with no retrievable history outside our own recording. | At least 80%. | 70% |
| 9 | **Transfer is weak.** AUC on Bluesky, in-thread labeled (Tier A plus B) against matched unlabeled repliers. | Frozen model (a): 0.50 to 0.65. Shared-columns model (b): 0.58 to 0.75. (b) above (a). | 55% for each range; 70% for the order |
| 10 | **Faction values dominate Skywatch volume.** Of all Skywatch labels in the replay, the share whose value is outside the behavioral whitelist (counted by value, subjects never stored). | Over 50%. | 55% |

## What would not count

- A low recall against Tier A is partly missing labels: Bluesky moderation labels have precision about 0.84 and
  recall about 0.22 (Singh et al.). Unlabeled is not human. Every result will say so.
- Prediction 3a found is a signature consistent with the claim, not confirmation of it; not found in 21 days
  around 21 targets is not evidence that no farm exists. No target is named on it either way.
- If the government/right list changes after this file is committed, the change is recorded in a dated addendum
  before the window starts, and prediction 1 is scored on the list as it stood at the start of the window.

## Scoring

In `docs/bluesky-politics-results.md`: one row per numbered prediction, hit / miss / partial / not testable, with
the numbers. A prediction with a direction and a range is a hit only if both hold, partial if one does.
Bootstrap intervals (2,000 resamples over accounts, threshold recomputed in each) on every recall and AUC.
Misses stay in.
