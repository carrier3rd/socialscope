"""Bluesky post records -> the Reddit item shape the frozen v7.1 code reads (RECON 2.2 and 3.4, reading (a)).

Written Nov 19 2026 (laptop session) for the Phase 1 plumbing check. The frozen code (socialscope/history.py,
prewindow.py, hijack.py, lookup_core.py) is not changed; this module only feeds it.

Mapping, one record from com.atproto.repo.listRecords (collection app.bsky.feed.post):
  top-level post -> a Reddit submission: id = record key, title = text, selftext = "", url = first link
  reply          -> a Reddit comment:    id = record key, body = text, link_id = "t3_" + root key,
                                         parent_id = "t3_" + root key if the parent is the root, else "t1_" + parent key
  created_utc    -> the record's createdAt (client-set, so it can be wrong; the check counts implausible ones)
Not produced, because Bluesky has no equivalent: subreddit, score, author_fullname, distinguished.

The frozen code reads a missing subreddit as "" and a missing score as 0, which would give every account one
subreddit and zero karma. So every model input that depends on either is blanked (NaN) after the features are
computed: see MASKED. The model accepts missing values. The list was found by perturbation, not by hand: rerun the
features with random subreddits and random scores and keep every column that moves (transfer_check.py
--perturb). It must be re-derived if the frozen feature code ever changes.
"""
import datetime as dt
import math

# Nov 19 2026: perturbation of 40 pilot histories (transfer_check.py --perturb 40) moved these model inputs.
MOVED_BY_SUBREDDIT = ("bot_score", "farm_share", "political_early", "political_late", "pw_distinct_subs_per_item",
                      "pw_new_subreddit_share", "sb", "sub_spread", "subs", "top_sub_share")
MOVED_BY_SCORE = ("pw_score_median_change",)
# A perturbation shows dependence, not independence: rules that need rare conditions don't fire in a sample. These
# two depend on subreddits in the code (RECON 3.4) but did not move in the 40 accounts: sh (solicitation only in
# NSFW subs, hijack.solicit_handle) and primary (its "tourist" part needs 10+ subreddits). Masked to match RECON's
# reading (a); primary's other parts (young_account, posts_only) are lost with it, which the results must say.
FROM_CODE = ("sh", "primary")
MASKED_BY_SUBREDDIT = MOVED_BY_SUBREDDIT + FROM_CODE
MASKED_BY_SCORE = MOVED_BY_SCORE
MASKED = MASKED_BY_SUBREDDIT + MASKED_BY_SCORE

BSKY_LAUNCH = dt.datetime(2023, 2, 1, tzinfo=dt.timezone.utc).timestamp()   # earliest plausible createdAt


def _rkey(uri):
    return uri.rsplit("/", 1)[1] if uri else ""


def _ts(iso):
    try:
        t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return t.timestamp()


def _first_link(v):
    emb = v.get("embed") or {}
    ext = emb.get("external") or (emb.get("media") or {}).get("external") or {}
    if ext.get("uri"):
        return ext["uri"]
    for f in v.get("facets") or []:
        for feat in f.get("features") or []:
            if feat.get("uri"):
                return feat["uri"]
    return None


def to_item(rec, author):
    """One listRecords record -> one Reddit-shaped item, or None if it has no usable time."""
    v = rec.get("value") or {}
    t = _ts(v.get("createdAt"))
    if t is None:
        return None
    key = _rkey(rec.get("uri"))
    item = {"id": key, "created_utc": t, "author": author}
    rep = v.get("reply")
    if rep:
        root = _rkey((rep.get("root") or {}).get("uri"))
        parent = _rkey((rep.get("parent") or {}).get("uri"))
        item["body"] = v.get("text") or ""
        item["link_id"] = "t3_" + root
        item["parent_id"] = ("t3_" + root) if parent == root else ("t1_" + parent)
    else:
        item["title"] = v.get("text") or ""
        item["selftext"] = ""
        url = _first_link(v)
        if url:
            item["url"] = url
    return item


def to_items(records, author):
    out, bad = [], 0
    for r in records:
        it = to_item(r, author)
        if it is None:
            bad += 1
        else:
            out.append(it)
    return out, bad


def mask(row, masked=None):
    """Blank the inputs that have no Bluesky meaning (in place; returns row)."""
    for c in (MASKED if masked is None else masked):
        if c in row:
            row[c] = math.nan
    return row
