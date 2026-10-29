#!/usr/bin/env python3
"""What each subreddit talked about: topic clusters and most-mentioned names, per sub.

Topics come from NMF on TF-IDF of posts and comments (5+ words), fixed seed, so the same data gives
the same topics. Names are capitalized words and two-word phrases counted once per comment, minus
common sentence starters. Both are starting points: read the top terms and label topics yourself, and
pick subjects for stance coding from the names list.

Usage:
  python3 topics.py reddit/*.zip -o out/topics
  python3 topics.py reddit/*.zip -o out/topics --topics 8 --names 40

Outputs:
  topics.csv  sub, topic number, share of documents, top terms
  names.csv   sub, name, comments mentioning it
  topics.md   readable summary of both
"""
import argparse, csv, os, re, sys
from collections import Counter, defaultdict

import numpy as np
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reddit_io import load_reddit

EXTRA_STOP = set("""just like people think know get really would one even also going said say make time way good right
actually lol yeah want need thing things much still see guy guys gonna dont im thats its youre cant didnt doesnt https
com www http amp gt deleted removed ve don doesn didn isn wasn aren shit fuck fucking lmao bro dude""".split())
# image/link debris that otherwise forms its own "topic"
JUNK = re.compile(r"https?://\S+|preview\.redd\.it\S*|\b(?:jpe?g|png|gif|webp|pjpg|giphy|width|format|auto)\b", re.I)
CAP = re.compile(r"\b([A-Z][a-zA-Z]{2,}(?:\s[A-Z][a-zA-Z]{2,})?)\b")
CAP_STOP = set("""The This That What It's You And But Not Just Like Yeah Also Its They There Why How When Who Well Yes He She We
If Lol So Is Was Are Do Does Did Can For Of In On To My Me Your His Her Our Their Imagine Because Even I'm Don't I've Edit
Reddit Maybe Never Literally Honestly Nah Wait Same Oh Okay Ok Then Now Here All No One Some Thank Thanks Holy Damn God
Where Should Would Could Any Every Being With From Most Still Only Has Have Had These Those Which People Don Let Sure
Idk Bro Dude Man Good Get Please Pretty Thats Everyone Especially Omg""".split())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-o", "--out", default="topics_out")
    ap.add_argument("--topics", type=int, default=0, help="topics per sub (default: 10 for 3,000+ docs, else 6)")
    ap.add_argument("--names", type=int, default=30)
    ap.add_argument("--min-docs", type=int, default=200, help="skip topic modeling for subs with fewer docs")
    ap.add_argument("--skip-authors", default="")
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()

    rows = load_reddit(a.inputs, [x.strip() for x in a.skip_authors.split(",") if x.strip()])
    docs = defaultdict(list)
    for r in rows:
        if r["removed"]:
            continue
        t = JUNK.sub(" ", (r["title"] + " " + r["body"]).strip())
        if len(t.split()) >= 5:
            docs[r["sub"]].append(t)

    os.makedirs(a.out, exist_ok=True)
    trows, nrows, md = [], [], ["# Topics by subreddit", ""]
    stop = list(ENGLISH_STOP_WORDS | EXTRA_STOP)
    for sub, ds in sorted(docs.items(), key=lambda kv: -len(kv[1])):
        names = Counter()
        for d in ds:
            names.update({m for m in CAP.findall(d) if m.split()[0] not in CAP_STOP})
        md += [f"## r/{sub} ({len(ds):,} posts and comments)", "",
               "Most-mentioned names: " + ", ".join(f"{n} ({c})" for n, c in names.most_common(a.names)), ""]
        nrows += [{"subreddit": sub, "name": n, "comments": c} for n, c in names.most_common(a.names)]
        if len(ds) < a.min_docs:
            md += [f"Too few documents for topic modeling (under {a.min_docs}).", ""]
            continue
        k = a.topics or (10 if len(ds) >= 3000 else 6)
        vec = TfidfVectorizer(max_df=0.3, min_df=5, stop_words=stop, ngram_range=(1, 2), max_features=20000)
        X = vec.fit_transform(ds)
        nmf = NMF(n_components=k, random_state=a.seed, init="nndsvda", max_iter=400)
        W = nmf.fit_transform(X)
        terms = np.array(vec.get_feature_names_out())
        share = Counter(W.argmax(1))
        order = sorted(range(k), key=lambda i: -share[i])
        md += ["| Topic | Share | Top terms |", "|---|---|---|"]
        for rank, i in enumerate(order):
            top = ", ".join(terms[nmf.components_[i].argsort()[::-1][:10]])
            pct = round(100 * share[i] / len(ds), 1)
            trows.append({"subreddit": sub, "topic": rank + 1, "share_pct": pct, "top_terms": top})
            md.append(f"| {rank + 1} | {pct}% | {top} |")
        md += ["", "The largest topic is often general chatter (insults, agreement, filler). Label topics from their terms.", ""]

    for name, data in (("topics.csv", trows), ("names.csv", nrows)):
        with open(os.path.join(a.out, name), "w", newline="", encoding="utf-8") as fh:
            if data:
                w = csv.DictWriter(fh, fieldnames=list(data[0].keys())); w.writeheader(); w.writerows(data)
    open(os.path.join(a.out, "topics.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
