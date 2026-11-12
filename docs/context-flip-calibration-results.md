# Context-flip calibration: results

Scored 2026-11-12 against `context-flip-calibration-predictions.md` (frozen 17:44 UTC, sha256 of the final version
with its pre-coding addendum: 182639f7...bddf36; unchanged since). Analysis output: `docs/context-flip-calibration-analysis.txt`.
Scripts: `scripts/context_calib/` (`parse.py`, `build.py`, `analyze.py`; Gemini arm: `gemini_run.py`,
`gemini_analyze.py`). Item text and per-item codes are private sample data and are not committed.

**Score: 3 held, 4 missed, 1 held but uninformative (n=4).**

## What ran
- 150 socialscope stance items (113 replies + 37 top-level placebo), coded P/A/B/N with the sarcasm-aware prompt.
- C0 (comment only) and C1 (comment + parent), two independent runs each, four separate Claude subagents, each blind
  to the other condition, shuffled order. All 4 x 150 rows returned.
- **Coder caveat:** the coder is Claude (this session's model) running as subagents, not socialscope's Gemini coder
  or rhetoric.py's Batch pipeline. No human codes, so this measures movement, not correctness.

## Numbers (replies, n = 113)
| measure | result | 95% CI |
|---|---|---|
| Context flips, C0r1 vs C1r1 (primary) | 5 / 113 = 4.4% | 1.9-9.9% |
| Context flips, C0r2 vs C1r2 (replicate) | 10 / 113 = 8.8% | 4.9-15.5% |
| Rerun noise, C0 | 8 / 113 = 7.1% | 3.6-13.4% |
| Rerun noise, C1 | 5 / 113 = 4.4% | 1.9-9.9% |
| Placebo (top-level, identical input), C0r1 vs C1r1 | 2 / 37 = 5.4% | 1.5-17.7% |
| Context-attributable (primary minus mean rerun) | **-1.3 points** | |
| Robust flips (same code in both runs of each condition, different across) | **2 / 103 = 1.9%** | |

Code mix barely moves: C0r1 P56 A47 N46 B1; C1r1 P56 A47 N46 B1.

## Predictions
1. **Missed.** Context flip rate 4.4% (replicate 8.8%), under the 15-35% range.
2. **Held.** Rerun noise 7.1% and 4.4%; placebo 5.4%; all <= 10%.
3. **Missed.** Context-attributable flips are -1.3 points: the reply flip rate is inside the noise floor.
4. **Held but uninformative.** N -> polar 3, polar -> N 1 (3:1), but on 4 flips.
5. **Held.** Cross-polar P <-> A was 1 of 5 flips (20%).
6. **Held in direction, too small to rely on.** '>'-quote replies flipped 2/18 (11%) vs 3/95 (3%), 3.5x, n = 5 flips.
7. **Missed.** VIEW = echo on replies: 2 in C0, 2 in C1.
8. **Missed (tiny n).** Truncated comments flipped 2/26 (8%) vs 3/87 (3%).

## The two robust flips
Both are the kinds the reports predicted:
- **Item 301 (N -> P):** a reply that questions the parent's claim ("How is it hurting Ukraine?"). Alone it is a bare
  question. With the parent, it is a rebuttal on Ukraine's side.
- **Item 779 (A -> P):** the comment opens with a '>' quote of the parent's Israel-Nazi comparison and rebuts it.
  Without the parent the coder read it against Israel, even with the '>' rule in the prompt. With the parent it
  read as a rebuttal.

## What this means
- For this sample (comments sampled because they *name the subject*), a frontier Claude coder rarely needs the parent
  to code stance: flips are at the noise floor. This matches the random-sample toxicity studies (~5%, Pavlopoulos et
  al. 2020), not the hate-word-seeded Reddit study (38.3%, Yu et al. 2022). Sampling decides the flip rate.
- The noise floor is real: 4-7% of codes change on an identical rerun. **Any single with/without comparison under
  ~10% can't be told from noise without reruns.** The skill's calibration step needs two runs per condition.
- The flips that do survive are question-replies and quote-rebuttals, so tier-0 cues for "reply opens with a
  question" and "comment opens with a '>' quote" are worth keeping.
- This does **not** say the parent is useless for socialscope: the Nov 2 study found the parent decided most of the
  *human* coder's errors. Whether Claude without the parent is *right* needs human codes on the flipped and stable
  items.

## Deviations from the plan
- 113 replies, not 300, and no rhetoric.py items: the 300-reply sample and rhetoric.py's coded chat are only on the
  laptop, and the Drive Reddit zips are too big for the Drive connector. The laptop runner in the skill
  (`skills/context-gathering/scripts/flip_calibration.py`) runs the same design on both with the Batch API.
