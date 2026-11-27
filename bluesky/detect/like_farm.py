"""like_farm: groups of accounts whose likes of target posts overlap almost completely (prediction 3a).

Frozen definition (docs/bluesky-politics-predictions.md, 3a): a group of 50 or more accounts in which every pair has
Jaccard overlap of 0.8 or more over the target posts they liked, each account liked at least 5 target posts, and the
posts span at least 3 targets. Output aggregate only (spec section 8): group sizes, never the targets or the accounts.

Method: candidate pairs from MinHash with banding (a pair with Jaccard >= 0.8 shares a band with probability above
0.999 at 32 bands x 4 rows), every candidate pair checked exactly, then groups grown greedily inside each connected
component of the "Jaccard >= 0.8" graph so that every pair in a group meets the threshold.
"""
import random

from common import connect, register_targets, table

MIN_LIKES, MIN_JACCARD, MIN_GROUP, MIN_TARGETS = 5, 0.8, 50, 3
BANDS, ROWS = 32, 4


def liked_sets(con, data, start_us, end_us):
    rows = con.execute(f"""
        SELECT i.actor_did, list(DISTINCT i.subject) AS posts
        FROM read_parquet('{table(data, 'interactions')}') i
        JOIN targets t ON t.did = split_part(i.subject, '/', 3)
        WHERE i.type = 'like' AND i.time_us >= ? AND i.time_us < ?
        GROUP BY i.actor_did HAVING count(DISTINCT i.subject) >= {MIN_LIKES}""", [start_us, end_us]).fetchall()
    return {a: frozenset(p) for a, p in rows}


def jaccard(a, b):
    return len(a & b) / len(a | b)


def find_groups(sets, min_group=MIN_GROUP, min_jaccard=MIN_JACCARD, seed=0):
    """Groups of accounts in which every pair has Jaccard >= min_jaccard. Returns a list of sets of accounts."""
    rnd = random.Random(seed)
    salts = [rnd.getrandbits(64) for _ in range(BANDS * ROWS)]
    buckets = {}
    for acct, s in sets.items():
        sig = [min(hash((salt, p)) for p in s) for salt in salts]
        for b in range(BANDS):
            buckets.setdefault((b, tuple(sig[b * ROWS:(b + 1) * ROWS])), []).append(acct)
    nbr = {}
    seen = set()
    for members in buckets.values():
        if len(members) < 2:
            continue
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a, b = members[i], members[j]
                key = (a, b) if a < b else (b, a)
                if key in seen:
                    continue
                seen.add(key)
                if jaccard(sets[a], sets[b]) >= min_jaccard:
                    nbr.setdefault(a, set()).add(b)
                    nbr.setdefault(b, set()).add(a)
    groups, used = [], set()
    for start in sorted(nbr, key=lambda a: -len(nbr[a])):        # best-connected accounts seed the groups
        if start in used or len(nbr[start]) + 1 < min_group:
            continue
        group = {start}
        for cand in sorted(nbr[start] - used, key=lambda a: -len(nbr[a])):
            if all(cand in nbr[g] for g in group):                # every pair must meet the threshold
                group.add(cand)
        if len(group) >= min_group:
            groups.append(group)
            used |= group
    return groups


def run(data, cfg, start_us, end_us):
    con = connect(data)
    register_targets(con, cfg)
    sets = liked_sets(con, data, start_us, end_us)
    con.close()
    groups = []
    for g in find_groups(sets):
        posts = frozenset().union(*(sets[a] for a in g))
        n_targets = len({p.split("/")[2] for p in posts})
        if n_targets >= MIN_TARGETS:
            groups.append((g, n_targets, len(posts)))
    summary = {"accounts_with_5_target_likes": len(sets), "groups": len(groups),
               "group_sizes": sorted((len(g) for g, _, _ in groups), reverse=True),
               "largest_group": max((len(g) for g, _, _ in groups), default=0)}
    private = [{"accounts": sorted(g), "targets": n, "posts": p} for g, n, p in groups]
    return summary, private
