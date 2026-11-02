# Sarcasm-aware stance prompt: predictions (written before any output)

Date: 2026-11-02. Status: scored 2026-11-02.

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

## Results (2026-11-02)
Raw agreement with my original codes: 123/150 (82%), kappa 0.735 (old prompt 119, kappa 0.702).

1. **Missed.** 82%, just under the 83-88% range.
2. **Held.** 13 of the 31 old disagreements now match my code. Another 13 stayed with old Gemini.
3. **Missed by one.** 9 old agreements flipped.
4. **Missed.** Only 5 items were marked echo (3%), far under 15-30. Two of those five fixed real errors (189, a sarcastic Trump-voice post on Ukraine; 787, a mock "Jewish space lasers" reply to a /s parent). One was an echo flag with the wrong target (469: mocks direct NATO intervention, not Ukraine).
5. **Missed.** Remaining disagreements by my code: N 11, A 9, B 4, P 3.

### Adjudication
I re-read every item where the coders split (the 13 where both Gemini runs agreed against me, and the 9 flips). This was not blind: I had seen the codes. Items where all three agreed were not re-checked.
- On the 13, Gemini was right on 11. Most of my errors were A where the comment was P. These were reply comments that quote the opponent with ">" and then rebut it (665, 677, 928, 774): I coded the quoted text. That is the echo problem, made by the human coder through quote blocks rather than sarcasm.
- On the 9 flips, the new prompt was better on 5 (301, 378, 540, 787, 1323), worse on 3 (104, 479, 795), with 1 tie.

Accuracy against adjudicated codes: my codes 134/150 (89%), old Gemini 125 (83%), new Gemini 139 (93%).

### Takeaways
- Sarcasm proper is rare in this comment sample (about 3%). It is not the main error source for comment stance.
- Context is. The parent comment plus quote-block structure decide most hard cases.
- Future comment coding uses this prompt. Add one rule: text after ">" is quoted from someone else and is never the commenter's view.
