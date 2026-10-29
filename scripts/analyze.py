#!/usr/bin/env python3
"""Coordination and bot-signal analysis for Reddit and X (Twitter) data.

Inputs (mix freely):
  Reddit  Arctic Shift / Pushshift NDJSON (.jsonl/.ndjson/.json/.zst) or Xpoz CSV
  X       API v2 responses (pages with data/includes, or flat tweet objects), v1.1 tweet JSON,
          or Xpoz CSV exports

Outputs:
  narratives.csv        repeated talking points (near-duplicate clusters) and how they spread
  community_flow.csv    community -> community edges (subreddit, or hashtag/conversation on X)
  accounts.csv          per-account bot/coordination signals with evidence, hashed by default
  coordination.graphml  account network: co-similar text, co-link, co-reply, co-retweet
  report.md             summary for a human reviewer

Every score is a lead for human review, never a verdict.
"""
import argparse, csv, glob, hashlib, io, json, math, os, re, subprocess, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from statistics import pstdev, mean

import networkx as nx
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

SKIP_AUTHORS = {"[deleted]", "AutoModerator", "", None}
EXTRA_SKIP = set()  # filled from --skip-authors (known, disclosed bots like clip mirrors)
URL_RE = re.compile(r"https?://[^\s)\]]+")
TAG_RE = re.compile(r"#(\w+)")
SHORTENERS = ("t.co/",)


# ---------- loading ----------
def _open_text(path):
    if path.endswith(".zip"):
        import zipfile
        z = zipfile.ZipFile(path)
        name = next(n for n in z.namelist() if not n.endswith("/"))
        return io.TextIOWrapper(z.open(name), encoding="utf-8", errors="replace")
    if path.endswith(".zst"):
        try:
            import zstandard
            dctx = zstandard.ZstdDecompressor(max_window_size=2**31)
            return io.TextIOWrapper(dctx.stream_reader(open(path, "rb")), encoding="utf-8", errors="replace")
        except ImportError:
            proc = subprocess.Popen(["zstd", "-dc", "--long=31", path], stdout=subprocess.PIPE)
            return io.TextIOWrapper(proc.stdout, encoding="utf-8", errors="replace")
    return open(path, encoding="utf-8", errors="replace")


def _ts(v):
    if v in (None, ""):
        return None
    try:
        v = float(v)
        return v / 1000 if v > 1e11 else v          # milliseconds -> seconds
    except (TypeError, ValueError):
        pass
    s = str(v)
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(s).timestamp()  # v1.1 "Wed Oct 10 20:19:24 +0000 2018"
    except Exception:
        return None


def _clean_url(u):
    if not u or any(s in u for s in SHORTENERS):
        return None
    return u.rstrip("/").split("?")[0].lower()


def _is_x(rec):
    keys = set(rec)
    return bool(keys & {"author_id", "referenced_tweets", "full_text", "retweeted_status",
                        "conversation_id", "screen_name", "tweetId", "retweetCount"}) \
        or ("user" in rec and isinstance(rec.get("user"), dict))


def _norm_reddit(rec):
    author = rec.get("author") or rec.get("author_name") or rec.get("username")
    created = _ts(rec.get("created_utc") or rec.get("createdAtDate") or rec.get("created_at"))
    if created is None or rec.get("distinguished") in ("moderator", "admin"):
        return None  # mod/admin removal notices are templated by design
    title = rec.get("title") or ""
    body = rec.get("body") or rec.get("selftext") or rec.get("text") or ""
    text = (title + "\n" + body).strip() if title else body.strip()
    if text in ("[deleted]", "[removed]"):
        text = ""
    url = rec.get("url") if rec.get("url") and "reddit.com" not in str(rec.get("url")) else None
    if not url:
        m = URL_RE.search(text)
        url = m.group(0) if m else None
    return {
        "platform": "reddit", "id": str(rec.get("id") or rec.get("name") or ""), "author": author,
        "community": str(rec.get("subreddit") or rec.get("subreddit_name") or "").lower(),
        "created": created, "text": text,
        "parent": rec.get("parent_id") or rec.get("link_id") or rec.get("postId"),
        "url": _clean_url(url), "retweet_of": None,
        "author_created": _ts(rec.get("author_created_utc")),
        "author_id": rec.get("author_fullname"),
    }


def _norm_x(rec, users, community_mode):
    # v1.1 nests the author; v2 references it by author_id via includes.users; Xpoz CSV flattens it
    u = rec.get("user") if isinstance(rec.get("user"), dict) else users.get(str(rec.get("author_id")), {})
    author = (u.get("screen_name") or u.get("username") or rec.get("authorUsername")
              or rec.get("author_username") or rec.get("username") or rec.get("author_id"))
    created = _ts(rec.get("created_at") or rec.get("createdAt") or rec.get("createdAtDate"))
    if created is None or not author:
        return None
    refs = {r.get("type"): str(r.get("id")) for r in rec.get("referenced_tweets") or [] if isinstance(r, dict)}
    rt = refs.get("retweeted") or (str(rec["retweeted_status"].get("id_str") or rec["retweeted_status"].get("id"))
                                   if isinstance(rec.get("retweeted_status"), dict) else None) \
        or rec.get("retweetedTweetId") or rec.get("retweeted_tweet_id")
    text = rec.get("full_text") or rec.get("text") or rec.get("content") or ""
    if not rt and str(text).startswith("RT @"):
        rt = "text:" + hashlib.md5(text.encode()).hexdigest()  # flattened exports with no RT id
    ents = rec.get("entities") or {}
    urls = [x.get("expanded_url") or x.get("unwound_url") for x in ents.get("urls") or [] if isinstance(x, dict)]
    url = next((_clean_url(x) for x in urls if _clean_url(x)), None)
    if not url:
        m = URL_RE.search(text)
        url = _clean_url(m.group(0)) if m else None
    tags = [t.get("tag") or t.get("text") for t in ents.get("hashtags") or [] if isinstance(t, dict)] \
        or TAG_RE.findall(text)
    conv = rec.get("conversation_id") or rec.get("conversationId")
    reply_to = refs.get("replied_to") or rec.get("in_reply_to_status_id_str") or rec.get("inReplyToTweetId")
    if community_mode == "conversation" and conv:
        community = f"conv:{conv}"
    else:
        community = ("#" + tags[0].lower()) if tags else "#(none)"
    acc = u.get("created_at") or rec.get("authorCreatedAt") or rec.get("author_created_at")
    return {
        "platform": "x", "id": str(rec.get("id_str") or rec.get("id") or rec.get("tweetId") or ""),
        "author": str(author), "community": community, "created": created,
        "text": "" if rt else str(text).strip(),        # retweets carry someone else's text
        "parent": reply_to or refs.get("quoted"), "url": url, "retweet_of": rt,
        "author_created": _ts(acc),
        "author_id": None,
    }


def _records(obj):
    """Yield (record, users_lookup) from a parsed JSON value (tweet, list, or v2 page)."""
    if isinstance(obj, list):
        for o in obj:
            yield from _records(o)
    elif isinstance(obj, dict) and "data" in obj and isinstance(obj["data"], (list, dict)):
        users = {str(u.get("id")): u for u in (obj.get("includes") or {}).get("users", [])}
        data = obj["data"] if isinstance(obj["data"], list) else [obj["data"]]
        for d in data:
            yield d, users
    elif isinstance(obj, dict):
        yield obj, {}


def load(paths, community_mode):
    rows = []

    def add(rec, users):
        r = _norm_x(rec, users, community_mode) if _is_x(rec) else _norm_reddit(rec)
        if r and r["author"] not in SKIP_AUTHORS and r["author"] not in EXTRA_SKIP:
            rows.append(r)

    for pattern in paths:
        for path in sorted(glob.glob(pattern)) or [pattern]:
            if path.endswith(".csv"):
                with open(path, encoding="utf-8", errors="replace") as fh:
                    for rec in csv.DictReader(fh):
                        add(rec, {})
                continue
            with _open_text(path) as fh:
                head = fh.read(1)
                if head in ("[",) or path.endswith(".json"):
                    try:
                        for rec, users in _records(json.loads(head + fh.read())):
                            add(rec, users)
                        continue
                    except json.JSONDecodeError:
                        fh = _open_text(path); head = ""
                for line in ([head + fh.readline()] if head else []) + list(fh):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    for rec, users in _records(obj):
                        add(rec, users)
    return rows


# ---------- known bots (Bot Bouncer) ----------
def load_known_bots(paths, before=None):
    """Usernames Bot Bouncer marked banned (optionally only listings before a date), plus plain-text lists."""
    import zipfile
    cut = datetime.fromisoformat(before).replace(tzinfo=timezone.utc).timestamp() if before else None
    user_rx = re.compile(r"/(?:user|u)/([A-Za-z0-9_-]{3,20})|^Overview for ([A-Za-z0-9_-]{3,20})")
    names = set()

    def take(lines):
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if not line.startswith("{"):
                names.add(re.sub(r"^/?u/", "", line).lower())
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("link_flair_text") != "banned":
                continue  # pending, organic (human), purged or unresolved
            if cut and float(r.get("created_utc") or 0) >= cut:
                continue
            m = user_rx.search(r.get("url") or "") or user_rx.search(r.get("title") or "")
            if m:
                names.add((m.group(1) or m.group(2)).lower())

    for p in paths:
        if p.endswith(".zip"):
            with zipfile.ZipFile(p) as z:
                for n in z.namelist():
                    with z.open(n) as fh:
                        take(io.TextIOWrapper(fh, encoding="utf-8", errors="replace"))
        else:
            with _open_text(p) as fh:
                take(fh)
    return names


# ---------- identity handling ----------
class Ids:
    def __init__(self, salt, reveal):
        self.salt, self.reveal = salt, reveal

    def show(self, author, tier=None):
        if self.reveal == "all" or (self.reveal == "bots" and tier in ("high", "known")):
            return author
        return "acct_" + hashlib.sha256((self.salt + author).encode()).hexdigest()[:10]


# ---------- talking-point clusters ----------
BRUTE_LIMIT = int(os.environ.get("COORD_BRUTE_LIMIT", 40000))  # above this many texts, use MinHash LSH to find candidate pairs first


def _lsh_pairs(texts, X, threshold, bands=20, rows=3, big_bucket=200, reps=5):
    """Candidate near-duplicate pairs via MinHash LSH on 5-char shingles, verified by TF-IDF cosine."""
    import zlib
    P = (1 << 31) - 1
    rng = np.random.default_rng(1)
    k = bands * rows
    a = rng.integers(1, P, k, dtype=np.int64)
    b = rng.integers(0, P, k, dtype=np.int64)
    sigs = np.empty((len(texts), k), dtype=np.int64)
    for n, t in enumerate(texts):
        t = " ".join(t.split())
        sh = {t[i:i + 5] for i in range(max(1, len(t) - 4))}
        h = np.fromiter((zlib.crc32(s.encode()) for s in sh), dtype=np.int64, count=len(sh)) % P
        sigs[n] = ((h[:, None] * a + b) % P).min(axis=0)
    cand = set()
    for j in range(bands):
        buckets = defaultdict(list)
        for n, key in enumerate(map(bytes, sigs[:, j * rows:(j + 1) * rows])):
            buckets[key].append(n)
        for members in buckets.values():
            m = len(members)
            if m < 2:
                continue
            if m <= big_bucket:
                cand.update((members[x], members[y]) for x in range(m) for y in range(x + 1, m))
            else:  # mass-posted text: link everyone to a few representatives instead of all pairs
                cand.update((members[r], members[y]) for r in range(reps) for y in range(r + 1, m))
    if not cand:
        return []
    pairs = np.array(sorted(cand))
    keep = []
    for s in range(0, len(pairs), 200000):
        chunk = pairs[s:s + 200000]
        sims = np.asarray(X[chunk[:, 0]].multiply(X[chunk[:, 1]]).sum(axis=1)).ravel()
        keep.extend(map(tuple, chunk[sims >= threshold]))
    return keep


def cluster_texts(rows, threshold, min_words):
    idx = [i for i, r in enumerate(rows) if len(r["text"].split()) >= min_words]
    if len(idx) < 2:
        return {}
    texts = [TAG_RE.sub(" ", URL_RE.sub(" ", rows[i]["text"].lower())) for i in idx]
    X = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True).fit_transform(texts)
    g = nx.Graph()
    g.add_nodes_from(range(len(idx)))
    if len(idx) <= BRUTE_LIMIT:
        nn = NearestNeighbors(radius=1 - threshold, metric="cosine", algorithm="brute").fit(X)
        for start in range(0, X.shape[0], 2000):
            _, neigh = nn.radius_neighbors(X[start:start + 2000])
            for off, ns in enumerate(neigh):
                a = start + off
                g.add_edges_from((a, b) for b in ns if b > a)
    else:
        g.add_edges_from(_lsh_pairs(texts, X, threshold))
    out, cid = {}, 0
    for comp in nx.connected_components(g):
        members = [idx[k] for k in comp]
        if len({rows[m]["author"] for m in members}) >= 2:
            for m in members:
                out[m] = cid
            cid += 1
    return out


# ---------- coordination edges ----------
def coordination_graph(rows, clusters, windows):
    g = nx.Graph()

    def link(a, b, kind):
        if a == b:
            return
        if g.has_edge(a, b):
            g[a][b]["weight"] += 1
            g[a][b][kind] = g[a][b].get(kind, 0) + 1
        else:
            g.add_edge(a, b, weight=1, **{kind: 1})

    groups = {k: defaultdict(list) for k in windows}
    for i, r in enumerate(rows):
        if i in clusters: groups["co_similar"][clusters[i]].append(r)
        if r["url"]: groups["co_link"][r["url"]].append(r)
        # top-level comments on the same Reddit post are thread co-participation, not a reply pile-on
        if r["parent"] and not str(r["parent"]).startswith("t3_"): groups["co_reply"][r["parent"]].append(r)
        if r["retweet_of"]: groups["co_retweet"][r["retweet_of"]].append(r)
    for kind, buckets in groups.items():
        w = windows[kind]
        for items in buckets.values():
            items.sort(key=lambda r: r["created"])
            for i, r in enumerate(items):
                for s in items[i + 1:]:
                    if s["created"] - r["created"] > w:
                        break
                    link(r["author"], s["author"], kind)
    return g


# ---------- per-account signals ----------
def _id_num(fullname):
    try:
        return int(str(fullname)[3:], 36) if str(fullname).startswith("t2_") else None
    except ValueError:
        return None


def account_signals(rows, clusters, g, min_edge_weight, new_pct=3.0, known=frozenset()):
    by_author = defaultdict(list)
    for i, r in enumerate(rows):
        by_author[r["author"]].append((i, r))
    # Reddit account IDs are issued in sign-up order, so the highest IDs are the newest accounts.
    idn = {}
    for a, items in by_author.items():
        for _, r in items:
            v = _id_num(r.get("author_id"))
            if v:
                idn[a] = v
                break
    ranked = sorted(idn.values())
    new_cut = ranked[int(len(ranked) * (1 - new_pct / 100))] if ranked and new_pct > 0 else None
    out = {}
    for author, items in by_author.items():
        items.sort(key=lambda x: x[1]["created"])
        n = len(items)
        ts = [r["created"] for _, r in items]
        gaps = [b - a for a, b in zip(ts, ts[1:]) if b > a]
        flags = defaultdict(list)

        texts = [(i, r) for i, r in items if r["text"]]
        nt = len(texts)
        shared = sum(1 for i, _ in texts if i in clusters)
        dup_ratio = shared / nt if nt else 0.0
        if nt >= 5 and dup_ratio >= 0.5:
            flags["content"].append(f"{dup_ratio:.0%} of written posts repeat text from other accounts")
        own = Counter(r["text"].lower() for _, r in texts if len(r["text"].split()) >= 4)
        self_rep = sum(c for c in own.values() if c > 1) / nt if nt else 0.0
        if nt >= 5 and self_rep >= 0.4:
            flags["content"].append(f"{self_rep:.0%} of written posts are verbatim self-repeats")
        rt_ratio = sum(1 for _, r in items if r["retweet_of"]) / n
        if n >= 20 and rt_ratio >= 0.9:
            flags["content"].append(f"{rt_ratio:.0%} of activity is reposts (amplification only)")

        cv = ent = None
        if len(gaps) >= 9:
            cv = pstdev(gaps) / mean(gaps)
            if cv < 0.35:
                flags["timing"].append(f"posting intervals unusually regular (CV {cv:.2f})")
        if n >= 30:
            hours = Counter(int((t % 86400) // 3600) for t in ts)
            ent = -sum((c / n) * math.log(c / n) for c in hours.values()) / math.log(24)
            if ent > 0.95:
                flags["timing"].append(f"posts evenly around the clock (hour entropy {ent:.2f})")
        burst, j = 0, 0
        for k, t in enumerate(ts):
            while ts[j] < t - 600:
                j += 1
            burst = max(burst, k - j + 1)
        if burst >= 10:
            flags["timing"].append(f"{burst} items within 10 minutes")

        partners = [nb for nb in g.neighbors(author) if g[author][nb]["weight"] >= min_edge_weight] if author in g else []
        if len(partners) >= 3:
            kinds = Counter(k for nb in partners for k in g[author][nb] if k.startswith("co_"))
            flags["network"].append(f"repeatedly acts in sync with {len(partners)} accounts ({', '.join(kinds)})")

        age_days = None
        if items[0][1]["author_created"]:
            age_days = (ts[0] - items[0][1]["author_created"]) / 86400
            if age_days < 30:
                flags["account"].append(f"account was {age_days:.0f} days old at first item")
        elif new_cut is not None and idn.get(author, 0) >= new_cut:
            flags["account"].append(f"among the newest {new_pct:g}% of accounts in this data (by account ID)")

        fams = len(flags)
        tier = "high" if fams >= 3 and n >= 10 else "likely" if fams >= 2 else "lead" if fams == 1 else ""
        out[author] = {
            "platform": items[0][1]["platform"], "items": n,
            "communities": len({r["community"] for _, r in items}),
            "dup_ratio": round(dup_ratio, 3), "self_repeat": round(self_rep, 3), "repost_ratio": round(rt_ratio, 3),
            "interval_cv": round(cv, 3) if cv is not None else "",
            "hour_entropy": round(ent, 3) if ent is not None else "",
            "max_10min_burst": burst, "sync_partners": len(partners),
            "account_age_days": round(age_days, 1) if age_days is not None else "",
            "known_bot": "yes" if author.lower() in known else "",
            "signal_families": fams, "tier": tier,
            "evidence": " | ".join(f"[{k}] {v}" for k, vs in flags.items() for v in vs),
        }
    return out


# ---------- narratives & cross-community flow ----------
def narratives(rows, clusters, accounts, ids):
    groups = defaultdict(list)
    for i, c in clusters.items():
        groups[c].append(rows[i])
    narr, flow = [], Counter()
    for c, items in groups.items():
        items.sort(key=lambda r: r["created"])
        firsts = {}
        for r in items:
            firsts.setdefault((r["platform"], r["community"]), r["created"])
        order = sorted(firsts, key=firsts.get)
        label = lambda k: ("r/" if k[0] == "reddit" else "x:") + k[1]
        for a, b in zip(order, order[1:]):
            flow[(label(a), label(b))] += 1
        authors = {r["author"] for r in items}
        first = items[0]["author"]
        narr.append({
            "cluster": c, "items": len(items), "accounts": len(authors),
            "flagged_accounts": sum(1 for a in authors if accounts.get(a, {}).get("tier") in ("likely", "high")),
            "platforms": "+".join(sorted({r["platform"] for r in items})),
            "communities": len(firsts), "first_community": label(order[0]),
            "spread_order": " > ".join(label(k) for k in order),
            "first_seen_utc": int(items[0]["created"]),
            "span_hours": round((items[-1]["created"] - items[0]["created"]) / 3600, 1),
            "first_author": ids.show(first, accounts.get(first, {}).get("tier")),
            "example": items[0]["text"][:200].replace("\n", " "),
        })
    narr.sort(key=lambda d: (d["communities"], d["accounts"]), reverse=True)
    return narr, flow


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        if rows:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="files or globs: .jsonl/.ndjson/.json/.zst/.csv")
    ap.add_argument("-o", "--out", default="coord_out")
    ap.add_argument("--similarity", type=float, default=0.9, help="cosine threshold for near-duplicate text")
    ap.add_argument("--min-words", type=int, default=8, help="ignore short texts (memes, 'lol')")
    ap.add_argument("--sim-window", type=int, default=3600, help="seconds: same talking point by two accounts")
    ap.add_argument("--link-window", type=int, default=120, help="seconds: same URL by two accounts")
    ap.add_argument("--reply-window", type=int, default=120, help="seconds: same parent replied to by two accounts")
    ap.add_argument("--retweet-window", type=int, default=60, help="seconds: same post reposted by two accounts (X)")
    ap.add_argument("--min-edge-weight", type=int, default=3, help="sync events needed to count a partner")
    ap.add_argument("--x-community", choices=["hashtag", "conversation"], default="hashtag",
                    help="what counts as a 'community' on X for the spread map")
    ap.add_argument("--reveal", choices=["none", "bots", "all"], default="none",
                    help="none: hash all usernames; bots: show only high-tier; all: own-community moderation only")
    ap.add_argument("--salt", default=None, help="hash salt (saved to out/.salt; reuse it to keep IDs stable)")
    ap.add_argument("--skip-authors", default="", help="comma-separated accounts to exclude (disclosed bots)")
    ap.add_argument("--known-bots", nargs="*", default=[],
                    help="r/BotBouncer post dumps (.json/.jsonl/.zip) and/or text files with one username per line")
    ap.add_argument("--known-before", default=None,
                    help="YYYY-MM-DD: only use Bot Bouncer listings made before this date (keeps tests honest)")
    ap.add_argument("--new-account-pct", type=float, default=3.0,
                    help="flag accounts among the newest N%% by Reddit account ID when creation dates are missing (0 = off)")
    a = ap.parse_args()
    EXTRA_SKIP.update(x.strip() for x in a.skip_authors.split(",") if x.strip())

    os.makedirs(a.out, exist_ok=True)
    salt_path = os.path.join(a.out, ".salt")
    salt = a.salt or (open(salt_path).read().strip() if os.path.exists(salt_path) else os.urandom(8).hex())
    open(salt_path, "w").write(salt)
    ids = Ids(salt, a.reveal)

    rows = load(a.inputs, a.x_community)
    if not rows:
        sys.exit("No usable rows loaded. Check the file format and fields.")
    plat = Counter(r["platform"] for r in rows)
    print(f"loaded {len(rows)} items ({', '.join(f'{k} {v}' for k, v in plat.items())}) "
          f"from {len({r['author'] for r in rows})} accounts in {len({r['community'] for r in rows})} communities")

    clusters = cluster_texts(rows, a.similarity, a.min_words)
    g = coordination_graph(rows, clusters, {"co_similar": a.sim_window, "co_link": a.link_window,
                                            "co_reply": a.reply_window, "co_retweet": a.retweet_window})
    known = load_known_bots(a.known_bots, a.known_before) if a.known_bots else set()
    if a.known_bots:
        print(f"known bots loaded: {len(known)}")
    accounts = account_signals(rows, clusters, g, a.min_edge_weight, a.new_account_pct, known)
    narr, flow = narratives(rows, clusters, accounts, ids)

    write_csv(os.path.join(a.out, "narratives.csv"), narr)
    write_csv(os.path.join(a.out, "community_flow.csv"),
              [{"from": x, "to": y, "talking_points": n} for (x, y), n in flow.most_common()])
    acc_rows = [{"account": ids.show(au, "known" if d["known_bot"] else d["tier"]), **d} for au, d in accounts.items()]
    acc_rows.sort(key=lambda d: (d["signal_families"], d["sync_partners"], d["dup_ratio"]), reverse=True)
    write_csv(os.path.join(a.out, "accounts.csv"), acc_rows)

    h = nx.Graph()
    for u, v, d in g.edges(data=True):
        if d["weight"] >= a.min_edge_weight:
            h.add_edge(ids.show(u, accounts[u]["tier"]), ids.show(v, accounts[v]["tier"]), **d)
    nx.write_graphml(h, os.path.join(a.out, "coordination.graphml"))

    tiers = Counter(d["tier"] for d in accounts.values() if d["tier"])
    comps = sorted(nx.connected_components(h), key=len, reverse=True)
    lines = [
        "# Coordination analysis report", "",
        f"Items: {len(rows)} ({', '.join(f'{k} {v}' for k, v in plat.items())}) · accounts: {len(accounts)} "
        f"· communities: {len({r['community'] for r in rows})}",
        f"Repeated talking points (2+ accounts): {len(narr)}",
        f"Accounts flagged: high {tiers.get('high', 0)} · likely {tiers.get('likely', 0)} · lead {tiers.get('lead', 0)}",
        f"Synchronized account groups (edge weight >= {a.min_edge_weight}): {len(comps)}; "
        f"largest {len(comps[0]) if comps else 0}",
        "", "Every flag below is a lead for human review. Read the underlying posts before acting.", "",
        "## Top cross-community talking points", "",
    ]
    for d in narr[:15]:
        lines.append(f"- {d['communities']} communities ({d['platforms']}), {d['accounts']} accounts "
                     f"({d['flagged_accounts']} flagged), {d['span_hours']}h: {d['spread_order']}  \n"
                     f"  \"{d['example'][:140]}\"")
    lines += ["", "## Strongest community flows", ""]
    lines += [f"- {x} → {y}: {n} talking points" for (x, y), n in flow.most_common(10)]
    kb = [d for d in acc_rows if d["known_bot"]]
    if a.known_bots:
        lines += ["", "## Accounts already listed as bots by Bot Bouncer", "",
                  f"{len(kb)} listed accounts were active here ({sum(d['items'] for d in kb)} items). "
                  "Bot Bouncer bans carry over across subs only where a sub runs it, so these are often still posting.", ""]
        lines += [f"- {d['account']} ({d['items']} items, tier {d['tier'] or 'none'}){': ' + d['evidence'] if d['evidence'] else ''}"
                  for d in sorted(kb, key=lambda d: -d["items"])[:30]]
    lines += ["", "## Highest-signal accounts", ""]
    lines += [f"- {d['account']} ({d['platform']}, {d['tier']}, {d['items']} items): {d['evidence']}"
              for d in acc_rows[:15] if d["tier"]]
    open(os.path.join(a.out, "report.md"), "w").write("\n".join(lines) + "\n")
    print(f"wrote {a.out}/report.md, narratives.csv, community_flow.csv, accounts.csv, coordination.graphml")


if __name__ == "__main__":
    main()
