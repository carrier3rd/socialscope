# Proposal: shared modules for the statistics (not started; waiting for the owner's go-ahead)

Nov 19, 2026. The owner's decision 9: not yet; propose separately. Nothing in Phase 1 depends on this. The
collectors import nothing from `scripts/` or `socialscope/`.

## Why it comes up

Phases 4 and 6 need four things that today live inside Reddit run scripts: the negative-binomial alarm, the
bootstrap recall and AUC intervals, the kNN evidence, and "cut history at the anchor, then compute features".
The spec says shared code is shared, not copied. The alternative is to reimplement them under `bluesky/`.

## What would move

| New module | From | What |
|---|---|---|
| `socialscope/evalstats.py` | `scripts/repull_run/score.py`, `common.py` | `wilson`, `bootstrap_recall_at_fpr`, `precision_at` |
| `socialscope/knn.py` | `scripts/repull_run/knn_evidence.py` | `neighbours`, the calibration table |
| `socialscope/alarm.py` | `scripts/brigade_alarm/brigade_alarm.py` | profile fit, NB threshold, leave-one-week-out rate, over any `(unit, hour) -> count` table. The home-community step stays in the Reddit script |
| `socialscope/anchored.py` | `scripts/repull_run/feats.py` | cut at anchor, then features |

`history._flags` and `prewindow.compute_prewindow_features` stay untouched (frozen v7.1). Bluesky reaches them
through an adapter in `bluesky/features/shared.py`.

## Order and safeguard

1. One module per commit, starting with `evalstats.py` (smallest).
2. In each commit the Reddit script imports the moved functions and its own code is deleted, so there is one copy.
3. After each commit the laptop session reruns the script that used the code and compares outputs with the
   current ones byte for byte: `results_repull.md` and per-account scores for `score.py` and `knn_evidence.py`;
   the Nov 3-9 alarm list for `brigade_alarm.py`. Any difference: revert that commit.
4. Bluesky code starts importing a module only after its check has passed.

## Cost and risk

About 400 lines move; no logic changes. The risk is a changed number in a published result, which step 3 exists
to catch. It needs laptop time for three reruns. If the answer is no, Phases 4 and 6 copy the four pieces into
`bluesky/` with a note saying where each came from, and the spec's "not copied" rule is waived.

## Decision needed

Go ahead, go ahead for some modules only, or copy instead.
