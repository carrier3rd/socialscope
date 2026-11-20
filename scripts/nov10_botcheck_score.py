#!/usr/bin/env python3
"""Score the Nov 10-16 bot check (design and predictions: docs/nov10-botcheck-predictions.md, da93a36).

Every pulled account is scored with the frozen v7.1 model exactly as the public lookup runs it
(socialscope/lookup_core.analyze, site/public/lookup/model.json), anchored at the account's last item. Then the
eight predictions are scored. Written Nov 20, 2026.

Privacy: usernames are read from and written to ~/socialscope_data/nov10_botcheck/ only (scored_private.csv,
review_candidates_private.csv). stdout and the aggregates JSON hold counts and rates only.

Usage: python3 -I scripts/nov10_botcheck_score.py [--out scored_private.csv]
"""
import argparse, csv, glob, io, json, math, os, re, sys, zipfile
from collections import defaultdict
from datetime import datetime, timezone, timedelta

REPO = os.path.expanduser("~/socialscope")
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts", "repull_run"))
import common as C  # noqa: E402
from socialscope import lookup_core as LC  # noqa: E402

D = os.path.join(C.DATA, "nov10_botcheck")
WEEK = os.path.join(C.DATA, "reddit_pulls", "nov10")
ET = timezone(timedelta(hours=-5))  # EST all week (DST ended Nov 1)
WEEK_START = datetime(2026, 11, 10, tzinfo=ET).timestamp()
WEEK_END = datetime(2026, 11, 17, tzinfo=ET).timestamp()
USER_RX = re.compile(r"/(?:user|u)/([A-Za-z0-9_-]{3,20})|^Overview for ([A-Za-z0-9_-]{3,20})")


def wilson(k, n, z=1.96):
    if not n:
        return [None, None]
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [(c - h) / d, (c + h) / d]


def bb_listings():
    """name(lower) -> (earliest listing time, earliest *banned* listing time or None), from every r/BotBouncer pull.
    The flair is the verdict at pull time; a listing counts as banned if any pull saw it banned."""
    first, first_banned = {}, {}
    for p in sorted(glob.glob(C.BB_GLOB)):
        with zipfile.ZipFile(p) as z:
            for n in z.namelist():
                with z.open(n) as fh:
                    for line in io.TextIOWrapper(fh, encoding="utf-8", errors="replace"):
                        try:
                            r = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        m = USER_RX.search(r.get("url") or "") or USER_RX.search(r.get("title") or "")
                        if not m:
                            continue
                        u = (m.group(1) or m.group(2)).lower()
                        t = float(r.get("created_utc") or 0)
                        first[u] = min(first.get(u, t), t)
                        if r.get("link_flair_text") == "banned":
                            first_banned[u] = min(first_banned.get(u, t), t)
    return first, first_banned


def week_authors():
    seen = set()
    for p in sorted(glob.glob(os.path.join(WEEK, "**", "*.zip"), recursive=True)):
        for r in C.iter_jsonl(p):
            a = r.get("author")
            t = float(r.get("created_utc") or 0)
            if a and a not in ("[deleted]", "AutoModerator") and WEEK_START <= t < WEEK_END:
                seen.add(a.lower())
    return seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="scored_private.csv")
    a = ap.parse_args()
    groups = {r["account"] if "account" in r else r[list(r)[0]]: r for r in csv.DictReader(open(os.path.join(D, "shortlist", "groups.csv")))}
    by = defaultdict(list)
    for k in ("posts", "comments"):
        for r in C.iter_jsonl(os.path.join(D, "histories", f"nov10_{k}.zip")):
            by[r.get("author")].append(r)
    oldest = json.load(open(os.path.join(D, "histories", "nov10_oldest.json")))
    M = json.load(open(os.path.join(REPO, "site", "public", "lookup", "model.json")))
    th = M["thresholds"]
    strict = th["1%"]
    print(f"model {M['tag']}; strict line {strict:.4f}; {len(groups)} accounts in groups.csv; {len(by)} authors in the pull",
          flush=True)

    rows = []
    for i, (u, g) in enumerate(groups.items()):
        R = LC.analyze(u, by.get(u, []), oldest.get(u), M)
        row = {"account": C.H(u), "username": u, "group": g["group"], "reasons": g.get("reasons", "")}
        if "error" in R:
            row.update(status=R["error"])
        else:
            row.update(status="ok", n_items=R["n_items"], score=round(R["score"], 6), rating=R["rating_text"],
                       strict=int(R["score"] >= strict), line2=int(R["score"] >= th["2%"]), line5=int(R["score"] >= th["5%"]),
                       sh=int(R["solicit_handle"]), sb=int(R["solicit_broad"]),
                       gate=int(R["score"] >= strict and (R["solicit_handle"] or R["solicit_broad"])),
                       last_item=int(R["last_item"]), age_days=round(R["age_days"], 1) if R["age_days"] is not None else "")
        rows.append(row)
        if (i + 1) % 50 == 0:
            print(f"scored {i + 1}/{len(groups)}", flush=True)
    cols = ["account", "username", "group", "reasons", "status", "n_items", "score", "rating", "strict", "line2", "line5",
            "sh", "sb", "gate", "last_item", "age_days"]
    with open(os.path.join(D, a.out), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    os.chmod(os.path.join(D, a.out), 0o600)

    # ---- predictions
    first, first_banned = bb_listings()
    authors = week_authors()
    known = {u for u, t in first_banned.items() if t < WEEK_START}
    later = {u for u, t in first_banned.items() if WEEK_START <= first.get(u, t) < WEEK_END and u not in known}
    ok = [r for r in rows if r["status"] == "ok"]
    grp = lambda name: [r for r in ok if r["group"] == name]
    rate = lambda rs, key: (sum(r[key] for r in rs), len(rs))
    out = {"authors_week": len(authors), "known_active": len(known & authors), "later_active": len(later & authors),
           "known_in_groups": len(grp("known_bot")), "not_scored": {g: sum(1 for r in rows if r["group"] == g and r["status"] != "ok")
                                                                  for g in ("shortlist", "control", "known_bot")}}
    for g in ("known_bot", "control", "shortlist"):
        for key in ("strict", "gate", "line2", "line5"):
            k, n = rate(grp(g), key)
            out[f"{g}_{key}"] = [k, n, k / n if n else None, wilson(k, n)]
    later_in = [r for r in ok if r["username"].lower() in later]
    out["later_in_scored"] = {"n": len(later_in), "by_group": {g: sum(r["group"] == g for r in later_in) for g in ("shortlist", "control")},
                              "strict": sum(r["strict"] for r in later_in), "gate": sum(r["gate"] for r in later_in)}
    listed = known | later | set(first)  # any listing at all (banned, pending, organic...) counts as already checked
    review = [r for r in grp("shortlist") if r["gate"] and r["username"].lower() not in listed]
    out["review_n"] = len(review)
    sl, ct = out["shortlist_strict"], out["control_strict"]
    out["ratio_shortlist_control_strict"] = (sl[2] / ct[2]) if ct[2] else None
    with open(os.path.join(D, "review_candidates_private.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(review)
    os.chmod(os.path.join(D, "review_candidates_private.csv"), 0o600)
    json.dump(out, open(os.path.join(D, "aggregates.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
