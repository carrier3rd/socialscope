# Commentator valence toward US actions: design and predictions (written Nov 2, 2026, 6:10 AM ET, before any coding)

Hypothesis (Joseph): "America is bad" is shorthand for a default weighting in which US actions carry a negative sign
before they are assessed. The weighting comes more from commentators than from commenters, and audiences pick it up.

Design: Gemini watches YouTube uploads of commentator streams in our six pulled weeks (Aug 18, Sep 8, Sep 22, Oct 13,
Oct 20, Oct 27). For every segment discussing a US action (government, military, agency or company acting abroad or at
home), it codes:
- valence: neg / pos / mixed
- default: whether the negative or positive sign comes before any case-specific reasoning, or follows from it
- a verbatim quote of 25 words or fewer, with a timestamp

I verify every quote against the fetched transcript and drop any that don't match. Commenter side: the same coding on
Reddit comments from each commentator's sub in the same weeks. Then the lag: does a framing appear in the sub after the
commentator uses it, and how many days later?

Predictions:
1. Hasan: 80%+ of US-action segments negative, and at least half of those negative by default.
2. Destiny: 40-65% negative, mostly on Trump-administration actions. Negative by default under 15%.
3. Pakman and the Bulwark: 70%+ negative on administration actions, under 20% negative on US institutions or the US
   as a whole.
4. Each commentator's sub is less negative by default than the commentator: the stream-to-sub drop is at least 10 points.
5. Where a specific framing is traceable (the same phrase or claim), it reaches the sub within 0-3 days of the stream in
   most cases.
6. Gemini's quote accuracy before verification is under 80%: at least 1 in 5 quotes won't match the transcript.
