#!/usr/bin/env python3
"""Cross-link mobilization test, after Kumar, Hamilton, Leskovec & Jurafsky (2018),
"Community Interaction and Conflict on the Web".

For every post or comment in sub S that links a thread T in another sub H:
  - S-members: accounts with >= --min-member items in S that week and <= 2 items in H outside T.
  - Count S-member comments in T in the window before the first link and the window after.
  - Do the same for matched control threads in H (created within +-6h, similar comment count
    before the link time, never linked from S).
  - Mobilized when T's after/before ratio exceeds 1.6x the controls' ratio and T gets >= 3
    S-member comments after the link (the paper's 1.6x criterion, simplified).
Also reports how negative the arrivals were (VADER) against the thread's regulars, and the
removal rate of each group.

Usage: python3 crosslinks.py data/*.json -o out/crosslinks
"""
import argparse, csv, os, statistics as st, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reddit_io import load_reddit, THREAD_LINK
from vader.vaderSentiment import SentimentIntensityAnalyzer


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-o", "--out", default="crosslinks_out")
    ap.add_argument("--window-hours", type=float, default=12)
    ap.add_argument("--min-member", type=int, default=3)
    ap.add_argument("--ratio", type=float, default=1.6)
    ap.add_argument("--skip-authors", default="")
    a = ap.parse_args()
    W = a.window_hours * 3600
    rows = load_reddit(a.inputs, [x.strip() for x in a.skip_authors.split(",") if x.strip()])
    sia = SentimentIntensityAnalyzer()

    threads = {r["thread"]: r for r in rows if r["is_post"]}
    comments = defaultdict(list)
    activity = defaultdict(Counter)
    for r in rows:
        activity[r["sub"]][r["author"]] += 1
        if not r["is_post"]:
            comments[r["thread"]].append(r)

    links = {}  # (S, T) -> first link time
    for r in rows:
        for m in THREAD_LINK.findall(r["url"] + " " + r["body"]):
            t = "t3_" + m.lower()
            if t in threads and threads[t]["sub"] != r["sub"]:
                k = (r["sub"], t)
                links[k] = min(links.get(k, r["created"]), r["created"])
    linked_from = defaultdict(set)
    for s, t in links:
        linked_from[t].add(s)

    def members_in(cs, src, host, thread):
        own = Counter(c["author"] for c in cs)
        return {au for au, n in own.items() if activity[src][au] >= a.min_member and activity[host][au] - n <= 2}

    def counts(thread, src, host, L):
        cs = comments.get(thread, [])
        mem = members_in(cs, src, host, thread)
        before = sum(1 for c in cs if c["author"] in mem and L - W <= c["created"] < L)
        after = [c for c in cs if c["author"] in mem and L <= c["created"] < L + W]
        prior = sum(1 for c in cs if c["created"] < L)
        return before, after, prior, mem

    results = []
    for (src, t), L in sorted(links.items(), key=lambda kv: kv[1]):
        host = threads[t]["sub"]
        b, after, prior, mem = counts(t, src, host, L)
        ctrl = []
        for cid, p in threads.items():
            if p["sub"] != host or cid == t or src in linked_from.get(cid, ()):
                continue
            if abs(p["created"] - threads[t]["created"]) > 6 * 3600:
                continue
            cb, ca, cprior, _ = counts(cid, src, host, L - threads[t]["created"] + p["created"])
            if prior and not (0.5 * prior <= cprior <= 2 * prior + 5):
                continue
            ctrl.append((cb, len(ca)))
        t_ratio = (len(after) + 1) / (b + 1)
        c_ratio = st.fmean([(ca + 1) / (cb + 1) for cb, ca in ctrl]) if ctrl else 1.0
        mobilized = t_ratio > a.ratio * c_ratio and len(after) >= 3
        regulars = [c for c in comments.get(t, []) if c["author"] not in mem and L <= c["created"] < L + W]
        tone = lambda cs: round(st.fmean(sia.polarity_scores(c["body"])["compound"] for c in cs), 3) if cs else ""
        negs = lambda cs: round(100 * sum(sia.polarity_scores(c["body"])["compound"] <= -0.05 for c in cs) / len(cs), 1) if cs else ""
        rem = lambda cs: round(100 * sum(c["removed"] for c in cs) / len(cs), 1) if cs else ""
        results.append({
            "from": src, "to": host, "thread": t, "title": threads[t]["title"][:120],
            "link_hours_after_post": round((L - threads[t]["created"]) / 3600, 1),
            "members_before": b, "members_after": len(after), "control_threads": len(ctrl),
            "thread_ratio": round(t_ratio, 2), "control_ratio": round(c_ratio, 2), "mobilized": mobilized,
            "arrival_tone": tone(after), "regular_tone": tone(regulars),
            "arrival_negative_pct": negs(after), "regular_negative_pct": negs(regulars),
            "arrival_removed_pct": rem(after), "regular_removed_pct": rem(regulars),
        })

    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "crosslinks.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        if results:
            w = csv.DictWriter(fh, fieldnames=list(results[0].keys())); w.writeheader(); w.writerows(results)
    mob = [r for r in results if r["mobilized"]]
    print(f"{len(results)} cross-links between subs in the data; {len(mob)} mobilized ({100 * len(mob) / max(1, len(results)):.0f}%; "
          f"the 2018 study found about 16%)")
    for r in sorted(results, key=lambda r: -r["members_after"])[:12]:
        print(f"  {'MOBILIZED ' if r['mobilized'] else ''}r/{r['from']} -> r/{r['to']}: members {r['members_before']}->{r['members_after']} "
              f"(ratio {r['thread_ratio']} vs controls {r['control_ratio']}, n={r['control_threads']}) | tone arrivals {r['arrival_tone']} "
              f"vs regulars {r['regular_tone']} | {r['title'][:70]}")
    print("wrote", path)


if __name__ == "__main__":
    main()
