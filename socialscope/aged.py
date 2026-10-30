"""Candidate rule for aged bot accounts (frozen Oct 30, 2026, before its fresh test).

Round 4 found Bot Bouncer bots in political subs with years of history that age rules can't reach. aged_drift looks
for a recent move into unfamiliar subs: an account at least a year old with 100+ items whose last 30 days of activity
(5+ items) land mostly in subreddits it never used before, scattered across many of them.

Development data: 2,292 earlier-round histories labeled by Bot Bouncer (round 4 accounts excluded). Among aged
accounts with recent activity it flagged 7 of 23 bots (30%) and 42 of 745 others (5.6%). That is weak and the dev
"others" are not random, so it is a SUPPORT candidate with no weight until a fresh round scores it."""
from collections import Counter

DAY = 86400


def aged_drift(items, recent_days=30, min_items=100, min_span_days=365, min_recent=5, new_share=0.4, spread=0.5):
    """items: list of (created_utc, subreddit, ...) sorted by time. Returns (fired, details)."""
    if len(items) < min_items or items[-1][0] - items[0][0] < min_span_days * DAY:
        return False, {}
    cut = items[-1][0] - recent_days * DAY
    rec = [x for x in items if x[0] >= cut]
    pri = [x for x in items if x[0] < cut]
    if len(rec) < min_recent or len(pri) < 20:
        return False, {}
    seen = set(x[1] for x in pri)
    ns = sum(1 for x in rec if x[1] not in seen) / len(rec)
    sp = len(set(x[1] for x in rec)) / len(rec)
    return (ns >= new_share and sp >= spread), {"recent_items": len(rec), "new_sub_share": round(ns, 2), "recent_spread": round(sp, 2)}
