#!/usr/bin/env python3
"""Ukraine/Palestine framing asymmetry by community (candidate MOVE-11). Frozen with
docs/ukraine-palestine-asymmetry-predictions.md, Nov 16 2026: do not change the term lists or the metric after that
file is committed; changes go in a v2 with its own predictions.

The claim being tested (docs/antiwest-vod-analysis.md, T2): campists ask for "peace", "negotiations" and "diplomacy"
for Ukraine, and "liberation", "end the occupation" and "resistance" for Palestine.

  python -I scripts/asymmetry.py pull                 # comments mentioning either war, per sub, from Arctic Shift
  python -I scripts/asymmetry.py measure              # per-community counts, shares, asymmetry index, bootstrap CI
  python -I scripts/asymmetry.py sample               # blind-read items (sub hidden) + key, in the data folder
  python -I scripts/asymmetry.py score A.csv B.csv    # precision per coder and cell, agreement

Raw comments live in ~/socialscope_data/antiwest_asym/ and are never committed. Authors are dropped when the pull is
written; nothing here is computed or stored per account.
"""
import csv, glob, json, math, os, random, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

DATA = os.path.expanduser("~/socialscope_data/antiwest_asym")
REPO_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "antiwest", "asymmetry_by_sub.csv")
START, END = "2026-10-01", "2026-11-16"   # end exclusive
SUBS = ["TankieTheDeprogram", "Hasan_Piker", "dsa", "socialism", "Palestine", "Conservative", "Destiny",
        "neoliberal", "ukraine"]
SEARCH_TERMS = ["ukraine", "ukrainian", "russia", "putin", "zelensky", "kyiv",
                "gaza", "palestine", "palestinian", "israel", "west bank", "hamas"]

# ---- frozen term lists ----
UKR = re.compile(r"\b(ukrain\w*|kyiv|kiev|zelensk\w*|donbas+|donetsk|luhansk|crimea\w*|putin\w*|russia|russian|russians|kremlin)\b", re.I)
PAL = re.compile(r"\b(gaza\w*|palestin\w*|west\s+bank|israel\w*|idf|hamas|netanyahu|bibi)\b", re.I)
SETTLE = re.compile(r"\b(negotiat\w*|diplomac\w*|diplomatic\w*|cease-?\s?fires?|armistice|de-?escalat\w*|truce|"
                    r"compromis\w*|concessions?|stop\s+(sending|funding|arming)|end\s+the\s+war|stop\s+the\s+war|peace\w*)\b", re.I)
JUSTICE = re.compile(r"\b(liberat\w*|occup(ation|ations|ied|ier|iers|ying|y)|resist(ance|ing|s)?|self-?determination|"
                     r"decoloni\w*|free\s+(palestine|ukraine)|anti-?colonial\w*|colonial\w*|sovereign\w*|victory|"
                     r"win\s+the\s+war|intifada|armed\s+struggle|take\s+back)\b", re.I)
SENT = re.compile(r"(?<=[.!?])\s+|\n+")
BOTS = {"automoderator", "[deleted]"}
MIN_FRAMED = 30   # per war, per community, for an index to be reported


def frames(body):
    """-> dict with mention and frame flags per war. Quoted lines are dropped. Sentences naming both wars are skipped;
    a sentence naming neither inherits the war only when the comment names exactly one."""
    text = "\n".join(l for l in body.splitlines() if not l.lstrip().startswith(">"))
    mu, mp = bool(UKR.search(text)), bool(PAL.search(text))
    f = {"mu": mu, "mp": mp, "u_settle": False, "u_just": False, "p_settle": False, "p_just": False}
    if not (mu or mp):
        return f
    for s in SENT.split(text):
        su, sp = bool(UKR.search(s)), bool(PAL.search(s))
        if su and sp:
            continue
        war = "u" if su else "p" if sp else ("u" if mu and not mp else "p" if mp and not mu else None)
        if war is None:
            continue
        if SETTLE.search(s):
            f[war + "_settle"] = True
        if JUSTICE.search(s):
            f[war + "_just"] = True
    return f


def load():
    rows = {}
    for path in glob.glob(os.path.join(DATA, "comments_*.jsonl")):
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            if r["id"] in rows or len(r.get("body", "")) < 20 or r["body"] in ("[deleted]", "[removed]"):
                continue
            rows[r["id"]] = r
    return list(rows.values())


def pull(only=None):
    # Added Nov 16 2026: optional list of subs so each can run in its own process (one process per sub, never two
    # on the same sub: they would share the raw_ files). Does not change what is pulled.
    from socialscope import arctic
    os.makedirs(DATA, exist_ok=True)
    s, e = arctic.to_ts(START), arctic.to_ts(END)
    for sub in (only or SUBS):
        out = os.path.join(DATA, "comments_%s.jsonl" % sub)
        done = os.path.join(DATA, "done_%s.txt" % sub)
        finished = set(open(done).read().split("\n")) if os.path.exists(done) else set()
        for term in SEARCH_TERMS:
            if term in finished:
                continue
            raw = os.path.join(DATA, "raw_%s_%s.jsonl" % (sub, term.replace(" ", "_")))
            n = arctic._page_all("comments", {"subreddit": sub, "body": term}, s, e, raw, label="%s/%s" % (sub, term))
            with open(out, "a", encoding="utf-8") as w:   # authors dropped here
                for line in open(raw, encoding="utf-8"):
                    r = json.loads(line)
                    if str(r.get("author", "")).lower() in BOTS:
                        continue
                    w.write(json.dumps({"id": r["id"], "created_utc": r["created_utc"], "subreddit": sub,
                                        "body": r.get("body", "")}, ensure_ascii=False) + "\n")
            os.remove(raw)
            open(done, "a").write(term + "\n")
            print(sub, term, n, flush=True)


def index(c):
    """Asymmetry index from counts: ln((Pj+.5)/(Ps+.5)) - ln((Uj+.5)/(Us+.5)). Positive = Palestine framed toward
    justice/liberation, relative to Ukraine, more than toward settlement."""
    return math.log((c["p_just"] + .5) / (c["p_settle"] + .5)) - math.log((c["u_just"] + .5) / (c["u_settle"] + .5))


def counts(fl):
    keys = ["mu", "mp", "u_settle", "u_just", "p_settle", "p_just"]
    return {k: sum(f[k] for f in fl) for k in keys}


def measure():
    rows = load()
    by = {}
    for r in rows:
        by.setdefault(r["subreddit"], []).append(frames(r["body"]))
    rng = random.Random(20261116)
    out = []
    for sub in SUBS:
        fl = by.get(sub, [])
        c = counts(fl)
        ok = (c["u_settle"] + c["u_just"] >= MIN_FRAMED) and (c["p_settle"] + c["p_just"] >= MIN_FRAMED)
        boots = []
        if ok:
            for _ in range(1000):
                boots.append(index(counts([fl[rng.randrange(len(fl))] for _ in range(len(fl))])))
            boots.sort()
        row = dict(sub=sub, comments=len(fl), **c,
                   u_settle_share=round(c["u_settle"] / max(1, c["u_settle"] + c["u_just"]), 3),
                   p_just_share=round(c["p_just"] / max(1, c["p_settle"] + c["p_just"]), 3),
                   index=round(index(c), 3) if ok else "",
                   ci_lo=round(boots[25], 3) if ok else "", ci_hi=round(boots[974], 3) if ok else "",
                   enough=int(ok))
        out.append(row)
        print(row, flush=True)
    with open(REPO_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(out[0].keys())); w.writeheader(); w.writerows(out)
    print("wrote", REPO_OUT)


def sample(n_per_cell=60):
    """Blind items for the two halves of the move: Ukraine+settle and Palestine+justice. Stratified evenly over the
    communities, shuffled, sub hidden. Items file for coders; key file kept separately."""
    rng = random.Random(1116)
    rows = load()
    cells = {"u_settle": ("Ukraine", "settlement (peace, negotiation, ceasefire, diplomacy, compromise)"),
             "p_just": ("Israel-Palestine", "justice/liberation (liberation, occupation, resistance, self-determination, victory)")}
    items, key = [], []
    for cell, (war, frame) in cells.items():
        pools = {s: [r for r in rows if r["subreddit"] == s and frames(r["body"])[cell]] for s in SUBS}
        for p in pools.values():
            rng.shuffle(p)
        picked, i = [], 0
        while len(picked) < n_per_cell and any(pools.values()):
            s = SUBS[i % len(SUBS)]; i += 1
            if pools[s]:
                picked.append(pools[s].pop())
        for r in picked:
            items.append({"cell": cell, "war": war, "frame": frame, "text": r["body"][:1500], "rid": r["id"], "sub": r["subreddit"]})
    rng.shuffle(items)
    with open(os.path.join(DATA, "blind_items.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["item", "war", "frame", "text"])
        for k, it in enumerate(items):
            w.writerow([k, it["war"], it["frame"], it["text"]])
            key.append([k, it["cell"], it["sub"], it["rid"]])
    with open(os.path.join(DATA, "blind_key.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["item", "cell", "sub", "rid"]); w.writerows(key)
    print(len(items), "items ->", DATA)


def wilson(k, n, z=1.96):
    if not n:
        return (0, 0)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def score(paths):
    key = {r["item"]: r for r in csv.DictReader(open(os.path.join(DATA, "blind_key.csv"), encoding="utf-8"))}
    labs = [{r["item"]: r["label"].strip().lower() for r in csv.DictReader(open(p, encoding="utf-8"))} for p in paths]
    for p, lab in zip(paths, labs):
        for cell in ("u_settle", "p_just"):
            its = [i for i in key if key[i]["cell"] == cell and i in lab]
            k = sum(lab[i] == "endorse" for i in its)
            lo, hi = wilson(k, len(its))
            print("%s %s: %d/%d endorse = %.0f%% (%.0f-%.0f%%)" % (os.path.basename(p), cell, k, len(its),
                  100 * k / max(1, len(its)), 100 * lo, 100 * hi))
    if len(labs) == 2:
        common = [i for i in labs[0] if i in labs[1]]
        agree = sum(labs[0][i] == labs[1][i] for i in common)
        print("agreement %d/%d = %.0f%%" % (agree, len(common), 100 * agree / max(1, len(common))))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "pull" and len(sys.argv) > 2:
        pull(sys.argv[2:]); sys.exit()
    {"pull": pull, "measure": measure, "sample": sample}.get(cmd, lambda: score(sys.argv[2:]) if cmd == "score" else print(__doc__))()
