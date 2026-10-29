#!/usr/bin/env python3
"""Blind stance coding: where opinion about a person or side actually lands, per subreddit.

Three steps, each a subcommand:

  sample  Draw a random sample of relevant comments per sub and write two files:
            stance_sheet.csv  - item number + text only (what the coder sees; shuffled, no sub)
            stance_key.csv    - item number -> sub, score, thread (kept out of sight until tally)
          python3 stance.py sample data/*.json --target "atrioc|big a" \
              --context "poki|pokimane|deepfake|wedding" -o out/atrioc_stance

  subjects  Same as sample, but for several subjects across subs at once (sentiment toward each subject):
          python3 stance.py subjects data/*.json --subject "Trump=trump|maga" --subject "Hasan=hasan|hasanabi" \
              --cells "Destiny:Trump" "Destiny:Hasan" "Hasan_Piker:Trump" -o out/topics_stance
          (omit --cells to take every sub x subject pair with at least --min-mentions mentions)
          The sheet shows each item's subject (the coder needs it) but never its sub.

  tally   Join codes to the key and report shares per sub with 95% intervals, plus how
          upvotes treated each side.
          python3 stance.py tally --key out/atrioc_stance/stance_key.csv \
              --codes out/atrioc_stance/codes.csv -o out/atrioc_stance

  agree   Compare two coders on the items both coded (Cohen's kappa).
          python3 stance.py agree --codes out/a/codes.csv --codes2 out/a/codes_second.csv

Codes (one per item, CSV columns: item,code):
  P  for the target: defends them, minimizes the offense, or attacks the critic for raising it
  A  against the target: holds them culpable, or backs the critic's position
  B  both: concedes the critic's feelings or point are valid AND objects to how or when it was raised
  N  neither: jokes, questions, facts with no lean, off-topic, unclear
The full rubric with examples is in SKILL.md.
"""
import argparse, csv, math, os, random, re, statistics as st, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reddit_io import load_reddit

CODES = ("P", "A", "B", "N")


def cmd_sample(a):
    target = re.compile(rf"\b(?:{a.target})\b", re.I)
    context = re.compile(a.context, re.I) if a.context else None
    rows = load_reddit(a.inputs, [x.strip() for x in a.skip_authors.split(",") if x.strip()])
    titles = {r["thread"]: r["title"] for r in rows if r["is_post"]}
    # threads about the dispute: title names the target and matches the context
    hot = {t for t, ti in titles.items() if target.search(ti) and (context is None or context.search(ti))}
    pool = defaultdict(list)
    for r in rows:
        if r["removed"]:
            continue
        text = (r["title"] + " " + r["body"]).strip()
        named = target.search(text) and (context is None or context.search(text) or r["thread"] in hot)
        in_hot = r["thread"] in hot and len(text.split()) >= a.min_words
        if named or in_hot:
            pool[r["sub"]].append(r)
    rnd = random.Random(a.seed)
    items = []
    for sub, rs in sorted(pool.items()):
        take = rs if len(rs) <= a.per_sub else rnd.sample(rs, a.per_sub)
        for r in take:
            text = (r["title"] + " | " + r["body"]) if r["is_post"] else r["body"]
            items.append({"sub": sub, "score": r["score"], "thread": titles.get(r["thread"], "")[:120],
                          "text": " ".join(text.split())[:a.max_chars]})
    rnd.shuffle(items)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "stance_sheet.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["item", "text"])
        for i, it in enumerate(items):
            w.writerow([i, it["text"]])
    with open(os.path.join(a.out, "stance_key.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["item", "subreddit", "score", "thread"])
        for i, it in enumerate(items):
            w.writerow([i, it["sub"], it["score"], it["thread"]])
    with open(os.path.join(a.out, "codes.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["item", "code"])
        for i in range(len(items)):
            w.writerow([i, ""])
    print("relevant items per sub:", {s: len(v) for s, v in sorted(pool.items())})
    print(f"sampled {len(items)} items (up to {a.per_sub} per sub), shuffled across subs")
    print(f"code them blind from {a.out}/stance_sheet.csv in batches of ~100; fill {a.out}/codes.csv; "
          f"do not open stance_key.csv until tally")


def cmd_subjects(a):
    subjects = {}
    for spec in a.subject:
        name, _, rx = spec.partition("=")
        if not rx:
            sys.exit(f"--subject '{spec}' must look like Name=regex")
        subjects[name.strip()] = re.compile(rf"\b(?:{rx})\b", re.I)
    rows = load_reddit(a.inputs, [x.strip() for x in a.skip_authors.split(",") if x.strip()])
    pool = defaultdict(list)
    for r in rows:
        if r["removed"]:
            continue
        text = (r["title"] + " " + r["body"]).strip()
        if len(text.split()) < a.min_words:
            continue
        for name, rx in subjects.items():
            if rx.search(text):
                pool[(r["sub"], name)].append(r)
    if a.cells:
        cells = []
        for c in a.cells:
            sub, _, name = c.partition(":")
            if name not in subjects:
                sys.exit(f"cell '{c}': subject '{name}' not defined with --subject")
            cells.append((sub, name))
    else:
        cells = sorted(k for k, v in pool.items() if len(v) >= a.min_mentions)
    rnd = random.Random(a.seed)
    items = []
    for cell in cells:
        rs = pool.get(cell, [])
        take = rs if len(rs) <= a.per_cell else rnd.sample(rs, a.per_cell)
        for r in take:
            text = (r["title"] + " | " + r["body"]) if r["is_post"] else r["body"]
            items.append({"sub": cell[0], "subject": cell[1], "score": r["score"],
                          "text": " ".join(text.split())[:a.max_chars]})
        print(f"  r/{cell[0]} x {cell[1]}: {len(rs)} mentions, sampled {len(take)}")
    rnd.shuffle(items)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "stance_sheet.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["item", "subject", "text"])
        for i, it in enumerate(items):
            w.writerow([i, it["subject"], it["text"]])
    with open(os.path.join(a.out, "stance_key.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["item", "subreddit", "subject", "score"])
        for i, it in enumerate(items):
            w.writerow([i, it["sub"], it["subject"], it["score"]])
    with open(os.path.join(a.out, "codes.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["item", "code"])
        for i in range(len(items)):
            w.writerow([i, ""])
    print(f"sampled {len(items)} items across {len(cells)} sub x subject cells, shuffled; "
          f"code blind from {a.out}/stance_sheet.csv (sentiment toward the listed subject)")


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(100 * (c - m)), round(100 * (c + m)))


def read_codes(path):
    out = {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        c = (r.get("code") or "").strip().upper()
        if c:
            if c not in CODES:
                sys.exit(f"item {r['item']}: code '{c}' is not one of {CODES}")
            out[int(r["item"])] = c
    return out


def cmd_tally(a):
    key = {int(r["item"]): r for r in csv.DictReader(open(a.key, encoding="utf-8"))}
    codes = read_codes(a.codes)
    if a.corrections:
        fixes = read_codes(a.corrections)
        print(f"applying {len(fixes)} post-unblinding corrections; report them separately and have a second coder confirm")
        codes.update(fixes)
    multi = any("subject" in r for r in key.values())
    group = (lambda k: f"{k['subreddit']} | {k['subject']}") if multi else (lambda k: k["subreddit"])
    missing = sorted(set(key) - set(codes))
    if missing:
        print(f"warning: {len(missing)} sampled items have no code (e.g. {missing[:5]}); they are left out")
    by = defaultdict(Counter); scores = defaultdict(lambda: defaultdict(list))
    for i, c in codes.items():
        k = key[i]; g = group(k); by[g][c] += 1; scores[g][c].append(int(float(k["score"] or 0)))
    rows, total = [], Counter()
    for sub, v in sorted(by.items(), key=lambda kv: -sum(kv[1].values())):
        total += v
        side = v["P"] + v["A"] + v["B"]
        med = lambda c: st.median(scores[sub][c]) if scores[sub][c] else ""
        lo, hi = wilson(v["P"], side)
        rows.append({"group": sub, "coded": sum(v.values()), "side_takers": side,
                     "net": round(100 * (v["P"] - v["A"]) / side) if side else "",
                     "for_pct": round(100 * v["P"] / side) if side else "", "for_ci": f"{lo}-{hi}" if side else "",
                     "against_pct": round(100 * v["A"] / side) if side else "",
                     "both_pct": round(100 * v["B"] / side) if side else "",
                     "neither": v["N"], "median_score_for": med("P"), "median_score_against": med("A"),
                     "small_sample": "yes" if side < 30 else ""})
    side = total["P"] + total["A"] + total["B"]
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "stance_tally.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    label = "Sub | Subject" if multi else "Sub"
    md = [f"| {label} | Coded | Took a side | For | Against | Both | Net | Median score for / against |",
          "|" + "---|" * (len(label.split("|")) + 7)]
    for r in sorted(rows, key=lambda r: r["group"]):
        flag = " (small)" if r["small_sample"] else ""
        md.append(f"| r/{r['group']} | {r['coded']} | {r['side_takers']}{flag} | {r['for_pct']}% ({r['for_ci']}) | "
                  f"{r['against_pct']}% | {r['both_pct']}% | {r['net']:+} | {r['median_score_for']} / {r['median_score_against']} |"
                  if r["side_takers"] else f"| r/{r['group']} | {r['coded']} | 0 | | | | | |" + (" |" if multi else ""))
    md.append("")
    md.append(f"All subs: {side} of {sum(total.values())} coded items took a side; for {round(100 * total['P'] / side)}%, "
              f"against {round(100 * total['A'] / side)}%, both {round(100 * total['B'] / side)}%." if side else "No side-takers.")
    md.append("Percentages are of side-takers; parentheses give the 95% interval for 'for'. Net = for minus against, "
              "as a share of side-takers (+100 all for, -100 all against). Groups under 30 side-takers are marked small.")
    open(os.path.join(a.out, "stance_tally.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md)); print("wrote", path)


def cmd_agree(a):
    c1, c2 = read_codes(a.codes), read_codes(a.codes2)
    both = sorted(set(c1) & set(c2))
    if len(both) < 20:
        sys.exit(f"only {len(both)} items coded by both; double-code at least 20% of the sample")
    po = sum(c1[i] == c2[i] for i in both) / len(both)
    f1, f2 = Counter(c1[i] for i in both), Counter(c2[i] for i in both)
    pe = sum(f1[c] * f2[c] for c in CODES) / len(both) ** 2
    kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
    conf = Counter((c1[i], c2[i]) for i in both if c1[i] != c2[i])
    print(f"items coded by both: {len(both)} | agreement {100 * po:.0f}% | Cohen's kappa {kappa:.2f} "
          f"({'good' if kappa >= 0.6 else 'moderate' if kappa >= 0.4 else 'weak: tighten the rubric and recode'})")
    print("most common disagreements (coder1, coder2):", conf.most_common(5))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("sample")
    s.add_argument("inputs", nargs="+")
    s.add_argument("--target", required=True, help="regex naming the person or side, e.g. 'atrioc|big a'")
    s.add_argument("--context", default="", help="regex for the dispute, e.g. 'poki|pokimane|deepfake|wedding'")
    s.add_argument("--per-sub", type=int, default=120)
    s.add_argument("--min-words", type=int, default=4)
    s.add_argument("--max-chars", type=int, default=300)
    s.add_argument("--seed", type=int, default=11)
    s.add_argument("--skip-authors", default="")
    s.add_argument("-o", "--out", default="stance_out")
    t = sp.add_parser("tally")
    t.add_argument("--key", required=True); t.add_argument("--codes", required=True); t.add_argument("-o", "--out", default="stance_out")
    t.add_argument("--corrections", default=None, help="codes changed after unblinding (item,code); applied and counted")
    m = sp.add_parser("subjects")
    m.add_argument("inputs", nargs="+")
    m.add_argument("--subject", action="append", required=True, help="Name=regex, repeatable")
    m.add_argument("--cells", nargs="*", default=None, help="sub:Subject pairs to sample (default: all with enough mentions)")
    m.add_argument("--per-cell", type=int, default=25)
    m.add_argument("--min-mentions", type=int, default=50)
    m.add_argument("--min-words", type=int, default=5)
    m.add_argument("--max-chars", type=int, default=300)
    m.add_argument("--seed", type=int, default=5)
    m.add_argument("--skip-authors", default="")
    m.add_argument("-o", "--out", default="stance_out")
    g = sp.add_parser("agree")
    g.add_argument("--codes", required=True); g.add_argument("--codes2", required=True)
    a = ap.parse_args()
    {"sample": cmd_sample, "subjects": cmd_subjects, "tally": cmd_tally, "agree": cmd_agree}[a.cmd](a)


if __name__ == "__main__":
    main()
