#!/usr/bin/env python3
"""Sentiment toward a named target across subreddits, from a random sample of mentions.

Scores only the sentences that mention the target (plus one sentence either side) with VADER,
a lexicon model built for social media text (Hutto & Gilbert, 2014). VADER measures tone, so a
comment angrily defending the target scores negative: hand-check the saved sample before reporting.

Usage:
  python3 sentiment.py data/*.json --target "atrioc|big a" -o out/atrioc --sample 300
"""
import argparse, csv, os, random, re, statistics as st, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reddit_io import load_reddit
from vader.vaderSentiment import SentimentIntensityAnalyzer

SENT = re.compile(r"(?<=[.!?])\s+|\n+")


def window(text, rx):
    parts = [p for p in SENT.split(text) if p.strip()]
    keep = set()
    for i, p in enumerate(parts):
        if rx.search(p):
            keep.update({i - 1, i, i + 1})
    return " ".join(parts[i] for i in sorted(keep) if 0 <= i < len(parts))


def boot_ci(vals, n=2000, seed=1):
    if len(vals) < 5:
        return (None, None)
    rnd = random.Random(seed)
    means = sorted(st.fmean(rnd.choices(vals, k=len(vals))) for _ in range(n))
    return (round(means[int(0.025 * n)], 3), round(means[int(0.975 * n)], 3))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--target", required=True, help="regex for the target (case-insensitive), e.g. 'atrioc|big a'")
    ap.add_argument("--exclude", default="", help="regex; mentions matching it are dropped (e.g. 'destiny 2|manifest destiny')")
    ap.add_argument("--sample", type=int, default=300, help="random mentions scored per subreddit")
    ap.add_argument("--top", type=int, default=25, help="also score the N highest-scoring mentions, to show selection bias")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("-o", "--out", default="sentiment_out")
    a = ap.parse_args()

    rx = re.compile(rf"\b(?:{a.target})\b", re.I)
    ex = re.compile(a.exclude, re.I) if a.exclude else None
    sia = SentimentIntensityAnalyzer()
    rows = load_reddit(a.inputs)
    by_sub = defaultdict(list)
    for r in rows:
        text = (r["title"] + "\n" + r["body"]).strip()
        if r["removed"] or not rx.search(text) or (ex and ex.search(text)):
            continue
        by_sub[r["sub"]].append((r["score"], window(text, rx) or text))

    os.makedirs(a.out, exist_ok=True)
    rnd = random.Random(a.seed)
    summary, examples = [], []
    for sub, items in sorted(by_sub.items(), key=lambda kv: -len(kv[1])):
        samp = items if len(items) <= a.sample else rnd.sample(items, a.sample)
        comp = [sia.polarity_scores(t)["compound"] for _, t in samp]
        top = sorted(items, key=lambda x: -x[0])[:a.top]
        top_comp = [sia.polarity_scores(t)["compound"] for _, t in top]
        pos = sum(c >= 0.05 for c in comp) / len(comp)
        neg = sum(c <= -0.05 for c in comp) / len(comp)
        lo, hi = boot_ci(comp)
        summary.append({"subreddit": sub, "mentions": len(items), "sampled": len(samp),
                        "positive_pct": round(100 * pos, 1), "negative_pct": round(100 * neg, 1),
                        "neutral_pct": round(100 * (1 - pos - neg), 1), "mean_tone": round(st.fmean(comp), 3),
                        "ci_low": lo, "ci_high": hi,
                        "top_mean_tone": round(st.fmean(top_comp), 3) if top_comp else ""})
        for (sc, t), c in zip(samp, comp):
            examples.append({"subreddit": sub, "tone": c, "score": sc, "text": t[:400]})
    with open(os.path.join(a.out, "sentiment_summary.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0].keys())); w.writeheader(); w.writerows(summary)
    with open(os.path.join(a.out, "sentiment_sample.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["subreddit", "tone", "score", "text"]); w.writeheader(); w.writerows(examples)
    for s in summary:
        print(f"r/{s['subreddit']:18} n={s['mentions']:5} sampled={s['sampled']:4} pos {s['positive_pct']:5}% neg {s['negative_pct']:5}% "
              f"tone {s['mean_tone']:+.2f} [{s['ci_low']}, {s['ci_high']}] | top-voted tone {s['top_mean_tone']}")


if __name__ == "__main__":
    main()
