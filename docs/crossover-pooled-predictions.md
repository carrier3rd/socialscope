# Crossover across five weeks: predictions (written Nov 1, 2026, 4:10 PM ET, before the pooled runs)

Weeks: Aug 18-24, Sep 8-14, Sep 22-28, Oct 13-19, Oct 20-26 (the Ethan week), all comments in the 18 subs (h3snark
excluded). Same code and frozen tier 1 pattern rule as the earlier runs. Home sub = where an account comments most within
each week. A crossing = comments in a sub by accounts whose home that week is another of the 18 subs.

## Pooled crossover and reception (task 1)
1. Pooled over the four non-event weeks, Hasan regulars' comments in r/h3h3productions number over 50, and 25% or more
   score at or below 0 against 15% or less for h3 locals: the hostility is there in quiet weeks, just rare.
2. Destiny regulars are the largest outside group in r/thedavidpakmanshow in all five weeks.
3. Of the crossings with 100+ pooled comments, at most three are hostile (visitors' at-or-below-0 share at least 1.5x
   locals'), and every hostile one runs into the h3 subs or between the Hasan and Destiny communities.
4. Over 90% of each sub's comments come from its own week's regulars in every week, Ethan week included, except
   LeftoversH3 and the h3 sub in the Ethan week.

## Talking-point direction (task 3)
5. Repeated talking points (2+ accounts, 2+ subs) flow more often from the politics subs (neoliberal, thebulwark,
   PoliticalCompassMemes, Conservative, ukraine) into the drama subs than the reverse, pooled over five weeks.
6. LivestreamFail is the most common first-seen sub for talking points that reach three or more subs.

## Results for task 1 (scored Nov 1, 2026)
Visitor = an account whose home that week is another of the 18 subs. "Low" = comment score at or below 0. Wilson 95% intervals.

1. **Missed.** In the four quiet weeks, Hasan regulars left only 14 comments in r/h3h3productions, not over 50. 29% of them were low (12-55%), against 9% for h3 locals. The direction holds, but the count is far too small to count as a finding. In the Ethan week they left 204 comments, 33% low (27-40%) against 10% for locals. The crossing is close to empty outside drama weeks.
2. **Held.** Destiny regulars are the largest outside group in r/thedavidpakmanshow in every week: 8-12% of all its comments. The next group is always much smaller, usually thebulwark at about 2-4%.
3. **Missed.** 71 crossings had 100+ pooled comments, and 11 of them were hostile at the 1.5x bar. Most do run into the h3 subs: LeftoversH3 to h3 3.0x, Hasan to h3 3.4x, LSF to h3 2.2x, h3 to Leftovers 4.4x, neoliberal to h3 2.1x. The miss is a second cluster running into r/neoliberal: LSF 3.2x, PCM 3.1x, thebulwark 2.8x, Destiny 2.3x. Locals' low share there is only 3%, so a 7-10% visitor rate becomes a large ratio. That is real, but it is mild: about 90% of visitor comments in neoliberal still score above 0.
4. **Missed.** r/thedavidpakmanshow (80-84%) and r/atrioc (80-90%) fall below 90% in every week, and r/Hasan_Piker drops to 86% in the Ethan week. The other 15 subs stay at 91% or higher in every week, Ethan week included. LeftoversH3 and h3 stayed at 97-98% even in the Ethan week, which is the opposite of the exception I predicted.

## Results for task 3 (scored Nov 1, 2026)
Method change: the TF-IDF near-duplicate clustering ran out of memory on weeks of 250k+ comments. I switched to exact
8-word phrase matching instead. Quoted lines and URLs are stripped first. Two comments join a cluster when they share an
8-word phrase used by 2-200 comments, from at least two accounts. A talking point is a cluster that reaches 2+ subs, and
its spread order is the order of each sub's first use. This catches verbatim repetition and misses paraphrase. The code
is in work/tp/tp2.py (not committed: it reads the private weekly pickle).

Talking points found: 559 (Aug 18), 608 (Sep 8), 471 (Sep 22), 549 (Oct 13) and 1,919 in the Ethan week (Oct 20).
The largest cluster has 142 comments, so no single phrase chained everything together.

5. **Missed.** Politics subs = neoliberal, thebulwark, PCM, Conservative, ukraine. Drama subs = Asmongold, Destiny,
   Hasan_Piker, LeftoversH3, LSF, atrioc, h3h3productions. Pooled over five weeks, 859 spread steps run from politics to
   drama and 811 run the other way. That is an even split (p = 0.25). The four quiet weeks actually lean slightly the
   other way: 520 politics-to-drama against 557 drama-to-politics (p = 0.27). Only the Ethan week shows a direction:
   339 against 254 (p < 0.001). The traffic there mostly flows out of the h3 subs, and the h3 subs count as drama subs, so
   that week doesn't support the prediction's logic either. Bigger subs also produce more first uses just by volume, which
   I didn't adjust for.
6. **Missed.** Of the 666 talking points that reached 3+ subs, the most common first-seen subs were neoliberal (94), PCM (93),
   Destiny (92) and LivestreamFail (80), with h3h3productions next (63). These are roughly the biggest and fastest subs, so
   first-seen tracks size more than origin. In the Ethan week, h3h3productions leads (55) and LSF is second (39).

What this says: across these 18 subs, repeated phrasing moves in both directions about equally in normal weeks. Only a
drama event produces a clear source, and the source is the sub at the center of the event. Nothing here looks like a
coordinated push from one community into another.

## Correction (Nov 2, 2026): task 3 results void
Gemini labeled a random 150 of the phrase clusters. 59% were coincidental stock phrases, 11% memes and 7% shared
quotes. Only 22% were talking points, and my spot check says even that is generous, since many of those share a topic
rather than a framing. The share was 17% in quiet weeks and 43% in the Ethan week. So the direction counts and first-seen
counts above mostly measure idiom overlap, and predictions 5 and 6 are unscored. On the 33 talking-point clusters alone:
5 politics-to-drama steps against 6 drama-to-politics, too few to say anything. "Nothing here looks like a coordinated
push" is withdrawn as unsupported. Redo: embedding clustering (e5-base-v2, as in Hanley & Durumeric), with a single-source
cap and idiom, quote and meme filters, evaluated against Gemini's 150 labels (work/tp/gem_tp*.csv).
