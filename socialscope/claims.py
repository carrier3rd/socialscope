"""Claim checking: find checkable factual claims, track how rated claims spread, and score accounts.

Three steps, mirroring the stance workflow (the machine finds and counts, a person or Claude checks):

    from socialscope import claims
    claims.candidates("pulls/*.zip", out_dir="claims")          # 1. comments that state something checkable
    # 2. distill distinct claims into claims.csv (id, claim, rating, pattern, direction, source, note) and
    #    check each one against sources. Ratings: true, mostly_true, misleading, false, unverifiable.
    claims.spread("pulls/*.zip", "claims/claims.csv", out_dir="claims")   # 3. who said each claim, where, how it fared
    claims.accounts("claims/matches.csv", out_dir="claims", bot_flags="history_scores/accounts.csv")

`pattern` in claims.csv is a regular expression matched against comment text (case-insensitive); write it so it
catches people asserting the claim. An optional `thread` column is a regex the thread title must also match (for
comments that never name the subject, like "he's an insider trader" under a post about Ro Khanna).
Patterns also catch people disputing a claim, so read every match of a false or misleading claim and fill the
`stance` column of matches.csv (assert / dispute / other) before running accounts(); unreviewed rows count as asserts.
Optional columns carried into spread.csv: `origin_pillar` (where the narrative started, using the GEC "Pillars"
categories: official, state_media, proxy, social_media, cyber_forgery), `first_official` (when and where an official
first said it, so its first appearance in the subs can be timed against it) and `forged` (yes if the claim rests on
fabricated documents, video or fake news sites).
`direction` is who the claim favors or hurts ("anti-Hasan", "pro-Destiny", "none"), used for the pattern test.

Account levels (accounts.csv). An `authenticity` column sits beside them: "ai_style" when the account's writing
reads as AI-generated (10%+ of its history with AI-tic words or em dashes, or a third of its claim items), "some_ai_style"
when any does. It lowers how much weight the account's words carry as a person's own; it is never proof of a bot.
  repeat_spreader  3+ distinct false/misleading claims, or repeated a false claim after a reply corrected it
  one_directional  2+ false/misleading claims, all in the same direction
  one_off          1 false/misleading claim
Names are hashed unless reveal="all" (private use only).
"""
import csv, glob, hashlib, json, os, re, zipfile
from collections import Counter, defaultdict

CUES = [
    r"\b\d[\d,.]*\s?(?:%|percent|k\b|m\b|million|billion|thousand|viewers|subs|votes|days|years|dollars)",
    r"\$\s?\d", r"\baccording to\b", r"\breport(?:ed|s)?\b", r"\bconfirm(?:ed|s)\b", r"\bannounc(?:ed|es)\b",
    r"\b(?:he|she|they|it) (?:said|says|admitted|claimed|lied|never said)\b", r"\badmitted\b",
    r"\b(?:was|got|been|is being) (?:fired|banned|arrested|charged|sued|suspended|executed|shut down|caught|paid)\b",
    r"\bunder investigation\b", r"\bin fact\b", r"\bthe (?:data|numbers|stats|study|poll) (?:shows?|says?)\b",
    r"\b(?:view ?bott?(?:ed|ing|s)?|bot farm)\b", r"\b(?:fake|staged|scripted|doctored|edited)\b",
    r"\bfunded by\b", r"\bpaid (?:by|for)\b", r"\bsource\b", r"\bfact\b", r"\bproof\b", r"\bliterally (?:said|did)\b",
    r"\b(?:19|20)\d\d\b", r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.? \d{1,2}\b",
]
CUE_RE = [re.compile(c, re.I) for c in CUES]
CORRECTION = re.compile(r"\b(?:not true|that's false|that is false|fake news|misinformation|disinformation|debunked|"
                        r"source\?|citation needed|no it (?:wasn't|isn't|didn't)|that never happened|you're lying|"
                        r"this is false|wrong[,.!]|that's wrong|false\b|made up|lie\b|lying)", re.I)
RATED_BAD = {"false", "misleading"}


def _rows(inputs):
    paths = []
    for p in ([inputs] if isinstance(inputs, str) else inputs):
        paths += sorted(glob.glob(p)) or [p]
    for p in paths:
        z = zipfile.ZipFile(p) if p.endswith(".zip") else None
        fh = z.open(z.namelist()[0]) if z else open(p, "rb")
        with fh:
            for line in fh:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def _load(inputs):
    posts, comments = {}, []
    for r in _rows(inputs):
        if r.get("author") in (None, "[deleted]", "AutoModerator") or r.get("distinguished") in ("moderator", "admin"):
            continue
        if "title" in r:
            posts["t3_" + r["id"]] = r
        elif r.get("body") not in (None, "[deleted]", "[removed]"):
            comments.append(r)
    return posts, comments


def cue_score(text):
    """How many claim cues a text has (0+). Questions and /s sarcasm score 0."""
    t = (text or "").strip()
    if len(t.split()) < 6 or t.rstrip().endswith("?") or re.search(r"(?:^|\s)/s\b", t):
        return 0
    return sum(bool(rx.search(t)) for rx in CUE_RE)


def candidates(inputs, out_dir="claims", min_cues=2, top=3000):
    """Comments with min_cues+ claim cues, ranked by cues then upvotes. Writes candidates.csv and summary.md."""
    posts, comments = _load(inputs)
    rows = []
    for r in comments:
        s = cue_score(r.get("body"))
        if s >= min_cues:
            p = posts.get(r.get("link_id"), {})
            rows.append({"id": r["id"], "sub": r.get("subreddit"), "cues": s, "score": r.get("score") or 0,
                         "thread": (p.get("title") or "")[:140], "text": " ".join((r.get("body") or "").split())[:600]})
    rows.sort(key=lambda x: (-x["cues"], -x["score"]))
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "candidates.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "sub", "cues", "score", "thread", "text"]); w.writeheader()
        w.writerows(rows[:top])
    by_sub = Counter(r.get("subreddit") for r in comments)
    cand_sub = Counter(r["sub"] for r in rows)
    md = ["# Claim candidates", "", f"Comments read: {len(comments):,}. With {min_cues}+ claim cues: {len(rows):,} "
          f"({100 * len(rows) / max(1, len(comments)):.1f}%). Cues find claim-shaped text; most candidates still need a person to judge.", "",
          "| Sub | Comments | Candidates | Share |", "|---|---|---|---|"]
    md += [f"| r/{s} | {n:,} | {cand_sub[s]:,} | {100 * cand_sub[s] / n:.1f}% |" for s, n in by_sub.most_common()]
    open(os.path.join(out_dir, "summary.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md))
    return os.path.join(out_dir, "candidates.csv")


def _hash(salt, a):
    return "acct_" + hashlib.sha256((salt + a).encode()).hexdigest()[:10]


def spread(inputs, claims_csv, out_dir="claims", reveal="none", salt=None, stances=None):
    """Match each claim's pattern against every comment and post title. Writes matches.csv (one row per
    matching item) and spread.csv (per claim: items, accounts, subs, median score, share corrected in replies).
    stances: a reviewed CSV (claim_id, item, stance = assert/dispute/other); reviewed claims are then counted
    by asserting items only, with disputes reported beside them."""
    posts, comments = _load(inputs)
    claims = list(csv.DictReader(open(claims_csv, encoding="utf-8")))
    pats = [(c, re.compile(c["pattern"], re.I), re.compile(c["thread"], re.I) if c.get("thread") else None)
            for c in claims if c.get("pattern")]
    replies = defaultdict(list)
    for r in comments:
        replies[r.get("parent_id")].append(r)
    from . import salt as _salt
    salt = _salt.get(salt)
    name = (lambda a: a) if reveal == "all" else (lambda a: _hash(salt, a))
    items = [(r, r.get("body") or "", "t1_" + r["id"], (posts.get(r.get("link_id")) or {}).get("title") or "") for r in comments] + \
            [(p, (p.get("title") or "") + " " + (p.get("selftext") or ""), k, p.get("title") or "") for k, p in posts.items()]
    matches = []
    for r, text, fid, title in items:
        for c, rx, trx in pats:
            if rx.search(text) and (trx is None or trx.search(title)):
                corr = [x for x in replies.get(fid, []) if CORRECTION.search(x.get("body") or "")]
                matches.append({"claim_id": c["id"], "rating": c.get("rating", ""), "direction": c.get("direction", ""),
                                "item": fid, "author": r["author"], "account": name(r["author"]), "sub": r.get("subreddit"),
                                "created": int(float(r["created_utc"])), "score": r.get("score") or 0,
                                "corrected": int(bool(corr)), "first_correction": min((int(float(x["created_utc"])) for x in corr), default=""),
                                "text": " ".join(text.split())[:400]})
    st = {}
    if stances:
        for r in csv.DictReader(open(stances, encoding="utf-8")):
            st[(r["claim_id"], r["item"])] = r["stance"]
    reviewed = {k[0] for k in st}
    for x in matches:
        x["stance"] = st.get((x["claim_id"], x["item"]), "" if x["claim_id"] not in reviewed else "other")
    os.makedirs(out_dir, exist_ok=True)
    keys = ["claim_id", "rating", "direction", "item", "account", "sub", "created", "score", "corrected", "first_correction", "stance"]
    with open(os.path.join(out_dir, "matches.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys + ["author", "text"]); w.writeheader(); w.writerows(matches)
    rows = []
    for c in claims:
        allm = [x for x in matches if x["claim_id"] == c["id"]]
        m = [x for x in allm if x["stance"] in ("", "assert")]
        sc = sorted(x["score"] for x in m)
        extra = {k: c[k] for k in ("origin_pillar", "first_official", "forged") if k in c}
        rows.append({"id": c["id"], "claim": c["claim"], "rating": c.get("rating", ""), **extra, "reviewed": int(c["id"] in reviewed),
                     "disputes": sum(x["stance"] == "dispute" for x in allm), "items": len(m),
                     "accounts": len({x["author"] for x in m}), "subs": "; ".join(f"{s} {n}" for s, n in Counter(x["sub"] for x in m).most_common()),
                     "median_score": sc[len(sc) // 2] if sc else "", "max_score": sc[-1] if sc else "", "corrected_pct": round(100 * sum(x["corrected"] for x in m) / len(m), 1) if m else ""})
    with open(os.path.join(out_dir, "spread.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"{len(matches):,} matching items across {len(claims)} claims; see spread.csv")
    return os.path.join(out_dir, "spread.csv")


def _authenticity(items, hist_share=None):
    """AI-style writing is its own finding (lower authenticity), never proof of a bot. Share of the account's
    asserting items that read as AI-written (AI-tic words or em dashes), plus the history-wide share when known."""
    share = sum(bool(AI_RE_LOCAL.search(x.get("text") or "")) for x in items) / len(items) if items else 0
    best = hist_share if hist_share is not None else share
    level = "ai_style" if (hist_share is not None and hist_share >= 0.1) or (hist_share is None and len(items) >= 3 and share >= 0.34) \
        else ("some_ai_style" if best > 0 else "")
    return {"ai_style_share_in_claims": round(share, 2), "ai_style_share_history": "" if hist_share is None else round(hist_share, 3),
            "authenticity": level}


def accounts(matches_csv, out_dir="claims", bot_flags=None, keep_names=False):
    """Account pattern levels from matches.csv. bot_flags: a history.score or analyze.py accounts.csv to cross-check
    (matched on the same hashed or plain names). Writes accounts.csv (names dropped unless keep_names)."""
    m = list(csv.DictReader(open(matches_csv, encoding="utf-8")))
    by = defaultdict(list)
    for x in m:
        by[x["author"]].append(x)
    global AI_RE_LOCAL
    from .history import AI_RE as AI_RE_LOCAL
    flagged, ai_hist = {}, {}
    if bot_flags:
        for r in csv.DictReader(open(bot_flags, encoding="utf-8")):
            flagged[r["account"]] = r.get("flag_list") or r.get("tier") or ""
            if r.get("ai_vocab_share") not in (None, ""):
                ai_hist[r["account"]] = float(r["ai_vocab_share"])
    rows = []
    for a, xs in by.items():
        bad = [x for x in xs if x["rating"] in RATED_BAD and x.get("stance", "assert") in ("assert", "")]
        if not bad:
            continue
        distinct = {x["claim_id"] for x in bad}
        dirs = {x["direction"] for x in bad if x["direction"] and x["direction"] != "none"}
        repeat_after = False
        for cid in distinct:
            times = sorted((int(x["created"]), x) for x in bad if x["claim_id"] == cid)
            first_corr = min((int(x["first_correction"]) for _, x in times if x["first_correction"]), default=None)
            if first_corr is not None and any(t > first_corr for t, _ in times):
                repeat_after = True
        level = "repeat_spreader" if len(distinct) >= 3 or repeat_after else \
                "one_directional" if len(distinct) >= 2 and len(dirs) == 1 else "one_off"
        rows.append({"account": xs[0]["account"], **({"author": a} if keep_names else {}), "level": level,
                     "false_or_misleading_claims": len(distinct), "items": len(bad), "direction": "; ".join(sorted(dirs)),
                     "repeated_after_correction": int(repeat_after), "subs": "; ".join(sorted({x["sub"] for x in bad})),
                     "bot_flags": flagged.get(xs[0]["account"], flagged.get(a, "")),
                     **_authenticity(bad, ai_hist.get(xs[0]["account"], ai_hist.get(a)))})
    rows.sort(key=lambda r: ({"repeat_spreader": 0, "one_directional": 1, "one_off": 2}[r["level"]], -r["items"]))
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "accounts.csv"), "w", newline="", encoding="utf-8") as fh:
        if rows:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    lv = Counter(r["level"] for r in rows)
    print(f"accounts with a false or misleading claim: {len(rows)} | " + ", ".join(f"{k} {v}" for k, v in lv.most_common()))
    return os.path.join(out_dir, "accounts.csv")
