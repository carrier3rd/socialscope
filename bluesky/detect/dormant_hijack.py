"""dormant_hijack: long dormancy, then an identity change, then political posting (prediction 5).

Frozen rule (docs/bluesky-politics-predictions.md, 5): at least 180 days of silence, then a handle, PDS or key change
in the PLC log within 30 days before posting resumes, then at least 10 replies in target threads (from the resume,
inside [start_us, end_us)). Silence is measured on everything the tables hold for the account (history, threads,
Jetstream), so a short history pull can hide a gap: the results must report how many accounts had under 1,000 items.
"""
from common import DAY_US, connect, register_targets, table

SILENCE_DAYS, CHANGE_DAYS, MIN_REPLIES = 180, 30, 10


def run(data, cfg, start_us, end_us):
    con = connect(data)
    register_targets(con, cfg)
    posts, plc = table(data, "posts"), table(data, "plc_ops")
    rows = con.execute(f"""
        WITH p AS (SELECT did, epoch_us(created_at) AS t, reply_root FROM read_parquet('{posts}')
                   WHERE created_at IS NOT NULL),
        gaps AS (SELECT did, t, t - lag(t) OVER (PARTITION BY did ORDER BY t) AS gap FROM p),
        resumes AS (SELECT did, t AS resume FROM gaps WHERE gap >= {SILENCE_DAYS} * {DAY_US}),
        changes AS (
          SELECT did, epoch_us(created_at) AS t,
                 handle IS DISTINCT FROM lag(handle) OVER w AND lag(handle) OVER w IS NOT NULL AS h_chg,
                 pds IS DISTINCT FROM lag(pds) OVER w AND lag(pds) OVER w IS NOT NULL AS p_chg,
                 rotation_keys_changed AS k_chg
          FROM read_parquet('{plc}') WHERE NOT nullified
          WINDOW w AS (PARTITION BY did ORDER BY created_at)),
        hit AS (
          SELECT DISTINCT r.did, r.resume FROM resumes r JOIN changes c ON c.did = r.did
          WHERE (c.h_chg OR c.p_chg OR c.k_chg) AND c.t <= r.resume AND c.t >= r.resume - {CHANGE_DAYS} * {DAY_US})
        SELECT h.did, h.resume, count(*) AS replies
        FROM hit h JOIN p ON p.did = h.did
        JOIN targets t ON t.did = split_part(p.reply_root, '/', 3)
        WHERE p.t >= h.resume AND p.t >= ? AND p.t < ?
        GROUP BY h.did, h.resume HAVING count(*) >= {MIN_REPLIES}""", [start_us, end_us]).fetchall()
    candidates = con.execute(f"""
        SELECT count(DISTINCT did) FROM (
          SELECT did, epoch_us(created_at) - lag(epoch_us(created_at)) OVER (PARTITION BY did ORDER BY created_at) AS gap
          FROM read_parquet('{posts}') WHERE created_at IS NOT NULL) WHERE gap >= {SILENCE_DAYS} * {DAY_US}""").fetchone()[0]
    con.close()
    summary = {"accounts_with_180_day_silence": int(candidates), "matching_rule": len({d for d, *_ in rows})}
    private = [{"did": d, "resume_us": int(r), "target_replies": int(n)} for d, r, n in rows]
    return summary, private
