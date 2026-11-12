"""Public list of bots socialscope found and Bot Bouncer then banned (Path 1, build step 3). Written Nov 11, 2026.

Called by ops/publish_site.sh on every rebuild. Writes <out>/botfinds.json. The file is always written, with an empty
list when nothing qualifies, so a listing Bot Bouncer reverses comes off the site at the next rebuild. The site's
Bots tab stays hidden while the list is empty.

An account is listed only if all of these hold (CLAUDE.md rule 5):
  - tracker.csv status is "banned" and the row has a Bot Bouncer listing link;
  - bb_checked_utc (written by weekly_check.py) is no more than 7 days old;
  - we submitted it (it came through the two-reviewer process), so "found by socialscope" is true.
What is shown: the username, the Bot Bouncer listing link (the label is Bot Bouncer's, not ours), the dates, which
detector signals fired, and up to 10 bot-period posts. Posts appear only when the evidence file shows a takeover
break (posts from the break on) or the account has no earlier history at all. An account whose earlier history may
have been a real person's shows signals only. Contact handles inside posts are masked, so the site doesn't pass on
the spam, and so are other users' u/names.

Usage: python3 -I scripts/botfinds/build_site_bots.py --out <site data dir>
"""
import argparse, csv, json, os, re
from datetime import datetime, timedelta, timezone

BF = os.path.expanduser("~/socialscope_data/botfinds")
MAX_POSTS = 10
POST_RE = re.compile(r"^- (\d{4}-\d\d-\d\d \d\d:\d\d UTC) · r/(\S+) · (post|comment): (.*)$")
HANDLE_RE = re.compile(r"(?i)(\b(?:t[e3]l[e3]?g?r?a?m|tg|tele|snap(?:chat)?|sn[a-z]*ch?at|lnst[a-z]*|insta(?:gram)?|kik|"
                       r"whats?app|discord|session|wickr)\b\s*[:@\-]?\s*)(@?[\w.\-]{2,})")
AT_RE = re.compile(r"(?<![\w/])@[\w.\-]{2,}")
UNAME_RE = re.compile(r"(?i)\b(/?u/)([\w\-]{3,})")
LINK_RE = re.compile(r"(?i)\b(?:https?://|www\.)\S+|\b(?:t\.me|wa\.me|onlyfans\.com|fans\.ly)/\S*")


def read(path):
    return {r["account"]: r for r in csv.DictReader(open(path, encoding="utf-8"))} if os.path.exists(path) else {}


def mask(t, own):
    t = LINK_RE.sub("[link]", t)
    t = HANDLE_RE.sub(lambda m: m.group(1) + "[handle]", t)
    t = AT_RE.sub("@[handle]", t)
    return UNAME_RE.sub(lambda m: m.group(0) if m.group(2).lower() == own.lower() else m.group(1) + "[user]", t)


def posts_from_packet(path, own):
    """Bot-period posts from the evidence file, only when it shows a takeover break or no earlier history."""
    try:
        txt = open(path, encoding="utf-8").read()
    except OSError:
        return [], "no evidence file"
    takeover = "**Takeover break:** yes" in txt
    earlier = "## Earlier history" in txt
    if not takeover and earlier:
        return [], "earlier history may be a real person's; posts not shown"
    out = []
    for line in txt.splitlines():
        m = POST_RE.match(line)
        if m:
            out.append({"time": m.group(1), "sub": m.group(2), "kind": m.group(3), "text": mask(m.group(4), own)})
        if len(out) >= MAX_POSTS:
            break
    return out, ("posts from the takeover break on" if takeover else "account has no earlier history")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    now = datetime.now(timezone.utc)
    track, cand = read(os.path.join(BF, "tracker.csv")), read(os.path.join(BF, "candidates_private.csv"))
    bots, stale = [], 0
    for k, t in track.items():
        if t.get("status") != "banned" or not t.get("bb_link", "").startswith("https://www.reddit.com/r/BotBouncer/"):
            continue
        try:
            checked = datetime.strptime(t["bb_checked_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            stale += 1
            continue
        if now - checked > timedelta(days=7):
            stale += 1
            continue
        name = t["username"]
        c = cand.get(k, {})
        signals = [s for s, on in (("contact-handle or solicitation posts", c.get("sh") == "1"),
                                   ("normal history that turned to NSFW or solicitation posting", c.get("sb") == "1"),
                                   ("takeover break: new subreddits after a long ordinary history", c.get("takeover") == "1")) if on]
        posts, why = posts_from_packet(os.path.join(BF, c.get("packet", f"packets/{k}.md")), name)
        bots.append({"name": name, "profile": f"https://www.reddit.com/user/{name}", "listing": t["bb_link"],
                     "submitted": (t.get("submitted_utc") or "")[:10], "banned_since": t.get("banned_since", ""),
                     "checked": t["bb_checked_utc"][:10], "score": round(float(c["score"]), 2) if c.get("score") else None,
                     "signals": signals, "posts": posts, "posts_note": why})
    bots.sort(key=lambda b: b["banned_since"], reverse=True)
    out = {"updated": now.strftime("%Y-%m-%d %H:%M UTC"), "dispute": "carrier3rd@gmail.com", "bots": bots}
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "botfinds.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(f"botfinds.json: {len(bots)} listed; {stale} banned but not rechecked in 7 days (left off)")


if __name__ == "__main__":
    main()
