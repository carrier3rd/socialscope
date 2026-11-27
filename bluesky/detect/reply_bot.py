"""reply_bot: fast, reply-only accounts in target threads (spec section 8, Willison checker logic).

An account is flagged when, inside [start_us, end_us), it has at least MIN_REPLIES replies in target threads and:
  - FAST: at least half of its direct replies to target posts came within FAST_S seconds of the post
  - REPLY_ONLY: no top-level posts in the tables before end_us (no original posts)
  - NO_MEDIA: none of its replies carry an image or video embed
  - BAIT (counted, not required): share of replies that are short questions (under 80 characters, ending in "?")
"Replies mostly to bigger accounts" needs follower counts at the time of each reply, which the tables do not have
(profiles are fetched once, later): left out until the owner decides (RECON 2.3 check 4).
These are leads (Tier C), never labels or names (predictions file, Tier rules).
"""
from common import connect, register_targets, table

MIN_REPLIES, FAST_S = 10, 60


def run(data, cfg, start_us, end_us):
    con = connect(data)
    register_targets(con, cfg)
    posts = table(data, "posts")
    rows = con.execute(f"""
        WITH P AS (SELECT * FROM read_parquet('{posts}')),
        r AS (SELECT p.did, p.uri, p.text, p.embed_type, p.reply_parent, epoch_us(p.created_at) AS t
              FROM P p JOIN targets tg ON tg.did = split_part(p.reply_root, '/', 3)
              WHERE p.reply_parent IS NOT NULL AND p.did <> tg.did
                AND epoch_us(p.created_at) >= ? AND epoch_us(p.created_at) < ?),
        direct AS (SELECT r.did, (r.t - epoch_us(q.created_at)) / 1e6 AS lat_s
                   FROM r JOIN P q ON q.uri = r.reply_parent JOIN targets tg ON tg.did = q.did),
        tops AS (SELECT DISTINCT did FROM P WHERE reply_parent IS NULL AND epoch_us(created_at) < ?),
        per_reply AS (
          SELECT did, count(DISTINCT uri) AS replies,
                 coalesce(bool_or(embed_type IN ('app.bsky.embed.images', 'app.bsky.embed.video')), false) AS media,
                 avg(CASE WHEN length(text) < 80 AND trim(text) LIKE '%?' THEN 1.0 ELSE 0.0 END) AS bait_share
          FROM r GROUP BY did),
        per_direct AS (
          SELECT did, avg(CASE WHEN lat_s BETWEEN 0 AND {FAST_S} THEN 1.0 ELSE 0.0 END) AS fast_share
          FROM direct GROUP BY did)
        SELECT a.did, a.replies, coalesce(d.fast_share, 0.0) AS fast_share, a.media, a.bait_share,
               a.did IN (SELECT did FROM tops) AS has_top
        FROM per_reply a LEFT JOIN per_direct d USING (did)
        WHERE a.replies >= {MIN_REPLIES}""", [start_us, end_us, end_us]).fetchall()
    con.close()
    flagged = [(d, n, f, b) for d, n, f, m, b, top in rows if f >= 0.5 and not m and not top]
    summary = {"accounts_with_10_target_replies": len(rows), "flagged": len(flagged),
               "flagged_bait_share_mean": round(sum(b for *_, b in flagged) / len(flagged), 4) if flagged else None}
    private = [{"did": d, "replies": int(n), "fast_share": round(f, 4), "bait_share": round(b, 4)}
               for d, n, f, b in flagged]
    return summary, private
