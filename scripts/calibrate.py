#!/usr/bin/env python3
"""Calibrate analyze.py against known bots.

Known bots come from r/BotBouncer (download its posts from Arctic Shift), from a plain text file
with one username per line, or both. Matches them against an analyze.py output folder using its
.salt, then reports how the detector did:
  recall      share of known bots present in the data that got any tier / likely+ / high
  flag rate   share of all other accounts that got likely+ (an upper bound on false positives,
              since some unflagged-by-BotBouncer accounts may be bots too)

Usage:
  python3 calibrate.py --analysis out --botbouncer r_BotBouncer_posts.jsonl
  python3 calibrate.py --analysis out --bots known_bots.txt
"""
import argparse, csv, hashlib, os, re, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reddit_io import iter_records

USER = re.compile(r"(?:\bu/|/user/|/u/)([A-Za-z0-9_-]{3,20})")


def botbouncer_users(paths):
    names = set()
    for r in iter_records(paths):
        if r.get("link_flair_text") != "banned":
            continue  # pending, organic (judged human), purged or unresolved
        text = " ".join(str(r.get(k) or "") for k in ("title", "url", "selftext"))
        for m in USER.findall(text):
            if m.lower() not in {"botbouncer", "automoderator"}:
                names.add(m)
        # Bot Bouncer often titles posts with the bare username
        title = (r.get("title") or "").strip()
        if re.fullmatch(r"[A-Za-z0-9_-]{3,20}", title):
            names.add(title)
    return names


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--analysis", required=True, help="analyze.py output folder (needs accounts.csv and .salt)")
    ap.add_argument("--botbouncer", nargs="*", default=[], help="r/BotBouncer post dumps")
    ap.add_argument("--bots", default=None, help="text file, one known-bot username per line")
    a = ap.parse_args()

    known = botbouncer_users(a.botbouncer) if a.botbouncer else set()
    if a.bots:
        known |= {re.sub(r"^/?u/", "", l.strip()) for l in open(a.bots) if l.strip()}
    if not known:
        sys.exit("No known bots loaded.")
    salt = open(os.path.join(a.analysis, ".salt")).read().strip()
    h = lambda u: "acct_" + hashlib.sha256((salt + u).encode()).hexdigest()[:10]
    known_ids = {h(u) for u in known} | set(known)  # revealed names match directly

    accounts = list(csv.DictReader(open(os.path.join(a.analysis, "accounts.csv"), encoding="utf-8")))
    bots = [r for r in accounts if r["account"] in known_ids]
    rest = [r for r in accounts if r["account"] not in known_ids]
    tiers = Counter(r["tier"] or "none" for r in bots)
    pct = lambda n, d: f"{100 * n / d:.1f}%" if d else "n/a"
    likely = lambda rs: sum(r["tier"] in ("likely", "high") for r in rs)
    print(f"known bots loaded: {len(known)} | present in this data: {len(bots)} of {len(accounts)} accounts")
    if bots:
        print(f"  tiers among known bots: {dict(tiers)}")
        print(f"  recall: any tier {pct(sum(r['tier'] != '' for r in bots), len(bots))} · likely+ {pct(likely(bots), len(bots))} · high {pct(tiers['high'], len(bots))}")
        print(f"  median items per known bot: {sorted(int(r['items']) for r in bots)[len(bots) // 2]}")
    print(f"  flag rate among other accounts (likely+): {pct(likely(rest), len(rest))}")
    out = os.path.join(a.analysis, "calibration.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        if bots:
            w = csv.DictWriter(fh, fieldnames=list(bots[0].keys())); w.writeheader(); w.writerows(bots)
    print("missed bots and their signals written to", out, "- read them to see which signals would have caught them")


if __name__ == "__main__":
    main()
