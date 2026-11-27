"""follow_burst: bulk-follow bursts and account-creation streaks (spec section 8, Conspirador Norteno's method).

  bulk bursts      accounts that made at least BULK follows within one clock hour
  creation streaks clock hours in which at least STREAK accounts that follow the same target were created (their
                   first PLC operation); a streak of new accounts all following one target is the classic farm shape
Control (spec): bursts explained by starter-pack joins should be subtracted, but the recorder does not keep
app.bsky.graph.starterpack events, so this is NOT done yet and every result must say so (owner decision: add the
collection to the recorder, or drop the control).
"""
from common import connect, register_targets, table

BULK, STREAK = 50, 10


def run(data, cfg, start_us, end_us):
    con = connect(data)
    register_targets(con, cfg)
    inter, plc = table(data, "interactions"), table(data, "plc_ops")
    bulk = con.execute(f"""
        SELECT actor_did, max(n) AS peak FROM (
          SELECT actor_did, time_us // 3600000000 AS h, count(*) AS n FROM read_parquet('{inter}')
          WHERE type = 'follow' AND time_us >= ? AND time_us < ? GROUP BY actor_did, h)
        WHERE n >= {BULK} GROUP BY actor_did""", [start_us, end_us]).fetchall()
    streaks = con.execute(f"""
        WITH created AS (
          SELECT did, min(epoch_us(created_at)) AS c FROM read_parquet('{plc}') WHERE NOT nullified GROUP BY did),
        followers AS (
          SELECT DISTINCT i.subject AS target, i.actor_did AS did FROM read_parquet('{inter}') i
          JOIN targets t ON t.did = i.subject WHERE i.type = 'follow' AND i.time_us >= ? AND i.time_us < ?)
        SELECT f.target, c.c // 3600000000 AS h, count(*) AS n
        FROM followers f JOIN created c USING (did)
        GROUP BY f.target, h HAVING count(*) >= {STREAK}""", [start_us, end_us]).fetchall()
    con.close()
    summary = {"bulk_follow_accounts": len(bulk), "bulk_threshold_per_hour": BULK,
               "creation_streak_hours": len(streaks), "creation_streak_accounts": int(sum(n for *_, n in streaks)),
               "starter_pack_control": "not applied (starter-pack events are not recorded)"}
    private = {"bulk": [{"did": d, "peak_follows_per_hour": int(p)} for d, p in bulk],
               "streaks": [{"target": t, "hour": int(h), "accounts": int(n)} for t, h, n in streaks]}
    return summary, private
