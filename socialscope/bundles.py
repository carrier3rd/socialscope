"""Idea bundles and cross-sub pollination.

    from socialscope import bundles
    acc = bundles.tag(["week/*_comments_*.zip", "histories/*_comments.zip"], out_dir="bundles")
    bundles.cooccur(acc, out_dir="bundles")      # which positions the same accounts hold, beyond chance
    bundles.crossover(acc, out_dir="bundles")    # who comments outside their main sub, how they're received,
                                                 # and which positions they carry

Positions are regex patterns in positions.py (stance toward a person or issue, e.g. hasan_neg, anti_ice).
Check each pattern by reading ~12 random matches before trusting it; drop any under ~65% accurate.
On the Oct 2026 corpus, 13 of 23 drafted patterns passed.

The null model matters. Accounts that talk politics hit many patterns, including opposite ones, so a plain
co-occurrence count says "everything goes with everything". cooccur() compares against curveball
randomizations that keep each account's number of positions and each position's count, within home sub.
"""
import csv, glob, itertools, json, os, random, zipfile
from collections import Counter, defaultdict
from statistics import median

from .positions import RX

SIX = ("h3h3productions", "Destiny", "LivestreamFail", "Hasan_Piker", "atrioc", "h3snark")


def _rows(inputs):
    for p in ([inputs] if isinstance(inputs, str) else inputs):
        for f in sorted(glob.glob(p)) or [p]:
            z = zipfile.ZipFile(f) if f.endswith(".zip") else None
            fh = z.open(z.namelist()[0]) if z else open(f, "rb")
            with fh:
                for line in fh:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue


def tag(inputs, subs=SIX, out_dir="bundles", start=None, end=None):
    """Tag every comment with the positions it takes. Returns a dict used by cooccur() and crossover()."""
    seen, acts, hits, week = set(), defaultdict(Counter), [], []
    for r in _rows(inputs):
        i, b, a = r.get("id"), r.get("body"), r.get("author")
        if not i or i in seen or not b or b in ("[deleted]", "[removed]") or a in (None, "[deleted]", "AutoModerator"):
            continue
        t = float(r.get("created_utc") or 0)
        seen.add(i)
        s = str(r.get("subreddit") or "")
        acts[a][s] += 1
        if s in subs and (start is None or t >= start) and (end is None or t < end):
            week.append((a, s, r.get("score") or 0))
        for k, rx in RX.items():
            if rx.search(b):
                hits.append((a, k, s, t, i, r.get("link_id")))
    home = {}
    for a, c in acts.items():
        best = max(subs, key=lambda x: c[x])
        home[a] = best if c[best] else None
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "position_counts.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["position", "comments", "accounts"])
        for k in RX:
            w.writerow([k, sum(h[1] == k for h in hits), len({h[0] for h in hits if h[1] == k})])
    return {"acts": acts, "hits": hits, "home": home, "week": week, "subs": subs}


def _curveball(rows, groups, trades):
    rows = [set(r) for r in rows]
    gl = [g for g in groups.values() if len(g) > 1]
    weights = [len(g) for g in gl]
    for _ in range(trades):
        g = random.choices(gl, weights)[0]
        a, b = random.sample(g, 2)
        A, B = rows[a], rows[b]
        sa, sb = A - B, B - A
        if not sa and not sb:
            continue
        pool = list(sa | sb); random.shuffle(pool)
        rows[a] = (A & B) | set(pool[:len(sa)]); rows[b] = (A & B) | set(pool[len(sa):])
    return rows


def cooccur(acc, out_dir="bundles", min_comments=10, sims=400, seed=1, z_edge=2.0):
    """Pairwise co-occurrence vs a curveball null within home sub; clusters positions into bundles."""
    random.seed(seed)
    P = list(RX)
    held = defaultdict(set)
    for a, k, *_ in acc["hits"]:
        held[a].add(P.index(k))
    pop = [a for a in held if sum(acc["acts"][a].values()) >= min_comments]
    rows = [held[a] for a in pop]
    groups = defaultdict(list)
    for i, a in enumerate(pop):
        groups[acc["home"][a]].append(i)

    def count(rs):
        m = Counter()
        for r in rs:
            for i, j in itertools.combinations(sorted(r), 2):
                m[(i, j)] += 1
        return m
    obs = count(rows)
    cur = _curveball(rows, groups, 20000)
    nulls = []
    for _ in range(sims):
        cur = _curveball(cur, groups, 2000); nulls.append(count(cur))
    out = []
    for i, j in itertools.combinations(range(len(P)), 2):
        v = [n[(i, j)] for n in nulls]
        mu = sum(v) / len(v); sd = (sum((x - mu) ** 2 for x in v) / len(v)) ** 0.5 or 1e-9
        out.append({"a": P[i], "b": P[j], "observed": obs[(i, j)], "expected": round(mu, 1),
                    "lift": round(obs[(i, j)] / mu, 2) if mu else "", "z": round((obs[(i, j)] - mu) / sd, 1)})
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "pairs.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(sorted(out, key=lambda r: -r["z"]))
    try:
        import networkx as nx
        from networkx.algorithms.community import louvain_communities
        G = nx.Graph(); G.add_nodes_from(P)
        G.add_edges_from((r["a"], r["b"], {"weight": r["z"]}) for r in out if r["z"] >= z_edge)
        comms = [sorted(c) for c in louvain_communities(G, weight="weight", seed=0)]
    except ImportError:
        comms = []
    open(os.path.join(out_dir, "bundles.json"), "w").write(json.dumps(comms, indent=1))
    print(f"{len(pop)} accounts; bundles: {[c for c in comms if len(c) > 1]}")
    return comms


def crossover(acc, bundles_of=None, out_dir="bundles"):
    """Who comments outside their main sub, how they score there, and which positions they carry in."""
    subs, home = acc["subs"], acc["home"]
    cnt, sc = defaultdict(Counter), defaultdict(list)
    for a, s, score in acc["week"]:
        cnt[s][home[a]] += 1; sc[(s, home[a])].append(score)
    rows = []
    for s in subs:
        loc = sc.get((s, s)) or [0]
        for h, n in cnt[s].most_common():
            if h == s or n < 20:
                continue
            v = sc[(s, h)]
            rows.append({"into": s, "from": h, "comments": n, "share_of_sub": round(100 * n / sum(cnt[s].values()), 1),
                         "median_score": median(v), "local_median": median(loc),
                         "pct_at_or_below_0": round(100 * sum(x < 1 for x in v) / len(v)),
                         "local_pct_at_or_below_0": round(100 * sum(x < 1 for x in loc) / len(loc))})
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "visitors.csv"), "w", newline="") as fh:
        if rows:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    flow = Counter()
    for a, k, s, t, i, *_ in acc["hits"]:
        b = (bundles_of or {}).get(k, k)
        if s in subs and s != home.get(a):
            flow[(b, home.get(a), s)] += 1
    with open(os.path.join(out_dir, "carried.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["position_or_bundle", "from_home", "into", "comments"])
        for (b, h, s), n in flow.most_common():
            w.writerow([b, h, s, n])
    return os.path.join(out_dir, "visitors.csv")


def amplifiers(acc, window=3600, min_threads=3, out_dir="bundles"):
    """Seeder -> amplifier pairs (the EEAS pattern: seeders post, amplifiers echo within minutes). For every position
    asserted in a thread, any other account asserting the same position in the same thread within `window` seconds
    counts as following the first. Pairs that repeat across min_threads+ different threads are written to
    amplifier_pairs.csv (hashed names). Ordinary allies in one argument rarely repeat across many threads."""
    import hashlib
    by = defaultdict(list)
    for a, k, s, t, i, link in acc["hits"]:
        if link:
            by[(link, k)].append((t, a))
    pairs = defaultdict(set)
    for (link, k), xs in by.items():
        xs.sort()
        for j, (t1, a1) in enumerate(xs):
            for t2, a2 in xs[j + 1:]:
                if t2 - t1 > window:
                    break
                if a2 != a1:
                    pairs[(a1, a2)].add(link)
    from . import salt as _salt
    salt = _salt.get()
    h = lambda a: "acct_" + hashlib.sha256((salt + a).encode()).hexdigest()[:10]
    rows = [{"seeder": h(a1), "amplifier": h(a2), "threads": len(ls)} for (a1, a2), ls in pairs.items() if len(ls) >= min_threads]
    rows.sort(key=lambda r: -r["threads"])
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "amplifier_pairs.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["seeder", "amplifier", "threads"]); w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} seeder->amplifier pairs repeating in {min_threads}+ threads")
    return rows


OPPOSED = (("hasan_neg", "hasan_pos"), ("gaza_genocide", "israel_defense"), ("anti_zionist", "israel_defense"))


def mixed(acc, out_dir="bundles"):
    """Accounts asserting opposed positions (EEAS: for-hire amplifiers boost unrelated or contradictory content).
    Usually a person arguing both sides or a pattern misfire; read the comments before reading anything into it."""
    held = defaultdict(set)
    for a, k, *_ in acc["hits"]:
        held[a].add(k)
    out = [a for a, ks in held.items() if any(x in ks and y in ks for x, y in OPPOSED)]
    print(f"{len(out)} accounts asserted opposed positions")
    return out
