"""block_surge: hours in which a target gets unusually many distinct blockers (predictions file, block_surge terms).

Frozen rule (docs/bluesky-politics-predictions.md, "block_surge", from docs/brigade-alarm-v2-predictions.md): distinct
blockers per target per UTC hour; expected count = total blocks across all targets that hour x the target's share
profile by hour-of-day and weekday/weekend, both fitted on the baseline days; an alarm is a count above the negative
binomial 99.9th percentile (extra variance alpha fitted on baseline residuals, var = mu + alpha mu^2) with at least
5 distinct blockers. The baseline is [base_start, base_end): week 1 of the window for the test; alarms are counted
only in [start_us, end_us) (weeks 2 and 3).
"""
import math

from common import HOUR_US, connect, register_targets, table

Q, MIN_ACCOUNTS = 0.999, 5


def cell(h):
    """epoch hour -> 0..47: hour of day, +24 on Saturday and Sunday (epoch day 0 was a Thursday)."""
    day = (h // 24 + 3) % 7      # Monday = 0
    return h % 24 + (24 if day >= 5 else 0)


def nb_quantile(q, mu, alpha):
    """Smallest k with P(X <= k) >= q for a negative binomial with mean mu and var mu + alpha mu^2 (Poisson at 0)."""
    if mu <= 0:
        return 0
    if alpha <= 1e-9:
        p0, k, cum = math.exp(-mu), 0, math.exp(-mu)
        pk = p0
        while cum < q:
            k += 1
            pk *= mu / k
            cum += pk
        return k
    n = 1.0 / alpha
    p = n / (n + mu)
    pk = p ** n
    cum, k = pk, 0
    while cum < q:
        k += 1
        pk *= (k - 1 + n) / k * (1 - p)
        cum += pk
    return k


def counts(con, data, lo, hi):
    """{(target, epoch hour): distinct blockers} and {epoch hour: total blocks of all targets}."""
    rows = con.execute(f"""
        SELECT i.subject, i.time_us // {HOUR_US} AS h, count(DISTINCT i.actor_did)
        FROM read_parquet('{table(data, 'interactions')}') i JOIN targets t ON t.did = i.subject
        WHERE i.type = 'block' AND i.time_us >= ? AND i.time_us < ? GROUP BY ALL""", [lo, hi]).fetchall()
    per = {(t, int(h)): int(n) for t, h, n in rows}
    tot = {}
    for (_, h), n in per.items():
        tot[h] = tot.get(h, 0) + n
    return per, tot


def fit(per, tot, targets, hours):
    """share[target][cell] and alpha from the baseline hours."""
    share, num, den = {}, {}, {}
    for t in targets:
        for h in hours:
            c = cell(h)
            num[(t, c)] = num.get((t, c), 0) + per.get((t, h), 0)
            den[c] = den.get(c, 0) + (tot.get(h, 0) if t == targets[0] else 0)
    for t in targets:
        share[t] = {c: (num.get((t, c), 0) / den[c]) if den.get(c) else 0.0 for c in range(48)}
    sq = mm = 0.0
    for t in targets:
        for h in hours:
            mu = tot.get(h, 0) * share[t][cell(h)]
            y = per.get((t, h), 0)
            sq += (y - mu) ** 2 - mu
            mm += mu * mu
    alpha = max(sq / mm, 0.0) if mm > 0 else 0.0
    return share, alpha


def alarms(per, tot, share, alpha, targets, hours):
    out = []
    for t in targets:
        for h in hours:
            y = per.get((t, h), 0)
            if y < MIN_ACCOUNTS:
                continue
            mu = tot.get(h, 0) * share[t][cell(h)]
            if y > nb_quantile(Q, mu, alpha):
                out.append((t, h, y, mu))
    return out


def run(data, cfg, start_us, end_us, base_start, base_end):
    con = connect(data)
    targets = sorted(register_targets(con, cfg))
    per_b, tot_b = counts(con, data, base_start, base_end)
    per_t, tot_t = counts(con, data, start_us, end_us)
    con.close()
    base_hours = range(base_start // HOUR_US, base_end // HOUR_US)
    test_hours = range(start_us // HOUR_US, end_us // HOUR_US)
    share, alpha = fit(per_b, tot_b, targets, base_hours)
    found = alarms(per_t, tot_t, share, alpha, targets, test_hours)
    summary = {"baseline_hours": len(base_hours), "test_hours": len(test_hours), "alpha": round(alpha, 4),
               "target_hours": len(targets) * len(test_hours), "alarms": len(found)}
    private = [{"target": t, "hour": int(h), "blockers": int(y), "expected": round(mu, 3)} for t, h, y, mu in found]
    return summary, private
