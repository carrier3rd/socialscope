"""Weekly Bot Bouncer status check for Path 1 (docs/bot-publishing-plan.md, build step 2). Written Nov 11, 2026.

Run by ops/botfinds_weekly.sh after it pulls recent r/BotBouncer posts into reddit_pulls/bb_weekly/. Reads every
Bot Bouncer pull on the laptop (reddit_pulls/bb_*/*/r_BotBouncer_posts_*.zip) and keeps the latest listing per
account, as scripts/bb_inventory.py does (newest post wins; on a tie, the file that sorts later, i.e. the newer pull).

Updates, private, in ~/socialscope_data/botfinds/:
  tracker.csv             every row past to_submit: bb_flair, bb_listed_utc, bb_link, bb_checked_utc, and status
                          banned / pending / cleared / gone (purged) / submitted (not listed yet). banned_since keeps the
                          first date a ban was seen. bb_checked_utc is what the site's "rechecked within 7 days" rule
                          (CLAUDE.md rule 5) reads.
  candidates_private.csv  bb_flair_now: candidates Bot Bouncer has listed on its own since the evidence files were
                          built (reviewers can skip those).
stdout carries counts only.

Caveat: Arctic Shift stores a post's flair as captured, so a listing shown as pending may have been decided since.
Pending rows are re-pulled each week; a pending row older than 14 days should be checked by hand on the listing link.

Usage: python3 -I scripts/botfinds/weekly_check.py
"""
import csv, glob, os, sys
from collections import Counter
from datetime import datetime, timezone

REPO = os.path.expanduser("~/socialscope")
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "scripts", "botfinds"))
import bb_inventory  # noqa: E402
from review_merge import BF, TRACK_COLS, read, write  # noqa: E402

BB_GLOB = os.path.expanduser("~/socialscope_data/reddit_pulls/bb_*/*/r_BotBouncer_posts_*.zip")
STATUS = {"banned": "banned", "pending": "pending", "purged": "gone"}   # anything else Bot Bouncer sets = cleared
OPEN = ("submitted", "pending", "banned", "cleared", "gone")


def listings():
    paths = sorted(glob.glob(BB_GLOB))
    latest = {}
    for post in bb_inventory.iter_records(paths):
        u = bb_inventory.extract_username(post)
        ts = post.get("created_utc")
        if not u or ts is None:
            continue
        ts = int(float(ts))
        prev = latest.get(u.lower())
        if prev is None or ts >= prev[1]:
            link = post.get("permalink") or ""
            if link.startswith("/"):
                link = "https://www.reddit.com" + link
            latest[u.lower()] = (bb_inventory.normalize_flair(post.get("link_flair_text")), ts, link)
    return latest, len(paths)


def day(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def main():
    latest, n = listings()
    now = datetime.now(timezone.utc)
    print(f"Bot Bouncer pulls read: {n} files, {len(latest):,} listed accounts, newest listing "
          f"{day(max(v[1] for v in latest.values())) if latest else 'n/a'}")

    track_path = os.path.join(BF, "tracker.csv")
    track = read(track_path)
    moved = Counter()
    for t in track.values():
        if t.get("status") not in OPEN:
            continue
        hit = latest.get((t.get("username") or "").lower())
        old = t.get("status")
        if hit:
            flair, ts, link = hit
            t.update(bb_flair=flair, bb_listed_utc=day(ts), bb_link=link)
            t["status"] = STATUS.get(flair, "cleared")
            if t["status"] == "banned" and not t.get("banned_since"):
                t["banned_since"] = now.strftime("%Y-%m-%d")
        t["bb_checked_utc"] = now.strftime("%Y-%m-%d %H:%M")
        if t["status"] != old:
            moved[f"{old}->{t['status']}"] += 1
    if track:
        write(track_path, TRACK_COLS, list(track.values()))
    print("tracker:", dict(Counter(t.get("status") for t in track.values())) or "empty", "; changes:", dict(moved) or "none")

    cand_path = os.path.join(BF, "candidates_private.csv")
    cand = read(cand_path)
    on_own = Counter()
    for c in cand.values():
        hit = latest.get((c.get("username") or "").lower())
        c["bb_flair_now"] = hit[0] if hit else ""
        if hit and c["account"] not in track:
            on_own[hit[0]] += 1
    if cand:
        cols = list(next(iter(cand.values())).keys())
        write(cand_path, cols, list(cand.values()))
    print(f"candidates: {len(cand)}; listed by Bot Bouncer on its own since: {sum(on_own.values())} {dict(on_own)}")


if __name__ == "__main__":
    main()
