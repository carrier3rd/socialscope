#!/usr/bin/env python3
"""Phase 6 scorer for the predictions that need no model: 1, 2a-2c, 3a-3b, 5 and 7 (docs/bluesky-politics-predictions.md).

Written Nov 27 2026, before the window ended, from the frozen definitions only. Nothing here was tuned on window data.

    python bluesky/evaluate/score_window.py --dev      plumbing check on the development days: counts only, no shares,
                                                       no prediction is scored or printed
    python bluesky/evaluate/score_window.py --window   the scored run; refuses until 7 days after the window ends
                                                       (labels are taken "as they stand 7 days after", predictions file)
                                                       and until run_detectors.py --window has written its outputs

Frozen terms used (predictions file, "Data and terms"):
  in-thread replier  an account with at least one reply in the window, in a thread started by a target or directly to
                     a target; targets excluded. Side is the thread's (the root target's, else the parent target's), so
                     an account that replied on both sides counts on both.
  Tier A             an account-level Bluesky moderation label in keep_vals (spam, impersonation, !takedown), not
                     negated, not expired at the cutoff; or a DID in the hand-entered known-bad file (the Clemson, ISD,
                     AFP, CheckFirst reports). Labels on single posts do not count.
  Tier B             an account-level Skywatch label in its keep_vals or keep_prefixes, same conditions.
  labeled            Tier A or Tier B. Accounts that are no longer active and carry no label are counted separately.
  The labels table keeps the newest event per (labeler, subject, value); a label is used when that newest event was
  created before the cutoff. A label added after a removal that both fall after the cutoff is the one edge this misses.

Choices the predictions file leaves open, fixed here before any window data exists:
  2b "reply count"   replies whose thread root is the post (the whole thread), counted over the window
  2b "within 6 hours after a post"  the alarm hour [h, h + 1 h) overlaps [post time, post time + 6 h]
  1, thread size     the addendum under "Where I disagree": the same comparison restricted to replies in threads
                     rooted at a target post with 20 to 500 replies in the window (root replies only)
  7 "has a history"  the account has at least one post from a listRecords history pull (sources contains 'history')
  2c                 per target with alarms: distinct blockers in its alarm hours against distinct blockers of the same
                     target in its other hours of weeks 2-3; shares pooled over targets, weighted by blocker counts
  CIs                2,000 bootstrap resamples of accounts within each side (seed 17), percentile 95% intervals

Outputs (counts and shares only, no DID, handle or text): <data>/processed/evaluate/score_window_<tag>.json.
Predictions 4a, 4b, 6a, 6b and 9 need the transfer models, 8 needs fetch attempts and 10 the labeler value
counts: scored elsewhere.
"""
import argparse
import csv
import json
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "detect"))
import common as cm  # noqa: E402

B, SEED = 2000, 17
LABEL_LAG_DAYS = 7
SIDES = ("progressive", "government_right")


# ---------------------------------------------------------------------------------------------------------- inputs

def in_thread_repliers(con, data, start_us, end_us, size=None):
    """{side: set of DIDs}, the frozen in-thread replier definition. With size = (lo, hi): only replies in threads
    rooted at a target post that got lo to hi replies in the window (prediction 1's thread-size check)."""
    sized = "" if size is None else f"""AND r.did IS NOT NULL AND p.reply_root IN (
            SELECT reply_root FROM P WHERE t >= {int(start_us)} AND t < {int(end_us)} GROUP BY reply_root
            HAVING count(*) BETWEEN {int(size[0])} AND {int(size[1])})"""
    rows = con.execute(f"""
        WITH P AS (SELECT did, reply_root, reply_parent, epoch_us(created_at) AS t FROM read_parquet('{cm.table(data, 'posts')}')
                   WHERE reply_parent IS NOT NULL)
        SELECT DISTINCT p.did, coalesce(r.side, q.side) AS side
        FROM P p LEFT JOIN targets r ON r.did = split_part(p.reply_root, '/', 3)
                 LEFT JOIN targets q ON q.did = split_part(p.reply_parent, '/', 3)
        WHERE (r.did IS NOT NULL OR q.did IS NOT NULL) AND p.t >= ? AND p.t < ?
          AND p.did NOT IN (SELECT did FROM targets) {sized}""", [start_us, end_us]).fetchall()
    out = {s: set() for s in SIDES}
    for d, s in rows:
        out.setdefault(s, set()).add(d)
    return out


def known_bad(data, cfg):
    rel = (cfg.get("calibration") or {}).get("extra_known_bad")
    for base in (data, data.parent):
        p = base / rel if rel else None
        if p and p.is_file():
            with open(p, newline="", encoding="utf-8") as f:
                return {r["did"].strip() for r in csv.DictReader(f) if (r.get("did") or "").startswith("did:")}
    return set()


def tiers(con, data, cfg, cutoff_us):
    """(tier_a, tier_b) as sets of DIDs, account-level labels standing at cutoff_us."""
    labs = cfg["calibration"]["labelers"]

    def accounts(name):
        L = labs[name]
        vals = list(L.get("keep_vals") or [])
        pre = list(L.get("keep_prefixes") or [])
        cond = " OR ".join(["val IN (SELECT unnest(?::VARCHAR[]))"] + ["starts_with(val, ?)"] * len(pre))
        rows = con.execute(f"""
            SELECT DISTINCT uri_or_did FROM read_parquet('{cm.table(data, 'labels')}')
            WHERE src = ? AND starts_with(uri_or_did, 'did:') AND NOT coalesce(neg, false)
              AND epoch_us(cts) < ? AND (exp IS NULL OR epoch_us(exp) > ?) AND ({cond})""",
                           [L["did"], cutoff_us, cutoff_us, vals, *pre]).fetchall()
        return {r[0] for r in rows}

    return accounts("bluesky_mod") | known_bad(data, cfg), accounts("skywatch")


def inactive(con, data):
    rows = con.execute(f"SELECT did FROM read_parquet('{cm.table(data, 'accounts')}') WHERE status <> 'active'").fetchall()
    return {r[0] for r in rows}


def with_history(con, data):
    rows = con.execute(f"""SELECT DISTINCT did FROM read_parquet('{cm.table(data, 'posts')}')
                           WHERE list_contains(sources, 'history')""").fetchall()
    return {r[0] for r in rows}


# ------------------------------------------------------------------------------------------------------- statistics

def boot_share_ratio(groups, labeled, rnd):
    """Bootstrap the labeled share per side and the progressive / government_right ratio."""
    flags = {s: [1 if d in labeled else 0 for d in groups[s]] for s in SIDES}
    shares = {s: [] for s in SIDES}
    ratios = []
    for _ in range(B):
        one = {}
        for s in SIDES:
            f = flags[s]
            one[s] = sum(f[rnd.randrange(len(f))] for _ in f) / len(f) if f else float("nan")
            shares[s].append(one[s])
        g = one["government_right"]
        ratios.append(one["progressive"] / g if g > 0 else float("inf"))
    return shares, ratios


def pct(xs, q):
    xs = sorted(x for x in xs if x == x)
    if not xs:
        return None
    return xs[min(len(xs) - 1, int(q * len(xs)))]


def ci(xs):
    return [pct(xs, 0.025), pct(xs, 0.975)]


# --------------------------------------------------------------------------------------------------- predictions

def prediction_1(groups, labeled, rnd):
    n = {s: len(groups[s]) for s in SIDES}
    k = {s: len(groups[s] & labeled) for s in SIDES}
    share = {s: k[s] / n[s] if n[s] else None for s in SIDES}
    ratio = share["progressive"] / share["government_right"] if share["government_right"] else None
    bs, br = boot_share_ratio(groups, labeled, rnd)
    p, g = share["progressive"], share["government_right"]
    in_range = (p is not None and g is not None and ratio is not None
                and 0.003 <= p <= 0.020 and 0.001 <= g <= 0.015 and 1.2 <= ratio <= 4)
    return {"repliers": n, "labeled": k, "share": share, "share_ci95": {s: ci(bs[s]) for s in SIDES},
            "ratio": ratio, "ratio_ci95": ci(br),
            "direction_hit": (p is not None and g is not None and p > g), "range_hit": in_range}


def big_posts(con, data, start_us, end_us):
    """{target: [post times]} for each target's top 10% posts in the window by thread reply count."""
    rows = con.execute(f"""
        WITH P AS (SELECT uri, did, reply_root, reply_parent, epoch_us(created_at) AS t FROM read_parquet('{cm.table(data, 'posts')}')),
        tops AS (SELECT p.uri, p.did, p.t FROM P p JOIN targets tg ON tg.did = p.did
                 WHERE p.reply_parent IS NULL AND p.t >= ? AND p.t < ?),
        n AS (SELECT reply_root AS uri, count(*) AS replies FROM P WHERE reply_parent IS NOT NULL AND t >= ? AND t < ?
              GROUP BY reply_root)
        SELECT tops.did, tops.t, coalesce(n.replies, 0) FROM tops LEFT JOIN n USING (uri)""",
                       [start_us, end_us, start_us, end_us]).fetchall()
    per = {}
    for d, t, r in rows:
        per.setdefault(d, []).append((r, t))
    out = {}
    for d, xs in per.items():
        xs.sort(reverse=True)
        keep = max(1, -(-len(xs) // 10))           # top 10%, at least one post
        out[d] = [t for _, t in xs[:keep]]
    return out


def blockers_by_hour(con, data, lo, hi):
    rows = con.execute(f"""
        SELECT subject, time_us // {cm.HOUR_US} AS h, list(DISTINCT actor_did)
        FROM read_parquet('{cm.table(data, 'interactions')}') i JOIN targets t ON t.did = i.subject
        WHERE i.type = 'block' AND i.time_us >= ? AND i.time_us < ? GROUP BY ALL""", [lo, hi]).fetchall()
    return {(t, int(h)): set(ds) for t, h, ds in rows}


def prediction_2(con, data, alarms, labeled, start_us, end_us, alarm_lo, alarm_hi):
    n = len(alarms)
    posts = big_posts(con, data, start_us, end_us)
    six = 6 * cm.HOUR_US
    organic = 0
    for a in alarms:
        s = a["hour"] * cm.HOUR_US
        if any(p <= s + cm.HOUR_US and s <= p + six for p in posts.get(a["target"], [])):
            organic += 1
    by = blockers_by_hour(con, data, alarm_lo, alarm_hi)
    alarm_keys = {(a["target"], a["hour"]) for a in alarms}
    al_n = al_k = ot_n = ot_k = 0
    for t in {a["target"] for a in alarms}:
        for (tt, h), ds in by.items():
            if tt != t:
                continue
            k = len(ds & labeled)
            if (tt, h) in alarm_keys:
                al_n += len(ds); al_k += k
            else:
                ot_n += len(ds); ot_k += k
    sa = al_k / al_n if al_n else None
    so = ot_k / ot_n if ot_n else None
    diff = (sa - so) if sa is not None and so is not None else None
    return {"2a": {"alarms": n, "hit": 3 <= n <= 25},
            "2b": {"organic": organic, "share": organic / n if n else None, "hit": (organic / n >= 0.7) if n else None},
            "2c": {"labeled_share_alarm_hours": sa, "labeled_share_other_hours": so, "difference": diff,
                   "blockers_alarm_hours": al_n, "blockers_other_hours": ot_n,
                   "hit": (diff < 0.01) if diff is not None else None}}


def prediction_3(like_summary):
    g, big = like_summary.get("groups", 0), like_summary.get("largest_group", 0)
    return {"3a": {"groups": g, "largest_group": big, "hit": g >= 1}, "3b": {"largest_group": big, "hit": big < 2000}}


def prediction_5(dormant_private, repliers_all):
    matched = {r["did"] for r in dormant_private} & repliers_all
    share = len(matched) / len(repliers_all) if repliers_all else None
    return {"matched": len(matched), "in_thread_repliers": len(repliers_all), "share": share,
            "range_hit": 10 <= len(matched) <= 99, "under_1pct_hit": (share < 0.01) if share is not None else None}


# --------------------------------------------------------------------------------------------------------- driver

def detector_outputs(data, tag):
    d = data / "processed" / "detect"
    try:
        like = json.loads((d / f"like_farm_{tag}.json").read_text(encoding="utf-8"))
        surge = json.loads((d / "private" / f"block_surge_{tag}.json").read_text(encoding="utf-8"))
        dormant = json.loads((d / "private" / f"dormant_hijack_{tag}.json").read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        sys.exit(f"missing detector output ({e.filename}): run bluesky/detect/run_detectors.py --{tag} first")
    return like, surge, dormant


def score(data, cfg, start_us, end_us, cutoff_us, alarm_lo, alarm_hi, like, surge, dormant):
    con = cm.connect(data)
    cm.register_targets(con, cfg)
    groups = in_thread_repliers(con, data, start_us, end_us)
    a, b = tiers(con, data, cfg, cutoff_us)
    labeled = a | b
    everyone = set().union(*groups.values())
    gone = inactive(con, data)
    hist = with_history(con, data)
    rnd = random.Random(SEED)
    out = {
        "in_thread_repliers": {s: len(groups[s]) for s in SIDES}, "in_thread_any_side": len(everyone),
        "tier_a_in_thread": len(everyone & a), "tier_a_in_thread_with_history": len(everyone & a & hist),
        "tier_b_in_thread": len(everyone & b), "inactive_unlabeled_in_thread": len((everyone & gone) - labeled),
        "tier_a_testable": len(everyone & a & hist) >= 30,
        "p1": prediction_1(groups, labeled, rnd),
        "p1_threads_20_to_500": prediction_1(in_thread_repliers(con, data, start_us, end_us, (20, 500)), labeled, rnd),
        "p7": {"tier_a_with_history": len(everyone & a & hist),
               "range_hit": 10 <= len(everyone & a & hist) <= 150, "under_30": len(everyone & a & hist) < 30},
        "p2": prediction_2(con, data, surge, labeled, start_us, end_us, alarm_lo, alarm_hi),
        "p3": prediction_3(like), "p5": prediction_5(dormant, everyone)}
    con.close()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dev", action="store_true")
    g.add_argument("--window", action="store_true")
    ap.add_argument("--config", default=str(cm.bc.CONFIG))
    a = ap.parse_args()
    cfg = cm.bc.load_config(a.config)
    data = cm.bc.data_dir()
    w = cfg["window"]
    ws, we = cm.day_us(w["start"]), cm.day_us(w["end"])
    now = int(time.time() * 1e6)
    if a.window:
        cutoff = we + LABEL_LAG_DAYS * cm.DAY_US
        if now < cutoff:
            sys.exit("labels are scored as they stand 7 days after the window ends; too early to run --window")
        tag, start, end, alo, ahi = "window", ws, we, ws + 7 * cm.DAY_US, we
    else:
        cutoff, tag = now, "dev"
        start, end = cm.day_us("2026-11-19"), ws
        alo, ahi = start + (end - start) // 2 // cm.HOUR_US * cm.HOUR_US, end
    like, surge, dormant = detector_outputs(data, tag)
    t0 = time.time()
    out = score(data, cfg, start, end, cutoff, alo, ahi, like, surge, dormant)
    if a.dev:   # development days: keep the counts that test the plumbing, drop everything that reads like a result
        out = {k: out[k] for k in ("in_thread_repliers", "in_thread_any_side", "tier_a_in_thread",
                                   "tier_a_in_thread_with_history", "tier_b_in_thread", "inactive_unlabeled_in_thread")}
        out["note"] = "development days, plumbing only: no share, ratio or prediction is computed for output"
    out["run"], out["seconds"] = cm.bc.now_iso(), round(time.time() - t0, 1)
    cm.bc.atomic_json(data / "processed" / "evaluate" / f"score_window_{tag}.json", out)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
