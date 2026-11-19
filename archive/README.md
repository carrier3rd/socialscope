# Archive

Finished one-off scripts, moved here on Nov 19, 2026 so `scripts/` holds only what is still run. Nothing was
changed inside them. Their results are written up in `docs/`, and those docs (including frozen predictions files)
still cite the old paths, so here is the map. Paths and imports inside these scripts assume their old location: to
rerun one exactly as it was, check out commit `29e3356` (the last commit with them at the old paths).

| Old path | Now | Used for |
|---|---|---|
| `scripts/insub_run/build.py` | `archive/scripts/insub_run/build.py` | In-subreddit training study (docs/insub-training-predictions.md, forward-test-predictions.md) |
| `scripts/insub_run/feats.py` | `archive/scripts/insub_run/feats.py` | In-subreddit training study (docs/insub-training-predictions.md, forward-test-predictions.md) |
| `scripts/insub_run/score.py` | `archive/scripts/insub_run/score.py` | In-subreddit training study (docs/insub-training-predictions.md, forward-test-predictions.md) |
| `scripts/insub_run/score_fwd.py` | `archive/scripts/insub_run/score_fwd.py` | In-subreddit training study (docs/insub-training-predictions.md, forward-test-predictions.md) |
| `scripts/integrity/cmp_pulls.py` | `archive/scripts/integrity/cmp_pulls.py` | Pull integrity checks after the Nov 9-11 RAM faults |
| `scripts/integrity/week_records.py` | `archive/scripts/integrity/week_records.py` | Pull integrity checks after the Nov 9-11 RAM faults |
| `scripts/pull_context_subs.py` | `archive/scripts/pull_context_subs.py` | Context-subreddits pull (docs/context-subs-predictions.md) |
| `scripts/pull_oct27_topup.py` | `archive/scripts/pull_oct27_topup.py` | One-off top-up pull for the Oct 27 week |
| `scripts/sarcasm_ctx.py` | `archive/scripts/sarcasm_ctx.py` | Sarcasm-prompt study (docs/sarcasm-prompt-predictions.md) |
| `scripts/train_run/clf.py` | `archive/scripts/train_run/clf.py` | Nov 2 training run (superseded by the v7.1 re-pull, `scripts/repull_run/`) |
| `scripts/train_run/ext.py` | `archive/scripts/train_run/ext.py` | Nov 2 training run (superseded by the v7.1 re-pull, `scripts/repull_run/`) |
| `scripts/train_run/hij.py` | `archive/scripts/train_run/hij.py` | Nov 2 training run (superseded by the v7.1 re-pull, `scripts/repull_run/`) |
| `scripts/train_run/insub.py` | `archive/scripts/train_run/insub.py` | Nov 2 training run (superseded by the v7.1 re-pull, `scripts/repull_run/`) |
| `scripts/train_run/pred.py` | `archive/scripts/train_run/pred.py` | Nov 2 training run (superseded by the v7.1 re-pull, `scripts/repull_run/`) |
| `scripts/train_run/split.py` | `archive/scripts/train_run/split.py` | Nov 2 training run (superseded by the v7.1 re-pull, `scripts/repull_run/`) |
