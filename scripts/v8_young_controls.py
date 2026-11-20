#!/usr/bin/env python3
"""Choose the v8 young/light control sample (design frozen in docs/v8-predictions.md, e4e3e23). Written Nov 20, 2026.

From the authors of the Oct 27 and Nov 3 weekly pulls: those whose account ID is among the newest 25% of those
authors' IDs, minus every account with any Bot Bouncer listing and every account in the Nov 10-16 bot check; then
1,000 at random (seed 7). Writes ~/socialscope_data/v8/young_controls/users_to_pull.txt (private). Prints counts only.
"""
import csv, glob, os, random, sys
REPO = os.path.expanduser("~/socialscope")
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "scripts", "repull_run")); sys.path.insert(0, os.path.join(REPO, "scripts"))
import common as C  # noqa: E402
from socialscope import signals  # noqa: E402
from nov10_botcheck_score import bb_listings  # noqa: E402

OUT = os.path.join(C.DATA, "v8", "young_controls")
ids = {}
for wk in ("oct27", "nov03"):
    for p in sorted(glob.glob(os.path.join(C.DATA, "reddit_pulls", wk, "**", "*.zip"), recursive=True)):
        for r in C.iter_jsonl(p):
            a = r.get("author")
            v = signals.account_id_number(r.get("author_fullname"))
            if a and v and a not in ("[deleted]", "AutoModerator"):
                ids[a] = v
first, _ = bb_listings()
nov10 = {r[list(r)[0]].lower() for r in csv.DictReader(open(os.path.join(C.DATA, "nov10_botcheck", "shortlist", "groups.csv")))}
cut = sorted(ids.values())[int(0.75 * len(ids))]
young = sorted(a for a, v in ids.items() if v >= cut)
pool = [a for a in young if a.lower() not in first and a.lower() not in nov10]
random.Random(7).shuffle(pool)
pick = sorted(pool[:1000])
os.makedirs(OUT, mode=0o700, exist_ok=True)
with open(os.path.join(OUT, "users_to_pull.txt"), "w") as fh:
    fh.write("\n".join(pick) + "\n")
os.chmod(os.path.join(OUT, "users_to_pull.txt"), 0o600)
print(f"authors with an ID: {len(ids)}; newest 25%: {len(young)}; after removing listed and Nov 10 accounts: {len(pool)}; chosen: {len(pick)}")
