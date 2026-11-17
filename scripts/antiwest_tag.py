#!/usr/bin/env python3
"""Tag text with the anti-Western talking-point lexicon in data/antiwest/.

  transcripts:  python3 scripts/antiwest_tag.py data/antiwest/transcripts/*.txt --examples 3
  reddit dumps: python3 scripts/antiwest_tag.py 'pulls/week/*_comments_*.zip' --by subreddit -o out/antiwest_week.csv
  one string:   echo "critical support for the DPRK against the imperial core" | python3 scripts/antiwest_tag.py -

What it does: counts (a) vocabulary terms from vocabulary.csv and (b) cue phrases of each talking point in
talking_points.csv, then reports per group (file, or --by field for Reddit records): documents scanned, documents with
any hit, hits per 10,000 documents by family and by faction, and the top terms.

Faction scores weight a term by specificity (high 3, medium 2, low 1) and split it across the factions listed for it.
Counter-class factions (ANTICAMP, LIB) are reported too: a group high on ANTICAMP terms is arguing against campists.

What it does not do:
  - It does not read stance. "Critical support" inside a comment mocking tankies still counts. Before reporting any
    rate, read a random sample of hits per group (--examples) and code assert / dispute / quote / joke, as
    docs/research-methods.md does for claims.
  - It never labels an account. Output is per group only; no author field is read or written.
  - Tier 3 talking points and low-specificity terms are shared with the isolationist right and with mainstream
    critics. --min-specificity medium (the default) leaves low-specificity vocabulary out of the scores.

Before running it on a pulled week, commit a *-predictions.md file (CLAUDE.md rule 3).
"""
import argparse, collections, csv, glob, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "antiwest")
WEIGHT = {"high": 3, "medium": 2, "low": 1}
QUOTE = re.compile(r"^\s*>.*$", re.M)


def phrase_re(p):
    """Phrase -> regex: flexible spaces/hyphens, optional plural s; all-caps short terms stay case-sensitive."""
    p = p.strip()
    body = re.escape(p).replace(r"\-", "\x00").replace(r"\ ", r"[\s\-]+").replace("\x00", r"[\s\-]?")
    if p.isupper() and len(p) <= 5:
        return r"(?<![A-Za-z])(?-i:%s)(?![A-Za-z])" % body
    return r"(?<![A-Za-z])%s(?:s|es)?(?![A-Za-z])" % body


def load():
    terms, points = [], []
    for r in csv.DictReader(open(os.path.join(DATA, "vocabulary.csv"), encoding="utf-8")):
        forms = [r["term"]] + [v for v in r["variants"].split(";") if v.strip()]
        r["re"] = re.compile("|".join(phrase_re(f) for f in forms), re.I)
        terms.append(r)
    for r in csv.DictReader(open(os.path.join(DATA, "talking_points.csv"), encoding="utf-8")):
        cues = [c.split(" / ")[0] for c in r["cue_phrases"].split(";") if len(c.strip()) > 5]
        r["re"] = re.compile("|".join(phrase_re(c) for c in cues), re.I)
        points.append(r)
    return terms, points


def docs(paths, by):
    """Yield (group, text). .txt transcripts: one doc per line; Reddit dumps: one per comment or post."""
    for pat in paths:
        if pat == "-":
            for line in sys.stdin:
                yield "stdin", line
            continue
        for path in sorted(glob.glob(pat)) or [pat]:
            if path.endswith(".txt"):
                for line in open(path, encoding="utf-8", errors="replace"):
                    if not line.startswith("#"):
                        yield os.path.basename(path)[:-4], line
            else:
                sys.path.insert(0, HERE)
                from reddit_io import iter_records
                for d in iter_records([path]):
                    text = d.get("body") or ((d.get("title") or "") + "\n" + (d.get("selftext") or ""))
                    yield str(d.get(by, "all")), QUOTE.sub("", text)   # quoted lines are someone else's words


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("paths", nargs="+")
    p.add_argument("--by", default="subreddit", help="record field to group Reddit data by")
    p.add_argument("--min-specificity", default="medium", choices=["low", "medium", "high"])
    p.add_argument("--examples", type=int, default=0, help="print N random matching snippets per group (no authors)")
    p.add_argument("-o", "--out", help="write the per-group table as CSV")
    a = p.parse_args()
    terms, points = load()
    floor = WEIGHT[a.min_specificity]
    n, hit = collections.Counter(), collections.Counter()
    fam, fac, top, tp = (collections.defaultdict(collections.Counter) for _ in range(4))
    ex = collections.defaultdict(list)
    for g, text in docs(a.paths, a.by):
        n[g] += 1
        found = False
        for t in terms:
            if WEIGHT[t["specificity"]] >= floor and t["re"].search(text):
                found = True
                fam[g][t["family"]] += 1; top[g][t["term"]] += 1
                fs = t["factions"].split()
                for f in fs:
                    fac[g][f] += WEIGHT[t["specificity"]] / len(fs)
        for r in points:
            m = r["re"].search(text)
            if m:
                found = True
                tp[g][r["id"]] += 1
                if a.examples:
                    ex[g].append("%s  ...%s..." % (r["id"], re.sub(r"\s+", " ", text[max(0, m.start() - 120):m.end() + 120])))
        hit[g] += found
    rows = []
    for g in sorted(n, key=lambda k: -hit[k] / max(n[k], 1)):
        k = 1e4 / n[g]
        row = {"group": g, "docs": n[g], "docs_with_hit": hit[g], "hit_pct": round(100 * hit[g] / n[g], 2)}
        row.update({"fam_" + f: round(c * k, 1) for f, c in fam[g].items()})
        row.update({"faction_" + f: round(c * k, 1) for f, c in fac[g].items()})
        row["top_terms"] = "; ".join("%s %d" % x for x in top[g].most_common(8))
        row["top_points"] = "; ".join("%s %d" % x for x in tp[g].most_common(8))
        rows.append(row)
        print("\n%s: %d docs, %d with a hit (%.1f%%)" % (g, n[g], hit[g], row["hit_pct"]))
        print("  factions per 10k:", ", ".join("%s %.0f" % (f, c * k) for f, c in fac[g].most_common(6)))
        print("  terms:", row["top_terms"]); print("  talking points:", row["top_points"])
        for s in random.Random(1).sample(ex[g], min(a.examples, len(ex[g]))):
            print("   >", s[:330])
    if a.out:
        cols = sorted({c for r in rows for c in r}, key=lambda c: (c not in ("group", "docs", "docs_with_hit", "hit_pct"), c))
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
        print("\nwrote", a.out)
    print("\nHits are leads. Read a sample and code stance before reporting a rate; never report per account.")


if __name__ == "__main__":
    main()
