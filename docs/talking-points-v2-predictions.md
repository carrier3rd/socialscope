# Talking-point detection v2: design and predictions (written Nov 2, 2026, 7:30 AM ET, before any run)

Why: Gemini labeled 150 random clusters from the exact 8-word method, and only 22% were talking points (17% in quiet
weeks). The rest were stock phrases, memes and shared quotes. Those direction results are void
(docs/crossover-pooled-predictions.md).

Method (scripts/tp_embed.py, frozen at this commit):
- **Comments:** 12+ words after cleaning.
- **Embeddings:** all-mpnet-base-v2, with the 20 nearest neighbours per comment within a week.
- **Clustering:** leader clustering at cosine 0.80.
- **Talking point:** a cluster with 3+ accounts across 2+ subs, where no account or thread supplies over half the
  comments, and where under half the comments share a verbatim 10-word span. Clusters over that span limit go to a
  separate quotes file.
- **Sensitivity runs:** 0.75 and 0.85, on cached embeddings.
- **Weeks:** Aug 18, Sep 8, Sep 22, Oct 13, Oct 20 and Oct 27 (partial, through Nov 1).

Evaluation: Gemini labels 150 random kept clusters at 0.80, blind, with the same five labels as before. I spot-check 20.

Predictions:
1. 55-75% of sampled v2 clusters are labeled TP, against 22% for v1.
2. Coincidence (stock phrase) drops below 15%. Memes and quotes together make up 10-25%.
3. A quiet week yields 150-700 talking-point clusters at 0.80. The Ethan week yields at least 2x the quiet-week average.
4. Quiet weeks: politics-to-drama and drama-to-politics spread steps are within 20% of each other. Ethan week: the h3
   subs are first-seen for at least 30% of clusters that reach 3+ subs.
5. Under 10% of clusters spread across 3+ subs within an hour. Fast multi-sub spread is the coordination signature, and
   it should be rare.

Amendment (Nov 2, 2026, 11:00 AM ET, before any output existed): all-mpnet-base-v2 ran at about 15 s per 128 comments on
the laptop CPU, which works out to about 33 h for six weeks. The run was switched to sentence-transformers/all-MiniLM-L6-v2
(--batch 256). The thresholds, filters and predictions are unchanged.

## Results (Nov 2, 2026, 6:40 PM ET)
Gemini 4 Argon (high thinking) labeled the 150 sampled clusters at 0.80, blind, in three fresh chats: TP 86 (57%), coincidence 62 (41%), meme 2, quote 0, template 0. The sample is random over kept clusters, so it is mostly Oct 20 (100) and Oct 27 (34). Quiet weeks: 7 TP of 16. I spot-checked 20 random clusters and agreed on 19 (the miss, 135, is speculation about where Hila will live, which I would call a topic, not a point).

1. **Held, barely.** 57% TP, against 22% for v1. Note a labeler change: v1 was labeled on an older Gemini. A v1 relabel on Argon is pending.
2. **Missed.** Coincidence is 41%, not under 15%. Memes and quotes are 1%, not 10-25%. The coincidences are a new failure: same-topic clusters where commenters argue different or opposite points (Ethan and Tamara blame, anti-Zionism vs antisemitism). Embeddings group by subject more than by claim.
3. **Half held.** Quiet weeks gave 43-71 clusters, far below 150-700. The Ethan week gave 1,262 (Oct 27, partial: 424), well over 2x the quiet average.
4. **Held.** Quiet weeks: 40 politics-to-drama steps against 33 drama-to-politics (18% apart, inside 20%). Oct 20: h3 subs were first-seen for 60% of 3+-sub clusters (Oct 27: 39%). Drama subs here are h3h3productions, LeftoversH3, LivestreamFail, Asmongold and atrioc; Destiny and Hasan_Piker count as politics.
5. **Held.** No cluster in any week reached 3+ subs within an hour (0 of 1,916).

Next: Argon labels the 0.85 sample to test whether a stricter threshold removes topic clusters, and relabels the v1 part 1 sample to check for a labeler effect.
