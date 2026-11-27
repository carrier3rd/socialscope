#!/usr/bin/env python3
"""Phase 3 features: per-account Bluesky features from the Phase 2 tables, cut at each account's anchor.

    python bluesky/features/bsky_only.py            the development feature file (anchors capped at the window start)

Written Nov 27 2026 (owner: "and on the bluesky stuff", after Phase 2). Prints counts only.

Every feature uses only activity AT OR BEFORE the account's anchor (RECON 2.3 check 1, "cut at the anchor"): posts
by created_at, interactions by created_at (the record key time when createdAt is missing), PLC operations by
createdAt. For the development file the anchor is the account's history anchor (the time its listRecords pull
ended), capped at the start of the test window, so nothing from the window is read (predictions file: "pilot days
are development data"). Scoring runs later pass labelled anchors (first label cts) and matched control anchors.

Features (one row per account):
  shared, new columns (RECON 3.4): n_items, n_top, n_replies, reply_share, posts_per_day, interval_mean_h,
    interval_var_h2, longest_gap_days, account_age_days (from the first PLC operation)
  reply latency (prediction 4b): median_reply_minutes, share_replies_under_10min, n_replies_timed
    (replies whose parent is in the posts table; latency = reply created_at - parent created_at)
  reply-only (prediction 4a): reply_only (at least 90% of the items before the anchor are replies)
  PLC: handle_changes, days_since_handle_change, pds_migrations, key_rotations, key_rotation_before_burst
    (a rotation in the 3 days before a posting burst day: at least 10 posts and 5 times the median active day)
  dormant (prediction 5 parts; the detector adds the 10-replies-in-target-threads condition): longest_gap_days
    above, dormant_180 (a gap of at least 180 days), change_before_resume (a handle, PDS or key change in the 30 days
    before posting resumed after such a gap)
  PDS: pds_host, self_hosted_pds (not bsky.social or *.bsky.network), pds_accounts (accounts in the tables on the
    same host; the cluster-level share is a detector)
  interactions given: likes_given, follows_given, max_follows_per_hour, share_follows_in_bursts (follows made in
    clock hours with 10 or more follows), likes_with_zero_posts
  interactions received: blocks_received
  client-time skew: median_skew_s, share_skew_over_1h (|indexed_at - created_at|, Jetstream posts only)
  links: reddit_x_link_share (posts linking reddit.com, redd.it, x.com, twitter.com or t.co)

Not built yet, each needs an owner decision (see docs and the Phase 3 note):
  low-credibility domain share (a cited domain list has to be chosen, RECON 3.4), declared-langs mismatch (needs a
  language detector package), follower/following ratio and replies to higher-follower accounts (profile counts
  are fetched once, after the anchor, so they would leak: RECON 2.3 check 4).
"""
import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "collect"))
import bsky_common as bc  # noqa: E402

LINK_DOMAINS = ("reddit.com", "redd.it", "x.com", "twitter.com", "t.co")
BURST_MIN_POSTS, BURST_FACTOR, ROTATION_DAYS = 10, 5, 3
DORMANT_DAYS, CHANGE_DAYS = 180, 30
FOLLOW_BURST = 10
DAY_US = 86_400_000_000


def history_anchors(data):
    """{did: anchor_us} from the history pulls' .done.json files."""
    out = {}
    root = data / "raw" / "histories"
    for p in root.glob("*/*.done.json") if root.is_dir() else []:
        j = bc.load_json(p, {})
        if isinstance(j.get("anchor_us"), int):
            did = p.name[:-len(".done.json")].replace("_", ":", 2)    # did_plc_x -> did:plc:x
            out[did] = j["anchor_us"]
    return out


def window_start_us(cfg):
    w = cfg.get("window") or {}
    d = w.get("start")
    if d is None:
        return None
    d = d if isinstance(d, dt.date) else dt.date.fromisoformat(str(d))
    return int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp() * 1_000_000)


SQL = r"""
CREATE TEMP TABLE P AS                       -- each account's posts at or before its anchor
SELECT p.did, p.uri, p.reply_parent, p.facet_links, p.sources,
       epoch_us(p.created_at) AS t, epoch_us(p.indexed_at) AS ti, a.anchor_us
FROM read_parquet('{posts}') p JOIN anchors a USING (did)
WHERE p.created_at IS NOT NULL AND epoch_us(p.created_at) <= a.anchor_us;

CREATE TEMP TABLE I AS                       -- interactions each account GAVE at or before its anchor
SELECT i.actor_did AS did, i.type, coalesce(epoch_us(i.created_at), epoch_us(i.rkey_time)) AS t
FROM read_parquet('{inter}') i JOIN anchors a ON a.did = i.actor_did
WHERE coalesce(epoch_us(i.created_at), epoch_us(i.rkey_time)) <= a.anchor_us;

CREATE TEMP TABLE base AS
WITH gaps AS (
  SELECT did, t - lag(t) OVER (PARTITION BY did ORDER BY t) AS gap FROM P
)
SELECT a.did,
  count(p.uri) AS n_items,
  count(p.uri) FILTER (WHERE p.reply_parent IS NULL) AS n_top,
  count(p.uri) FILTER (WHERE p.reply_parent IS NOT NULL) AS n_replies,
  min(p.t) AS first_t, max(p.t) AS last_t
FROM anchors a LEFT JOIN P p USING (did) GROUP BY a.did;

CREATE TEMP TABLE intervals AS
SELECT did, avg(gap) / 3.6e9 AS interval_mean_h, var_samp(gap / 3.6e9) AS interval_var_h2,
       max(gap) / 8.64e10 AS longest_gap_days
FROM (SELECT did, t - lag(t) OVER (PARTITION BY did ORDER BY t) AS gap FROM P) WHERE gap IS NOT NULL GROUP BY did;

CREATE TEMP TABLE latency AS                 -- reply time minus parent time, parent from any source
SELECT r.did, median((r.t - epoch_us(q.created_at)) / 6e7) AS median_reply_minutes,
       avg(CASE WHEN r.t - epoch_us(q.created_at) < 6e8 THEN 1.0 ELSE 0.0 END) AS share_replies_under_10min,
       count(*) AS n_replies_timed
FROM P r JOIN read_parquet('{posts}') q ON q.uri = r.reply_parent
WHERE r.reply_parent IS NOT NULL AND q.created_at IS NOT NULL AND r.t >= epoch_us(q.created_at)
GROUP BY r.did;

CREATE TEMP TABLE skew AS                    -- client clock against the relay's, Jetstream posts only
SELECT did, median(abs(ti - t) / 1e6) AS median_skew_s,
       avg(CASE WHEN abs(ti - t) > 3.6e9 THEN 1.0 ELSE 0.0 END) AS share_skew_over_1h
FROM P WHERE ti IS NOT NULL AND list_contains(sources, 'jetstream') GROUP BY did;

CREATE TEMP TABLE links AS
SELECT did, avg(CASE WHEN len(list_filter(facet_links, lambda u: regexp_matches(lower(u),
         '^(https?://)?([a-z0-9-]+\.)*(reddit\.com|redd\.it|x\.com|twitter\.com|t\.co)(/|$)'))) > 0
         THEN 1.0 ELSE 0.0 END) AS reddit_x_link_share
FROM P GROUP BY did;

CREATE TEMP TABLE given AS
SELECT did, count(*) FILTER (WHERE type = 'like') AS likes_given,
       count(*) FILTER (WHERE type = 'follow') AS follows_given FROM I GROUP BY did;

CREATE TEMP TABLE follow_hours AS
SELECT did, max(n) AS max_follows_per_hour,
       sum(n) FILTER (WHERE n >= {burst}) * 1.0 / sum(n) AS share_follows_in_bursts
FROM (SELECT did, t // 3600000000 AS h, count(*) AS n FROM I WHERE type = 'follow' GROUP BY did, h) GROUP BY did;

CREATE TEMP TABLE blocks AS                  -- blocks RECEIVED before the anchor
SELECT a.did, count(*) AS blocks_received
FROM read_parquet('{inter}') i JOIN anchors a ON a.did = i.subject
WHERE i.type = 'block' AND coalesce(epoch_us(i.created_at), epoch_us(i.rkey_time)) <= a.anchor_us
GROUP BY a.did;

CREATE TEMP TABLE daily AS                   -- posts per UTC day, for bursts
SELECT did, t // 86400000000 AS d, count(*) AS n FROM P GROUP BY did, d;

CREATE TEMP TABLE resumes AS                 -- the first post after a silence of DORMANT_DAYS or more
SELECT did, t AS resume_t FROM (SELECT did, t, t - lag(t) OVER (PARTITION BY did ORDER BY t) AS gap FROM P)
WHERE gap >= {dormant} * 86400000000;
"""


def build(data, cfg, anchors, out_name="bsky_features_dev", log=print):
    import duckdb
    import pyarrow as pa
    import pyarrow.parquet as pq
    tables = data / "processed" / "tables"
    feats = data / "processed" / "features"
    feats.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
    con.execute(f"SET memory_limit = '{os.environ.get('BSKY_FEATURES_MEMORY', '2GB')}'")
    (data / "processed" / "duckdb_tmp").mkdir(parents=True, exist_ok=True)
    con.execute(f"SET temp_directory = '{(data / 'processed' / 'duckdb_tmp').as_posix()}'")
    con.register("anchors_arrow", pa.Table.from_pylist([{"did": d, "anchor_us": a} for d, a in anchors.items()],
                                                       schema=pa.schema([("did", pa.string()), ("anchor_us", pa.int64())])))
    con.execute("CREATE TEMP TABLE anchors AS SELECT * FROM anchors_arrow")
    sql = SQL.format(posts=(tables / "posts.parquet").as_posix(), inter=(tables / "interactions.parquet").as_posix(),
                     burst=FOLLOW_BURST, dormant=DORMANT_DAYS)
    for stmt in [s for s in sql.split(";") if s.strip()]:
        con.execute(stmt)

    rows = {r[0]: dict(zip([c[0] for c in con.description], r)) for r in con.execute("""
        SELECT b.*, iv.interval_mean_h, iv.interval_var_h2, iv.longest_gap_days,
               l.median_reply_minutes, l.share_replies_under_10min, coalesce(l.n_replies_timed, 0) AS n_replies_timed,
               s.median_skew_s, s.share_skew_over_1h, k.reddit_x_link_share,
               coalesce(g.likes_given, 0) AS likes_given, coalesce(g.follows_given, 0) AS follows_given,
               coalesce(f.max_follows_per_hour, 0) AS max_follows_per_hour, f.share_follows_in_bursts,
               coalesce(bl.blocks_received, 0) AS blocks_received
        FROM base b LEFT JOIN intervals iv USING (did) LEFT JOIN latency l USING (did) LEFT JOIN skew s USING (did)
        LEFT JOIN links k USING (did) LEFT JOIN given g USING (did) LEFT JOIN follow_hours f USING (did)
        LEFT JOIN blocks bl USING (did)""").fetchall()}
    daily = {}
    for did, d, n in con.execute("SELECT did, d, n FROM daily").fetchall():
        daily.setdefault(did, []).append((d, n))
    resumes = {}
    for did, t in con.execute("SELECT did, resume_t FROM resumes").fetchall():
        resumes.setdefault(did, []).append(t)
    plc = {}
    for did, op, handle, pds, rot, t in con.execute(f"""
            SELECT did, op_type, handle, pds, rotation_keys_changed, epoch_us(created_at)
            FROM read_parquet('{(tables / "plc_ops.parquet").as_posix()}') WHERE NOT nullified AND did IN (SELECT did FROM anchors)
            ORDER BY did, created_at""").fetchall():
        plc.setdefault(did, []).append((op, handle, pds, bool(rot), t))
    acct = {did: pds for did, pds in con.execute(
        f"SELECT did, pds_host FROM read_parquet('{(tables / 'accounts.parquet').as_posix()}')").fetchall()}
    pds_count = {}
    for h in acct.values():
        if h:
            pds_count[h] = pds_count.get(h, 0) + 1
    con.close()

    out = []
    for did, anchor in anchors.items():
        r = rows.get(did, {"did": did})
        n = r.get("n_items") or 0
        f = {"did": did, "anchor_us": anchor}
        f.update({k: r.get(k) for k in ("n_items", "n_top", "n_replies", "interval_mean_h", "interval_var_h2",
                                         "longest_gap_days", "median_reply_minutes", "share_replies_under_10min",
                                         "n_replies_timed", "median_skew_s", "share_skew_over_1h", "reddit_x_link_share",
                                         "likes_given", "follows_given", "max_follows_per_hour",
                                         "share_follows_in_bursts", "blocks_received")})
        f["reply_share"] = (r["n_replies"] / n) if n else None
        f["reply_only"] = bool(n) and r["n_replies"] / n >= 0.9
        span_days = ((r["last_t"] - r["first_t"]) / DAY_US) if n else None
        f["posts_per_day"] = n / max(span_days, 1.0) if n else 0.0
        f["likes_with_zero_posts"] = (f["likes_given"] or 0) > 0 and n == 0
        ops = [o for o in plc.get(did, []) if o[4] is not None and o[4] <= anchor]
        f["account_age_days"] = (anchor - ops[0][4]) / DAY_US if ops else None
        changes, prev_h, prev_p, last_h = [], None, None, None
        hc = pm = kr = 0
        for i, (op, h, p, rot, t) in enumerate(ops):
            if i and h and prev_h and h != prev_h:
                hc += 1; last_h = t; changes.append(t)
            if i and p and prev_p and p != prev_p:
                pm += 1; changes.append(t)
            if rot:
                kr += 1; changes.append(t)
            prev_h, prev_p = h or prev_h, p or prev_p
        f.update(handle_changes=hc, pds_migrations=pm, key_rotations=kr,
                 days_since_handle_change=(anchor - last_h) / DAY_US if last_h else None)
        days = daily.get(did, [])
        burst_days = []
        if days:
            counts = sorted(c for _, c in days)
            med = counts[len(counts) // 2]
            burst_days = [d for d, c in days if c >= max(BURST_MIN_POSTS, BURST_FACTOR * med)]
        rot_times = [o[4] for o in ops if o[3]]
        f["key_rotation_before_burst"] = any(0 <= d * DAY_US - t <= ROTATION_DAYS * DAY_US
                                             for d in burst_days for t in rot_times)
        res = resumes.get(did, [])
        f["dormant_180"] = bool(res)
        f["change_before_resume"] = any(0 <= rt - t <= CHANGE_DAYS * DAY_US for rt in res for t in changes)
        host = acct.get(did)
        f["pds_host"] = host
        f["self_hosted_pds"] = None if not host else not (host == "bsky.social" or host.endswith(".bsky.network"))
        f["pds_accounts"] = pds_count.get(host) if host else None
        out.append(f)

    table = pa.Table.from_pylist(out)
    pq.write_table(table, feats / f"{out_name}.parquet", compression="zstd")
    import csv
    with open(feats / f"{out_name}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()) if out else ["did"])
        w.writeheader()
        w.writerows(out)
    summary = {"accounts": len(out), "with_posts": sum(1 for f in out if f["n_items"]),
               "with_timed_replies": sum(1 for f in out if f["n_replies_timed"]),
               "reply_only": sum(1 for f in out if f["reply_only"]),
               "dormant_180": sum(1 for f in out if f["dormant_180"]),
               "change_before_resume": sum(1 for f in out if f["change_before_resume"]),
               "key_rotation_before_burst": sum(1 for f in out if f["key_rotation_before_burst"]),
               "self_hosted_pds": sum(1 for f in out if f["self_hosted_pds"]),
               "likes_with_zero_posts": sum(1 for f in out if f["likes_with_zero_posts"]),
               "columns": len(out[0]) if out else 0}
    bc.atomic_json(feats / f"{out_name}_summary.json", {"run": bc.now_iso(), **summary})
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(bc.CONFIG))
    a = ap.parse_args()
    cfg = bc.load_config(a.config)
    data = bc.data_dir()
    ws = window_start_us(cfg)
    anchors = {d: (min(t, ws - 1) if ws else t) for d, t in history_anchors(data).items()}
    print("features", json.dumps(build(data, cfg, anchors)))


if __name__ == "__main__":
    main()
