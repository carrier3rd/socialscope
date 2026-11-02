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

## Pilot and amendment (Nov 2, 2026, 2:50 PM ET, before the full run)
Pilot: 8 files of 5 transcript chunks each (4 Hasan, 4 Destiny, spread over the six weeks), coded by Gemini.
- **Quotes:** 42 of 50 matched the transcript verbatim (84%). That is above my "under 80%" prediction, so prediction 6
  missed.
- **Speakers:** most of Destiny's uploads are reactions and debates. Gemini put 14 of 25 Destiny rows on clips or
  guests, so a speaker column is now required, and only rows where the commentator is speaking are used.
- **Default column dropped:** Gemini's "default" (judgment-first) calls were unreliable. It called Destiny's
  step-by-step JCPOA argument judgment-first.
- **New variable, target:** what the evaluation is aimed at. Codes: administration (a named administration, official or
  politician); agency (an agency or institution as such, e.g. ICE, DHS, CIA, the military); company (a US company);
  system (the US as a whole, its empire, state policy across administrations, capitalism/the system).
- **Pilot result, my own tags on the verified commentator rows:**
  - Destiny: 7 of 7 aimed at an administration.
  - Hasan: about 4 of 23 aimed at an administration; the rest at agencies, companies or the system.
  - Valence did not separate them: 23 of 23 negative for Hasan, 6 of 7 for Destiny.

Amended predictions for the full run (Hasan and Destiny; Pakman and Bulwark later). Commentator rows only, verified
quotes only:
7. Hasan: 60% or more of his negative evaluations target agency, company or system.
8. Destiny: 60% or more of his evaluations target an administration. Agency plus system is 25% or less.
9. Positive or mixed share: Destiny 10% or more, Hasan 5% or less.
10. Agreement: my target tags on a random 20 of Gemini's rows agree with Gemini's 75% or more of the time.
