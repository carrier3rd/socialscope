# Sarcasm-aware stance prompt: predictions (written before any output)

Date: 2026-11-02. Status: sent to Gemini, results pending.

## Design
- Same 150 stance items Gemini coded before (opinion-pooled second-coder set). Old agreement with my codes: 119/150 (79%), kappa 0.70.
- New prompt adds what the literature says matters (see research-methods.md):
  - parent comment as context (found for 113 of 116 replies; 34 are top-level),
  - glossary entries for any glossary term in the item or parent,
  - a "whose view" step (own / echo / unclear) before coding, from echoic irony theory,
  - a one-line literal-vs-intended note before each code (pragmatic metacognitive prompting).
- Items reshuffled (seed 7), usernames masked, 3 parts of 50 in fresh chats.
- Context builder: scripts/sarcasm_ctx.py.

## Predictions
1. Agreement with my codes rises to 83-88% (kappa about 0.76).
2. Of the 31 old disagreements, the new prompt matches my code on 12-18.
3. Of the 119 old agreements, 8 or fewer flip.
4. VIEW = echo on 15-30 items, and the echo rate among old disagreements is at least twice the rate among old agreements.
5. Where new Gemini still disagrees with me, most are items I coded A (my errors leaned toward "against").

My codes are not ground truth. Items where old and new Gemini agree with each other against me get a blind re-read by me before scoring.
