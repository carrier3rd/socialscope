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
