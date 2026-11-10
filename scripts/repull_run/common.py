"""Shared paths, hashing and loaders for scripts/repull_run (written Nov 5, 2026).

Why this folder exists: scripts/insub_run pulled every history newest-first with a 1,000-per-kind cap and no end
date, then cut positives at their Bot Bouncer listing date. A positive that kept posting after its listing lost
pre-listing items to the cap while controls sat at the cap, so item counts, history age and every count-coupled
feature carried a class artifact. These scripts rebuild the cohorts, re-pull every history with the same cap ending
at the anchor, assign controls matched anchors, and score with thresholds from training data and bootstrap CIs.

Environment overrides (so the same scripts dry-run elsewhere):
  SOCIALSCOPE_REPO   repo root (default ~/socialscope)
  SOCIALSCOPE_DATA   data root (default ~/socialscope_data)
  SOCIALSCOPE_SALT   hashing salt (default: read <repo>/.socialscope_salt). Never print it.
  SOCIALSCOPE_REPULL     where work/ and out/ go (default <data>/repull)
  SOCIALSCOPE_PULL_DIR   where the re-pulled zips go (default <data>/reddit_pulls/repull)
Every file holding usernames stays under <data>/repull/work/; everything under <data>/repull/out/ is hashed.
"""
import csv, glob, hashlib, json, os, re, sys, zipfile
from datetime import datetime, timedelta, timezone

REPO = os.path.expanduser(os.environ.get("SOCIALSCOPE_REPO", "~/socialscope"))
DATA = os.path.expanduser(os.environ.get("SOCIALSCOPE_DATA", "~/socialscope_data"))
REPULL = os.path.expanduser(os.environ.get("SOCIALSCOPE_REPULL", os.path.join(DATA, "repull")))
WORK = os.path.join(REPULL, "work")       # private: usernames
OUT = os.path.join(REPULL, "out")         # hashed only
PULL_DIR = os.path.expanduser(os.environ.get("SOCIALSCOPE_PULL_DIR", os.path.join(DATA, "reddit_pulls", "repull")))
HIST_DIR = os.path.join(DATA, "reddit_pulls", "histories")
if REPO not in sys.path:
    sys.path.insert(0, REPO)

# The 18 subreddits of the study (scripts/train_run/insub.py).
SUBS = {s.lower() for s in ("Asmongold Conservative Destiny Hasan_Piker IsraelPalestine LeftoversH3 LivestreamFail "
                            "Palestine PoliticalCompassMemes TankieTheDeprogram atrioc dsa h3h3productions neoliberal "
                            "samharris thebulwark thedavidpakmanshow ukraine").split()}

# Cohort source lists on the laptop (usernames; never copied anywhere else).
LISTS = {
    "insub": os.path.join(DATA, "users_to_pull_insub.txt"),
    "train": os.path.join(DATA, "train", "users_to_pull_train.txt"),
    "augpanel": os.path.join(DATA, "augpanel", "users_to_pull_augpanel.txt"),
    "septest": os.path.join(DATA, "septest", "users_to_pull_septest.txt"),
    "round4": os.path.join(DATA, "round4", "users_to_pull_round4.txt"),
}
# Old (capped, no end date) history pulls that scripts/insub_run used, plus their oldest-item files.
OLD_HIST = ["insub", "train", "augpanel", "septest", "round4"]
# Bot Bouncer listing pulls (posts of r/BotBouncer). The glob also picks up the Oct 20-27 gap pull once it exists.
BB_GLOB = os.path.join(DATA, "reddit_pulls", "bb_*", "*", "r_BotBouncer_posts_*.zip")

# Documented counts from docs/insub-training-predictions.md (Results, Nov 2 2026), accounts with history.
DOCUMENTED = {"test_pos": 186, "test_ctl": 483, "test_pending": 259, "train_pos": 114, "train_ctl": 2216}

KEEP = ("id", "created_utc", "subreddit", "body", "title", "selftext", "score", "link_id", "parent_id", "url",
        "author_fullname", "distinguished")
REMOVED = ("[removed]", "[deleted]")


def salt():
    s = os.environ.get("SOCIALSCOPE_SALT")
    if not s:
        s = open(os.path.join(REPO, ".socialscope_salt")).read().strip()
    return s


_SALT = None


def H(name):
    """Hashed account id, identical to scripts/insub_run and history.score: 'acct_' + sha256(salt+name)[:10]."""
    global _SALT
    if _SALT is None:
        _SALT = salt()
    return "acct_" + hashlib.sha256((_SALT + name).encode()).hexdigest()[:10]


def hash_parity(name):
    """1 = test half, 0 = train half (build.py: int(H(u)[-1], 16) % 2)."""
    return int(H(name)[-1], 16) % 2


def read_names(path):
    return [re.sub(r"^/?u/", "", l.strip()) for l in open(path, encoding="utf-8") if l.strip() and not l.startswith("#")]


def iter_jsonl(path):
    """Records from a .zip (every member) or .jsonl; skips half-written lines like history._iter does."""
    if path.endswith(".zip"):
        z = zipfile.ZipFile(path)
        for n in z.namelist():
            with z.open(n) as fh:
                for line in fh:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
    else:
        with open(path, "rb") as fh:
            for line in fh:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def slim(r):
    d = {k: r[k] for k in KEEP if k in r}
    for k in ("body", "selftext"):
        if d.get(k):
            d[k] = d[k][:1500]
    d["author"] = r.get("author")
    return d


def load_histories(paths, wanted):
    """{author: {id: slim item}} for authors in `wanted`, across posts/comments files. Dedupes by item id."""
    items = {}
    for p in paths:
        for r in iter_jsonl(p):
            a = r.get("author")
            if a in wanted:
                items.setdefault(a, {})[r.get("id")] = slim(r)
    return items


def load_oldest(paths):
    old = {}
    for p in paths:
        if os.path.exists(p):
            for k, v in json.load(open(p)).items():
                if v is not None:
                    old.setdefault(k, v)
                else:
                    old.setdefault(k, None)
    return old


def et_day(ts):
    """Calendar day (YYYY-MM-DD) of a UTC timestamp in US Eastern time, using arctic's DST rule."""
    from socialscope import arctic
    d = datetime.fromtimestamp(ts, timezone.utc)
    return d.astimezone(timezone(arctic._et_offset(d))).strftime("%Y-%m-%d")


def next_day(day):
    return (datetime.fromisoformat(day) + timedelta(days=1)).date().isoformat()


def read_groups(path=None):
    path = path or os.path.join(WORK, "groups_private.csv")
    return list(csv.DictReader(open(path, encoding="utf-8")))


def wilson(k, n, z=1.96):
    import math
    if n == 0:
        return "n=0"
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return f"{100 * p:.0f}% ({100 * (c - h):.0f}-{100 * (c + h):.0f}), {k}/{n}"


def ensure_dirs():
    for d in (WORK, OUT):
        os.makedirs(d, exist_ok=True)
