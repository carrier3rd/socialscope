"""Path 1 evidence files for bots Bot Bouncer hasn't found (docs/bot-publishing-plan.md). Written Nov 11, 2026.

Reads only data already on the laptop:
  - repull/out/accounts_repull.csv and accounts_repull_check.csv (detector scores, hashed ids, two identical runs);
  - repull/out/features_repull.csv (signals);
  - repull/work/groups_private.csv (username for each hashed id; private);
  - reddit_pulls/bb_*/  (r/BotBouncer posts: latest listing per account, as scripts/bb_inventory.py builds it);
  - re-pulled and older history zips (the items shown in each file).

Candidates: control accounts (unlisted by Bot Bouncer when the groups were built) that the detector flags at the
strict setting (results_repull.md, "full" model at the 1% target: threshold 0.4828, test false-alarm rate 1.7%).
Test-half controls use score_full; train-half controls use their cross-validated score (oof_score_full), since
their in-sample score has seen their label. Both scoring runs must agree (laptop RAM fault, Nov 6). Accounts that
any Bot Bouncer pull lists, with any flair, are dropped: they are already in Bot Bouncer's hands.

Writes, all under ~/socialscope_data/botfinds/ (never committed; folder mode 700, files 600):
  packets/<hashed id>.md     one evidence file per account (username inside; the file name is hashed)
  candidates_private.csv     hashed id, username, score, source, signals, packet path
  review_user.csv, review_cloud.csv   one blank row per new account for each reviewer (blind: read only your own)
Existing packets and filled-in review rows are never overwritten. stdout carries counts only, never names.

A flag is a lead, not a finding. Nothing here is published; review_merge.py decides what goes to Bot Bouncer.

Usage: python3 -I scripts/botfinds/build_packets.py [--dry-run] [--rebuild]
"""
import argparse, csv, glob, os, re, sys
from collections import Counter
from datetime import datetime, timezone

REPO = os.path.expanduser("~/socialscope")
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "scripts", "repull_run"))
import common as C  # noqa: E402
import bb_inventory  # noqa: E402
from socialscope import hijack, prewindow  # noqa: E402

THRESHOLD = 0.4828      # results_repull.md line 19: full model, 1% FPR target (strict setting)
CTL_GROUPS = ("test_ctl", "train_ctl")
BF = os.path.join(C.DATA, "botfinds")
PACKETS = os.path.join(BF, "packets")
MAX_POSTS = 20
DAY = 86400
REVIEW_COLS = ["account", "packet", "call", "reason", "reviewed_utc"]   # call: bot / not bot / unsure

PLAIN = {
    "sh": "2+ posts carry a contact handle or solicitation template (Telegram/Snapchat/'ask for my menu' and similar)",
    "sb": "an established history that turns to NSFW or solicitation posting",
    "primary": "v7.1 primary-tier rule fired",
    "stock_name": "username looks auto-generated (Word_Word1234 style)",
    "topic_hopper": "spreads over unusually many unrelated subreddits",
    "dormant_then_burst": "long silence, then a burst of activity",
}


def fl(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def utc(ts):
    return datetime.fromtimestamp(int(float(ts)), timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def private_write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.chmod(path, 0o600)


def candidates():
    out = os.path.join(C.OUT)
    A = {r["account"]: r for r in csv.DictReader(open(os.path.join(out, "accounts_repull.csv")))}
    B = {r["account"]: r for r in csv.DictReader(open(os.path.join(out, "accounts_repull_check.csv")))}
    F = {r["account"]: r for r in csv.DictReader(open(os.path.join(out, "features_repull.csv")))}
    picked, skipped_disagree = [], 0
    for k, r in A.items():
        if r["group"] not in CTL_GROUPS:
            continue
        col = "score_full" if r["group"] == "test_ctl" else "oof_score_full"
        s, s2 = fl(r.get(col)), fl(B.get(k, {}).get(col))
        if s is None or s < THRESHOLD:
            continue
        if s2 is None or abs(s - s2) > 1e-9:
            skipped_disagree += 1
            continue
        picked.append((k, s, r, F.get(k, {})))
    return picked, skipped_disagree


def bb_listings():
    paths = sorted(glob.glob(C.BB_GLOB))
    latest, _ = bb_inventory.build_inventory(bb_inventory.iter_records(paths))
    newest = max((v[2] for v in latest.values()), default=0)
    return latest, newest, len(paths)


def history_files():
    hp = sorted(glob.glob(os.path.join(C.PULL_DIR, "repull_*_posts.zip")) + glob.glob(os.path.join(C.PULL_DIR, "repull_*_comments.zip")))
    hp += [p for n in C.OLD_HIST for p in (os.path.join(C.HIST_DIR, f"{n}_posts.zip"), os.path.join(C.HIST_DIR, f"{n}_comments.zip"))
           if os.path.exists(p)]
    return hp


def load_items(names):
    """{username: [items]} across re-pulled and older histories, deduped by id. A byte prefilter skips json parsing
    for lines that can't belong to a wanted author."""
    import json, zipfile
    pat = re.compile(rb'"author"\s*:\s*"(' + b"|".join(re.escape(n.encode()) for n in names) + rb')"')
    got = {}
    for p in history_files():
        z = zipfile.ZipFile(p)
        for member in z.namelist():
            with z.open(member) as fh:
                for line in fh:
                    if not pat.search(line):
                        continue
                    try:
                        r = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    a = r.get("author")
                    if a in names:
                        got.setdefault(a, {})[r.get("id")] = C.slim(r)
    return {a: sorted(d.values(), key=lambda x: float(x.get("created_utc") or 0)) for a, d in got.items()}


def is_post(x):
    return "title" in x


def text(x):
    t = x.get("body") if "body" in x else f"{x.get('title') or ''} - {x.get('selftext') or ''}".strip(" -")
    return re.sub(r"\s+", " ", t or "").strip()


def takeover(items):
    """Descriptive only (the Path 2 bar is frozen separately in docs/bot-publishing-predictions.md): measured over the
    last 30 days of pulled activity, 50+ earlier items and most recent items in subreddits never used before.
    Returns (is_break, start_utc of the bot period or None, new_sub_share, n_earlier)."""
    if not items:
        return False, None, 0.0, 0
    last = float(items[-1]["created_utc"])
    earlier, window = prewindow.partition_history(items, last)
    share = prewindow.compute_new_subreddit_share(earlier, window)
    if len(earlier) >= 50 and share > 0.5:
        used = {str(x.get("subreddit") or "").lower() for x in earlier}
        first_new = next((x for x in window if str(x.get("subreddit") or "").lower() not in used), window[0])
        return True, float(first_new["created_utc"]), share, len(earlier)
    return False, None, share, len(earlier)


def packet(hid, name, score, row, feat, items, bb_newest):
    sh, sb = hijack.solicit_handle(items), hijack.solicit_broad(items)
    brk, start, share, n_earlier = takeover(items)
    period_start = start if brk else (float(items[-1]["created_utc"]) - 30 * DAY if items else 0)
    bot = [x for x in items if float(x["created_utc"]) >= period_start]
    before = [x for x in items if float(x["created_utc"]) < period_start]
    fired = [PLAIN["sh"]] if sh else []
    if sb and not sh:
        fired.append(PLAIN["sb"])
    if str(row.get("primary")) in ("1", "True"):
        fired.append(PLAIN["primary"])
    fired += [PLAIN.get(f, f) for f in (feat.get("flag_list") or "").split("+") if f]
    L = [f"# Evidence file {hid}", "",
         "PRIVATE. Contains a username. Never commit, paste or publish. A detector flag is a lead, not a finding.", "",
         f"- **Account:** u/{name}  (https://www.reddit.com/user/{name})",
         f"- **Detector score:** {score:.3f} (strict setting flags at {THRESHOLD}; about 2 in 100 ordinary accounts also pass it)",
         f"- **Where it came from:** {feat.get('cohort_source') or row.get('group')} controls, scored in the Nov 2026 re-pull",
         f"- **Bot Bouncer:** not listed in any pull through {utc(bb_newest) if bb_newest else 'n/a'}. Check the live listing before submitting.",
         f"- **Signals that fired:** " + ("; ".join(fired) if fired else "none of the named rules; the score comes from the combined features"),
         f"- **Takeover break:** " + (f"yes, from {utc(start)}: {n_earlier} earlier items, then {share:.0%} of the last 30 days' items in subreddits it had never used"
                                       if brk else f"no ({n_earlier} earlier items; {share:.0%} of the last 30 days' items in new subreddits)"),
         ""]
    if before:
        first, lastb = float(before[0]["created_utc"]), float(before[-1]["created_utc"])
        subs = Counter(str(x.get("subreddit") or "?") for x in before).most_common(5)
        L += ["## Earlier history (aggregate only)", "",
              f"{len(before)} items ({sum(1 for x in before if is_post(x))} posts, {sum(1 for x in before if not is_post(x))} comments), "
              f"{(lastb - first) / (365.25 * DAY):.1f} years active ({utc(first)[:10]} to {utc(lastb)[:10]}). "
              f"Top subreddits by count: " + ", ".join(f"r/{s} {n}" for s, n in subs) + ".", ""]
    head = "Bot period (from the takeover break on)" if brk else "Most recent 30 days of pulled activity"
    L += [f"## {head}: {len(bot)} items, newest {min(MAX_POSTS, len(bot))} shown", ""]
    for x in reversed(bot[-MAX_POSTS:]):
        kind = "post" if is_post(x) else "comment"
        t = text(x)
        L.append(f"- {utc(x['created_utc'])} · r/{x.get('subreddit')} · {kind}: {t[:400]}{'…' if len(t) > 400 else ''}")
    L += ["", "## Review", "",
          "Write your call in your own file only (review_user.csv or review_cloud.csv): bot / not bot / unsure, with one line of reasons.",
          "Two 'bot' calls are needed before it goes to Bot Bouncer. Any disagreement counts as unsure.", ""]
    return "\n".join(L), {"sh": int(sh), "sb": int(sb), "takeover": int(brk), "n_items": len(items), "n_bot_period": len(bot)}


def ensure_review(path, hids):
    rows = list(csv.DictReader(open(path, encoding="utf-8"))) if os.path.exists(path) else []
    have = {r["account"] for r in rows}
    added = 0
    for h in hids:
        if h not in have:
            rows.append({"account": h, "packet": f"packets/{h}.md", "call": "", "reason": "", "reviewed_utc": ""})
            added += 1
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=REVIEW_COLS)
        w.writeheader()
        w.writerows(rows)
    os.chmod(path, 0o600)
    return added


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="counts only; write nothing")
    ap.add_argument("--rebuild", action="store_true", help="rewrite existing packets (review rows are kept)")
    a = ap.parse_args()

    picked, disagree = candidates()
    print(f"flagged controls at the strict setting: {len(picked) + disagree} ({disagree} dropped: runs disagree)")
    print("by source:", dict(Counter(f.get("cohort_source") or r["group"] for _, _, r, f in picked)))

    names = {C.H(g["username"]): g["username"] for g in C.read_groups()}
    latest, bb_newest, n_bb = bb_listings()
    print(f"Bot Bouncer pulls read: {n_bb} files, newest listing {utc(bb_newest) if bb_newest else 'n/a'}")
    keep, listed, noname = [], Counter(), 0
    for k, s, r, f in picked:
        n = names.get(k)
        if not n:
            noname += 1
            continue
        if n.lower() in latest:
            listed[latest[n.lower()][1]] += 1
            continue
        keep.append((k, n, s, r, f))
    print(f"already listed by Bot Bouncer since grouping: {sum(listed.values())} {dict(listed)}; no username on file: {noname}")
    print(f"candidates: {len(keep)}")
    if a.dry_run:
        return

    os.makedirs(PACKETS, exist_ok=True)
    os.chmod(BF, 0o700)
    os.chmod(PACKETS, 0o700)
    todo = [c for c in keep if a.rebuild or not os.path.exists(os.path.join(PACKETS, f"{c[0]}.md"))]
    print(f"new packets to write: {len(todo)}")
    items = load_items({c[1] for c in todo}) if todo else {}
    cand_path = os.path.join(BF, "candidates_private.csv")
    old = {r["account"]: r for r in csv.DictReader(open(cand_path, encoding="utf-8"))} if os.path.exists(cand_path) else {}
    stats = Counter()
    for k, n, s, r, f in todo:
        its = items.get(n, [])
        if not its:
            stats["no_items"] += 1
        txt, info = packet(k, n, s, r, f, its, bb_newest)
        private_write(os.path.join(PACKETS, f"{k}.md"), txt)
        stats["sh"] += info["sh"]; stats["sb"] += info["sb"]; stats["takeover"] += info["takeover"]
        old[k] = {"account": k, "username": n, "score": f"{s:.4f}", "source": f.get("cohort_source") or r["group"],
                  "sh": info["sh"], "sb": info["sb"], "takeover": info["takeover"], "n_items": info["n_items"],
                  "packet": f"packets/{k}.md", "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    cols = ["account", "username", "score", "source", "sh", "sb", "takeover", "n_items", "packet", "built_utc"]
    with open(cand_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(old.values())
    os.chmod(cand_path, 0o600)
    hids = [c[0] for c in keep]
    au = ensure_review(os.path.join(BF, "review_user.csv"), hids)
    ac = ensure_review(os.path.join(BF, "review_cloud.csv"), hids)
    print(f"packets written: {len(todo)}; with handle template {stats['sh']}, broad turn {stats['sb']}, takeover break "
          f"{stats['takeover']}, no items found {stats['no_items']}")
    print(f"review rows added: user {au}, cloud {ac}")


if __name__ == "__main__":
    main()
