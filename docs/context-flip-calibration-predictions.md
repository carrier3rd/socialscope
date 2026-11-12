# Context-flip calibration: predictions (written before any coding)

Written 2026-11-12 by the cloud Claude session, before any item was coded in this study. Never edited after coding
starts; additions go at the end as dated addenda. Results go in `context-flip-calibration-results.md`, misses included.

Disclosure: while checking the data format I read the text (not any codes) of the 50 items in part 1. I have not
seen any code for any item in this study, and the old Gemini/human codes are not available in this session.

## Data
socialscope's sarcasm-prompt item set (Nov 2 2026, Drive `gemini/gemini_sarcasm_part{1,2,3}.txt`): 150 Reddit
comments with subject (Ukraine / Israel / Hasan), usernames masked, glossary notes where present.
- 113 replies with parent text (37 parents truncated at ~506 chars; 32 comments capped at 600 chars).
- 37 top-level comments with no parent: a **placebo** set, since both conditions give them identical input.

The planned 300 socialscope replies and a few hundred rhetoric.py items are not reachable from this session: the
Reddit zips on Drive are too large to load through the Drive connector, and rhetoric.py's coded items live only on
the laptop (`archive/rhetoric/`). This is a deviation from the plan; see the results file for the laptop runner.

## Design
- Rubric: the Nov 2 sarcasm-aware stance prompt (VIEW own/echo/unclear, then code P/A/B/N toward the subject),
  unchanged except that condition C0 has no PARENT line.
- C0 = subject + comment + glossary. C1 = C0 + parent comment.
- Coder: Claude (this session's model) as separate subagents, one per run, each seeing only its own condition's file.
  Two independent runs per condition, each with a different item order (seeds 11, 12 for C0; 21, 22 for C1).
- Primary flip measure: C0 run 1 vs C1 run 1. Noise floor: C0 run 1 vs C0 run 2, and C1 run 1 vs C1 run 2.
  Placebo: C0 vs C1 on the 37 top-level items (identical input), which should look like noise.
- No human ground truth here, so this measures how often and which way the *model's* label moves, not which
  label is right.

## Predictions
1. Context flip rate on the 113 replies (C0r1 vs C1r1): **15-35%**.
2. Noise floor: same-condition rerun disagreement on replies **<= 10%** in both conditions; placebo flip rate **<= 10%**.
3. Context-attributable flips: reply flip rate minus the mean of the two rerun rates **>= 10 points**.
   Falsified if the reply flip rate is within 5 points of the noise floor.
4. Direction: among reply flips, **N -> polar (P, A or B) outnumbers polar -> N by at least 1.5 : 1**
   (from Yu et al. 2022 Table 3; the reversed P11 in "Predicting context label flips").
5. Cross-polar reversals (P <-> A) are **<= 25%** of reply flips.
6. Replies whose comment contains a ">" quote flip at **>= 1.5x** the rate of replies without one.
7. VIEW = echo is assigned **more often in C1 than in C0** on replies.
8. Truncated comments (600-char cap) flip at a rate **no higher** than untruncated ones (length is not the driver;
   Bourgeade et al. 2024).

Scoring rule: each prediction is Held / Missed / Not scorable, with the counts, in the results file.

## Addendum 2026-11-12 (before any coding)
Two prompt details differ from the Nov 2 file, in both conditions alike: (a) the ">" rule from the Nov 2 results
("text after > is quoted from someone else and is never the commenter's view") is added, as that file said future
coding would; (b) the literal_vs_intended column is dropped to keep outputs short. Predictions above are unchanged.

## Addendum 2026-11-12: Gemini arm (written before any Gemini call on these items)
Claude's results are already scored and known to me; these predictions are written with that knowledge.
Same 150 items, C0/C1, two runs each, coder `gemini-4-hydrogen` (the only Gemini model on this key that returns
token logprobs), default sampling. To get a label-token probability, the prompt asks for **one letter only**
(P/A/B/N), so the VIEW step is dropped in this arm. Per item and condition: the probability of each label at the
label token (from top-5 logprobs, renormalised over P/A/B/N), and the signed shift
P-CXMI = log p(y_C1 | C1) - log p(y_C1 | C0).

G1. Gemini context flip rate on replies (C0r1 vs C1r1) <= 12%.
G2. Gemini rerun noise on replies <= 10% in each condition.
G3. Median total-variation shift of the label distribution (C0 -> C1) is larger on replies than on the placebo
    top-level items (which get identical input).
G4. Replies whose Gemini label flips have a larger mean |P-CXMI| than replies that don't.
G5. Gemini and Claude agree on >= 75% of C1 run-1 codes (all 150 items).
G6. On Claude's two robust flips (items 301, 779), Gemini's probability of P rises from C0 to C1.
G7. Replies where Gemini is unsure in C0 (top label prob < 0.9) flip at >= 2x the rate of confident ones.
