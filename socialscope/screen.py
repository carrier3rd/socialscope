"""Stage 1: shortlist suspicious accounts from subreddit dumps, plus a random control group and known bots.

    from socialscope import screen
    screen.shortlist(["pulls/2026-10-06_to_2026-10-12/*.zip"], out_dir="shortlist",
                     known_bots="r_botbouncer_posts.zip", known_before="2026-10-06")

A shortlist is a net, not a verdict: most accounts on it are people. The control group (random accounts
that tripped nothing) is what makes stage 2 meaningful, so keep it the same size as the shortlist.

Outputs (usernames: keep private)
  users_to_pull.txt   every username in all three groups, one per line, for pull_user_histories
  groups.csv          username, group (shortlist / control / known_bot), reasons
  summary.md          counts only, safe to share
"""
import csv, glob, hashlib, os, random, re, sys
from collections import Counter, defaultdict

from . import signals

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "scripts"))
from reddit_io import load_reddit  # noqa: E402


def _expand(paths):
    out = []
    for p in ([paths] if isinstance(paths, str) else paths):
        out += sorted(glob.glob(p)) or [p]
    return out


def _known(known_bots, known_before):
    if not known_bots:
        return set()
    from importlib import util
    spec = util.spec_from_file_location("analyze", os.path.join(_HERE, "..", "scripts", "analyze.py"))
    mod = util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.load_known_bots(_expand(known_bots), known_before)


# How strongly each rule pointed to Bot Bouncer bots on Oct 6-12, 2026 (lift over ordinary accounts).
# When more accounts are flagged than max_shortlist, the strongest-scoring accounts are kept first.
# ai_style and ai_lite were tuned on that same week, so treat their lift as optimistic until re-tested.
PRIORITY = {"ai_style": 12, "new": 11, "ai_lite": 6, "detector": 3, "downvoted": 1}


def shortlist(inputs, out_dir="shortlist", new_pct=3.0, ai_style=True, ai_threshold=3, ai_lite=True,
              downvoted_min=2, downvoted_share=0.5, detector_dir=None, max_shortlist=300,
              controls="match", known_bots=None, known_before=None, skip_authors=("LSFSecondaryMirror",),
              seed=7):
    """Build the three groups for stage 2.

    Rules (any one puts an account on the shortlist):
      new        account among the newest new_pct% of accounts in the data (by Reddit account ID)
      ai_style   at least one comment scoring ai_threshold+ on the AI-quip template (signals.ai_style_score)
      ai_lite    Reddit-default username (Word_Word1234) and a comment scoring 2+ on the template
      downvoted  downvoted_min+ comments and downvoted_share+ of them below zero
      detector   any tier in an analyze.py run (pass its folder as detector_dir; needs its .salt)
    controls: "match" = same size as the shortlist, an int = that many, 0 = none.
    """
    rows = load_reddit(_expand(inputs), list(skip_authors))
    by = defaultdict(list)
    for r in rows:
        by[r["author"]].append(r)
    reasons = defaultdict(list)

    ids = {}
    for a, items in by.items():
        for r in items:
            v = signals.account_id_number(r.get("author_id"))
            if v:
                ids[a] = v
                break
    if ids and new_pct:
        cut = sorted(ids.values())[int(len(ids) * (1 - new_pct / 100))]
        for a, v in ids.items():
            if v >= cut:
                reasons[a].append("new")
    for a, items in by.items():
        comments = [r for r in items if not r["is_post"] and not r["removed"]]
        if ai_style and any(signals.is_ai_style(r["body"], ai_threshold) for r in comments):
            reasons[a].append("ai_style")
        elif ai_lite and signals.DEFAULT_NAME.match(a) and any(
                8 <= len(r["body"].split()) <= 70 and "?" not in r["body"] and signals.ai_style_score(r["body"]) >= 2
                for r in comments):
            reasons[a].append("ai_lite")
        if len(comments) >= downvoted_min and sum(r["score"] < 0 for r in comments) / len(comments) >= downvoted_share:
            reasons[a].append("downvoted")
    if detector_dir:
        salt = open(os.path.join(detector_dir, ".salt")).read().strip()
        h = lambda u: "acct_" + hashlib.sha256((salt + u).encode()).hexdigest()[:10]
        tiers = {r["account"]: r["tier"] for r in csv.DictReader(open(os.path.join(detector_dir, "accounts.csv"), encoding="utf-8"))}
        for a in by:
            if tiers.get(h(a)) or tiers.get(a):
                reasons[a].append("detector")

    known = _known(known_bots, known_before)
    known_active = sorted(a for a in by if a.lower() in known)
    rnd = random.Random(seed)
    flagged = sorted(a for a in reasons if a not in known_active)
    total_flagged = len(flagged)
    if max_shortlist and len(flagged) > max_shortlist:
        rnd.shuffle(flagged)  # random order within equal priority
        flagged.sort(key=lambda a: -sum(PRIORITY.get(x, 1) for x in reasons[a]))
        flagged = sorted(flagged[:max_shortlist])
    pool = sorted(a for a in by if a not in reasons and a not in known_active)
    n_ctrl = len(flagged) if controls == "match" else int(controls)
    ctrl = sorted(rnd.sample(pool, min(n_ctrl, len(pool))))

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "groups.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["username", "group", "reasons"])
        for a in flagged:
            w.writerow([a, "shortlist", "+".join(reasons[a])])
        for a in ctrl:
            w.writerow([a, "control", ""])
        for a in known_active:
            w.writerow([a, "known_bot", "+".join(reasons.get(a, []))])
    with open(os.path.join(out_dir, "users_to_pull.txt"), "w") as fh:
        fh.write("\n".join(flagged + ctrl + known_active) + "\n")
    rc = Counter(x for a in flagged for x in reasons[a])
    kc = Counter(x for a in known_active for x in reasons.get(a, []))
    md = ["# Shortlist summary", "",
          f"Accounts in data: {len(by):,}. Flagged by any rule: {total_flagged:,}"
          + (f" (kept the {len(flagged)} with the strongest signals)" if total_flagged > len(flagged) else "") + ".",
          f"Groups to pull: shortlist {len(flagged)}, control {len(ctrl)}, known bots {len(known_active)}.", "",
          "| Rule | Shortlisted accounts | Known bots it also caught |", "|---|---|---|"]
    md += [f"| {k} | {rc.get(k, 0)} | {kc.get(k, 0)} of {len(known_active)} |" for k in ("new", "ai_style", "ai_lite", "downvoted", "detector")]
    md += ["", "Usernames are in groups.csv and users_to_pull.txt: keep those private."]
    open(os.path.join(out_dir, "summary.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md))
    return os.path.join(out_dir, "users_to_pull.txt")
