"""Matched anchors for control accounts (scripts/repull_run/anchors.py, Nov 5 2026).

Positives are anchored at their Bot Bouncer listing date. The old run anchored controls at their own last item,
which always lands on an active day and (for October-active controls) months after most listings, so the 30-day
pre-window compared "a bot's last month before listing" with "a regular's most active recent month". Here each
control draws an anchor from the positives' anchor distribution on its own side of the split (test controls from
test positives, train controls from train positives), restricted to anchors at least one day after the account's
first item ever, with a fixed seed. pull.py pulls the control's history ending at that anchor; feats.py cuts there.
"""
import random


def assign_control_anchors(G, first, last, seed=20261105, min_lead_days=1):
    """G: {username: row with 'group' and 'anchor_utc'}; first/last: {username: ts or None}.
    Returns {username: (anchor_ts, source)} for every control (train_ctl, test_ctl)."""
    pos = {"test_ctl": sorted(float(r["anchor_utc"]) for r in G.values() if r["group"] == "test_pos" and r["anchor_utc"]),
           "train_ctl": sorted(float(r["anchor_utc"]) for r in G.values() if r["group"] == "train_pos" and r["anchor_utc"])}
    allpos = sorted(pos["test_ctl"] + pos["train_ctl"])
    rng = random.Random(seed)
    out = {}
    for u in sorted(G):   # sorted so the draw is reproducible
        g = G[u]["group"]
        if g not in pos:
            continue
        pool = pos[g] or allpos
        f = first.get(u)
        cands = [t for t in pool if f is None or t >= f + min_lead_days * 86400]
        if cands:
            out[u] = (rng.choice(cands), "matched")
        elif last.get(u) is not None:
            out[u] = (float(last[u]), "fallback_last")   # account younger than every positive anchor
    return out
