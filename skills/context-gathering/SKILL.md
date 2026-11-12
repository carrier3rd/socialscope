---
name: context-gathering
description: Decide, per item, whether more context would change a label and which way, then fetch only the context that matters. Use when coding or classifying short texts that may depend on surrounding discourse (Reddit replies, live chat, stream transcripts, quotes, sarcasm, dogwhistles, stance, endorse-vs-quote), when building an LLM coder or RAG step that pulls a context window, or when asked whether a fixed context window is enough. Also use before trusting any coder that sees context, to run a with/without-context calibration, and when a large coding job should run on a cheap model first with only the uncertain items escalated to a stronger one.
---

# Context gathering: fetch where labels flip, not everywhere

The question to ask of every item is not "does this need more context?" but **"would context change *this* label,
and in which direction?"** The research behind this skill (see `references/evidence.md`) says:

- Context changes a **minority** of labels overall (~5% of toxicity labels in random samples), but a **large share
  of relational labels** (38.3% of Reddit hate/counter-speech labels changed once the parent was shown).
- The direction is predictable in shape: **context corrects what the surface suggests**. Loud, profane or
  quoted-looking items tend to get *cleared*; neutral-looking replies tend to become *polar* once you see what they
  answer.
- **An LLM's own judgment of whether it needs context is the weakest gate** (near-chance AUROC in Zhang & Choi 2025;
  κ 0.26 between two LLMs in Shi et al. 2026). Combine it with cheap structural signals.
- LLMs have their own direction effects: pulled toward their own prior verdicts and toward unanimous framing, but
  in one 2026 preprint Claude was *pushed away* from a single toxic parent (a toxic reply looked less toxic next to
  it), the opposite of human raters. Measure this per project; don't assume a direction.

Never present a number from `references/evidence.md` as established unless it is tagged verified there.

## Procedure

Run the tiers in order. Stop as soon as an item is decided. Log which tiers ran.

### Tier 0: deterministic triage (no LLM call)

1. **Serialize every item the same way**: id, timestamp, speaker, reply-to / @-target, quoted spans, then the target
   text **last** (closest to the instruction).
2. **Attach the cheap, high-yield context by default:**
   - Reddit: parent comment + thread title. Tag every `>` block as `QUOTED (not the commenter's view)`.
   - Chat: the most recent message of the @-target or username-echo, plus the immediately previous line. (Recency is
     a strong baseline: zero-shot LLMs did no better than "reply to the previous message" on STAC.)
   - Transcripts: a window **skewed to the past** (reading-aloud cues like "chat says", "this tweet", "he's like"
     come *before* the quoted words). Align each transcript sentence with chat lines it echoes (3+ shared words in
     the preceding minute): an echoed line is a reading-aloud candidate, not the streamer's own view.
   - Lexicon hits (glossary, dogwhistle list, emotes): the **full glossary entry**, not a flag. (GPT-3 surfaced only
     12.9% of informal/online dogwhistles unaided.)
3. **Route by form:** emote-only and pure-reaction messages go to a *reaction* path (not coded for content, or tied
   to the stream moment). Don't spend context on them.
4. **Raise fetch priority (do not decide)** on the two cues that produced the only robust flips in the socialscope
   calibration: a reply that **opens with a question** aimed at the parent's claim, and a comment that **opens with a
   `>` quote** and rebuts it. Also raise it (no validated precision yet) on: bare "this/that/it", reply
   openers ("no", "lol", "exactly", "based"), second-person "you", reporting verbs. Message length alone is *not* a
   cue (Bourgeade et al. 2024).

### Tier 1: code with minimal context, plus attribution and sufficiency

Ask the coder for, in one call:

- `attribution`: own / echo / quote / report / read-aloud-unrebutted / unclear. **Decide who is speaking before deciding stance.** Quoted
  or reported text is never the speaker's view. Quote marks make LLMs *more* likely to misread a mention as
  endorsement (GPT-4 flagged 28.6% of quoted counter-speech vs 7.2% unquoted), so define use vs. mention in the
  prompt with contrastive examples (that cut GPT-4's false flags by 82.6%, Gligorić et al. 2024).
- `label` (the provisional code).
- `context_sufficient`: yes / no, and `missing` from a closed list: referent, claim being answered, quoted source,
  stream/transcript event, in-group term, author history.

### Escalate to tier 2 if ANY of these hold (OR-gate)

1. `context_sufficient = no`.
2. A tier-0 cue fired and the provisional label is **positive or relational** (endorses, A/P stance, toxic,
   dogwhistle-in-use) **or** the label is neutral on a reply.
3. Label instability: the item's label differs across 2-3 reruns or prompt rewordings, beyond the project's measured
   noise floor.
4. Cross-model disagreement (Gemini vs Claude). Weak evidence on its own: models share biases.
5. Spread across repeated samples or coders (Davani et al. 2022: multi-prediction spread tracks human disagreement
   better than one model's confidence). Count it only above the measured rerun noise floor (4-7% in the socialscope
   calibration).
6. Gemini/open models only: high token entropy on the label. **Claude returns no logprobs**; of the Gemini models tested
   on 2026-11-12 only `gemini-4-hydrogen` returned them, so test one live call per model before relying on it.

### Tier 2: targeted fetch, then re-code

Fetch only what `missing` names:

| missing | fetch |
|---|---|
| referent / claim | parent, or the @-target's last turns; for streams, the transcript at the timestamp |
| quoted source | the quoted comment, or the start of the reading-aloud span |
| stream event | past-skewed transcript window |
| in-group term | glossary entry |
| author history | **only** for the automated coder and only for author-level constructs; never on blind human sheets (Sucu et al.'s gains are label leakage by design) |

Re-code with the target last and the fetched context short (accuracy falls with input length alone, Du et al.
2025). **Two symmetric rules:**

- **Fetch before you flag.** Any positive label must pass tier 2 before it is final. Context mostly *clears* false
  positives (the parent fixed 40% of GPT-3.5 false positives but only 6% of false negatives, Kumar et al. 2024).
- **Fetch before you clear.** A neutral-looking *reply* must pass tier 2 before it is coded N. Neutral → polar is
  the dominant flip for relational labels (Yu et al. 2022).

### Tier 3: fallback

Still insufficient after one targeted fetch → code N / uncodeable with a reason code, **and log the provisional
label** (models are right 35-62% of the time even on insufficient context, Joren et al. 2025). Send a fixed budget
of the most uncertain items to human review. A fixed window (e.g. 10 messages / 30 s) survives only as a *logged
comparison condition*, never as a silent default.

### Always log

Per item: tiers run, what was fetched, token cost, provisional vs final label, and the **signed shift**
(e.g. `N->A`). Changing the context is itself a prompt change that moves label distributions (Atreja et al. 2025),
so the log is what lets you audit it.

## LLM drift guards (two-sided: measure, don't assume a direction)

- Pull: models move toward a stream of their own earlier verdicts (~5 points, AMEL preprint; strongest on uncertain
  items). Contrast: Claude moved *away* from a single toxic parent while humans moved toward it (Yue & Vance
  preprint). Log the parent's own stance/polarity and whether any discordant message is in the window, and flag
  movement either way in calibration.
- Send each item as its own request (Batch API), never many items in one prompt: models drift toward their own
  earlier verdicts in a conversation (AMEL, preprint).
- Audit strata where an overall agreement number can hide a weakness: second-person address (Claude over-flags
  "you" text, worse with the parent shown) and counter-speech about Jewish people (the most over-flagged target in
  Gligorić et al.).
- Record the polarity of any context window (share of hostile / supportive lines). Run a window ablation before
  trusting a window: none / original / polarity-flipped / shuffled.
- One salient hostile message can count disproportionately (Wang et al., EMNLP 2025): the first piece of bad context
  does most of the damage.

## Calibrate before you trust a coder that sees context

Before using context in any new project, run `scripts/flip_calibration.py` then `scripts/analyze.py` (or follow the design by hand; set `POLAR_LABELS` for non-P/A/B label sets):

1. **Pre-register** predictions in a `*-predictions.md` file and hash it before any coding.
2. Code a sample **with (C1) and without (C0)** context, **two independent runs each**, separate requests, shuffled
   order. Include items with no context available as a **placebo** (identical input in both conditions).
3. Report: flip rate C0 vs C1 with a 95% CI; rerun noise floor in each condition; placebo rate;
   context-attributable flips (flip rate minus noise floor); the transition table (direction); "robust flips"
   (stable within both conditions, different across).
4. Use the transition table as the project's **direction prior**. Keep separate "context lowers" and "context raises"
   predictors: the only published item-level predictor (Xenos et al., AUC 0.80) detects *decreases* only. and the flip features to tune the tier-0 cues.
5. Expect the answer to depend on how the sample was drawn. In the socialscope calibration (150 comments sampled
   because they name the subject; Claude coder), context flips were **at the noise floor**: 4.4% vs 4.4-7.1% rerun
   noise, 2 robust flips of 103. Hate-word-seeded or reply-heavy samples flip far more (38.3%, Yu et al.). A single
   with/without comparison under ~10% means nothing without reruns.
6. Add human codes on the flipped items if you need to know which side was right; the calibration alone measures
   movement, not correctness.

## Cascade: weak model first, stronger model only where it is measurably unsure

Use `scripts/cascade.py` (steps `weak` -> `flag` -> `strong` -> `report`) when a large set needs coding and a
strong model on everything is too costly.

1. **Weak pass.** A cheap coder labels every item **K = 3 times** (Claude Haiku 5.5, or `gemini-4-hydrogen` for
   label-token probabilities). Each item is its own request.
2. **Flag from measured signals only.** Escalate an item if its runs disagree (`unstable`), its top-label
   probability margin is small (`low_margin`, Gemini only), the coder wrote `SUFFICIENT: no`, or its label is one you
   never accept from the weak model (`--escalate-labels`, e.g. ENDORSE or A, applying "fetch before you flag").
   **Never escalate on the weak model's self-reported confidence alone**: asked whether they need more information,
   LLMs score near chance (AUROC 0.37-0.55, Zhang & Choi 2025), two LLMs agreed on context-dependence at κ 0.26, and
   stated confidence runs high (Xiong et al. 2024). Rerun agreement is the better signal (Kruk et al. 2024: 96.2%
   precision for labels repeated across runs; Davani et al. 2022: spread tracks human disagreement).
3. **Audit what wasn't flagged.** Add a random 5-10% of unflagged items to the queue. A cascade only catches errors
   the weak model is unsure about; confident errors pass straight through, and second looks fix false positives far
   more than misses (40% vs 6%, Kumar et al. 2024). The audit is how you see that miss rate.
4. **STOP and ask the user.** `flag` writes `escalate.jsonl` and `summary.md` (counts, reasons, rough cost per
   model). Show the summary and ask whether to run the strong pass and on which model. **Never pass `--yes` without
   the user's explicit go-ahead in this conversation.**
5. **Strong pass and report.** `strong --yes` codes the queue; `report` gives weak-vs-strong change rates on flagged
   and audit items (95% CIs), the flag reasons behind each change, and `final.csv` (strong label where it ran).
   Strong-model agreement is not ground truth: models share biases. For contested items, add human codes.

Thresholds (`--margin`, `--audit`, K) are calibration choices: set them on a sample with known labels and
pre-register them. Expect the unstable share to sit near the rerun noise floor (4-7% on socialscope stance), so an
escalation queue much larger than that usually means the margin threshold is too loose. Before building a cascade,
also try the strong model alone at lower effort: one model can be cheaper than two. Evidence for cascades as such
(e.g. FrugalGPT-style routing) was not reviewed in these research rounds; the support above is for the components.

## Project adapters

- **socialscope stance (P/A/B/N):** tier 0 = parent + title + `>` tagging + glossary. Blind human sheets never get
  author history. Pre-register a two-sided direction test.
- **thehasanproject rhetoric.py:** add the use/mention step before endorse/quote; past-skewed transcript window; full
  dogwhistle glossary entries; audit results by target group (LLMs over-flag counter-speech about Jews most,
  Gligorić et al.). Replace the fixed 10 messages / 30 s with tiered fetch and keep the fixed window as a logged
  comparison.
- **search.py / ask.py:** prepend a context header to each transcript window (VOD, date, speakers, topic), rerank,
  retrieve ~top-20, rewrite follow-up questions into standalone queries, and answer from top-k first, escalating only
  if insufficient (Self-Route).
- **DGG chat:** emote-only to the reaction path; glossary first; @-target / username-echo resolution before any LLM
  parent-finder. Expect profane messages to mostly be cleared by context.

## References

- `references/evidence.md`: every claim above with its source, link and verification status.
- `docs/context-flip-calibration-{predictions,results}.md`: the first calibration on socialscope stance items.
- The three research reports behind this skill (Nov 12 2026) are kept outside the public repo because one quotes
  private rhetoric-study figures.
