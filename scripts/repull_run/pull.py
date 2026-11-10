#!/usr/bin/env python3
"""Re-pull every cohort history with the same cap, ending at the account's anchor (scripts/repull_run/pull.py).

Why: arctic.pull_user_histories walks newest-first with max_items per kind and no end date, so a positive that kept
posting after its Bot Bouncer listing lost pre-listing items to the cap while controls (cut at their own last item)
kept all 1,000. Pulling with end = anchor gives every account the same cap on the same side of its anchor.

Anchors: positives and pending at listed_utc (from groups.py). Controls get a matched anchor drawn from the
positives' anchors on their side of the split (anchors.assign_control_anchors, seed fixed, at least a day after
the account's first item ever, taken from the old *_oldest.json files). The draw is written once to
<work>/anchors_private.csv and reused on every re-run, so a resumed pull never changes an anchor.

Batching: pull_user_histories takes one global end date (YYYY-MM-DD, Eastern, exclusive), so accounts are grouped
by their anchor's Eastern calendar day and pulled with end = the next day. That lets up to one day of post-anchor
items through; feats.py cuts at the exact anchor, so they never enter a feature, and they take at most a few of
the 1,000 slots. Batch zips are <pull_dir>/repull_<YYYYMMDD>_{posts,comments}.zip plus _oldest.json. The oldest
items are pre-seeded from the old pulls (two API calls per account saved); only unknown ones are fetched.

Resumable: pull_user_histories keeps per-user part files and .done markers under <pull_dir>/_parts; a finished
batch gets a .complete marker and is skipped. Re-run the same command after any interruption. --only test pulls the
test side first (test_pos, test_pending, test_ctl, train_pos); --only train the train controls; default all.
Progress: one overall "user histories: n/N users" line in the log, in the format status.py already parses.

Usage:
  python3 -I scripts/repull_run/pull.py --dry-run            # plan, batch count and time estimate, no network
  python3 -I scripts/repull_run/pull.py [--only test|train|all] [--max-items 1000] [--pause 0.8] [--retries 2]
Never prints a username (arctic's own per-user progress line is replaced).
"""
import argparse, collections, csv, hashlib, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
from socialscope import arctic  # noqa: E402
import anchors as A  # noqa: E402

TEST_SIDE = ("test_pos", "test_pending", "test_ctl", "train_pos")
SEC_PER_ACCOUNT = {"ctl": 19.0, "pos": 9.0}   # from the Nov 1-2 logs: insub 480 accts/2h22m = 17.8 s, fwd 2000/12h06m = 21.8 s (capped controls, with
                                                # oldest calls); train 2217/5h52m = 9.5 s (mostly short banned histories). Oldest calls are skipped here.


class OverallBar(arctic._TextBar):
    """Replaces arctic's per-batch bar: counts accounts across all batches and never shows a username."""
    offset = 0
    total_all = 0

    def __init__(self, total, initial=0, desc="", unit="it"):
        # `initial` is the batch's already-finished count; offset already counts every finished account overall
        super().__init__(OverallBar.total_all, OverallBar.offset, "user histories", "users")

    def set_postfix_str(self, t, refresh=True):
        t = t.split(":")[-1].strip() if t.startswith("u/") else t   # "u/<name> comments: 345" -> "345"
        super().set_postfix_str(t, refresh)


class Masked:
    """stdout wrapper: arctic prints "u/<name> posts failed" lines; the log must never hold a username."""
    import re as _re
    USER = _re.compile(r"/?u/[A-Za-z0-9_-]+")

    def __init__(self, raw):
        self.raw = raw

    def write(self, s):
        self.raw.write(self.USER.sub("u/<hidden>", s))

    def flush(self):
        self.raw.flush()


def overall_progress(total, initial=0, desc="", unit="it"):
    bar = OverallBar(total, initial, desc, unit)
    arctic._BAR = bar
    return bar


def plan_anchors(G, oldest):
    """Load or draw control anchors; returns {username: (anchor_ts, src)} for every account that gets one."""
    path = os.path.join(C.WORK, "anchors_private.csv")
    anchors = {}
    if os.path.exists(path):
        for r in csv.DictReader(open(path, encoding="utf-8")):
            anchors[r["username"]] = (float(r["anchor_utc"]), r["anchor_src"])
        missing = [u for u in G if u not in anchors]
        if missing:
            print(f"anchors file exists but lacks {len(missing)} cohort accounts; delete it to redraw (that changes every control anchor)", flush=True)
        return anchors
    for u, r in G.items():
        if r["anchor_utc"]:
            anchors[u] = (float(r["anchor_utc"]), "listing")
    first = {u: oldest.get(u) for u in G}
    last = {}
    ctl = [u for u, r in G.items() if r["group"].endswith("_ctl")]
    drawn = A.assign_control_anchors(G, first, last, seed=20261105)
    need_last = [u for u in ctl if u not in drawn]
    if need_last:   # controls younger than every positive anchor: fall back to their last item in the old pull
        hp = [os.path.join(C.HIST_DIR, f"{n}_{k}.zip") for n in C.OLD_HIST for k in ("posts", "comments")]
        for p in hp:
            if os.path.exists(p):
                for r in C.iter_jsonl(p):
                    a = r.get("author")
                    if a in need_last:
                        last[a] = max(last.get(a, 0), float(r["created_utc"]))
        drawn = A.assign_control_anchors(G, first, last, seed=20261105)
    anchors.update(drawn)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["username", "group", "anchor_utc", "anchor_src", "anchor_day", "batch"])
        for u in sorted(anchors):
            ts, src = anchors[u]
            day = C.et_day(ts)
            w.writerow([u, G[u]["group"], round(ts), src, day, "repull_" + day.replace("-", "")])
    print(f"wrote {path}: " + ", ".join(f"{k} {v}" for k, v in sorted(collections.Counter(s for _, s in anchors.values()).items())), flush=True)
    return anchors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["test", "train", "all"], default="all")
    ap.add_argument("--max-items", type=int, default=1000)
    ap.add_argument("--pause", type=float, default=0.8)
    ap.add_argument("--retries", type=int, default=2, help="extra passes over batches with unfinished accounts")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--groups", default=None)
    a = ap.parse_args()
    C.ensure_dirs()
    os.makedirs(C.PULL_DIR, exist_ok=True)
    G = {r["username"]: r for r in C.read_groups(a.groups)}
    oldest = C.load_oldest([os.path.join(C.HIST_DIR, f"{n}_oldest.json") for n in C.OLD_HIST])
    anchors = plan_anchors(G, oldest)
    sel = {u for u in G if a.only == "all" or (a.only == "test") == (G[u]["group"] in TEST_SIDE)}
    users = sorted(u for u in sel if u in anchors)
    skipped = len(sel) - len(users)
    batches = collections.defaultdict(list)
    # Fixed Nov 6 2026 (laptop session): batches were named repull_<day> on both sides, so --only train reused the
    # test side's names for the same anchor days and its zips (train controls only) replaced the test zips
    # (410 test-side accounts lost in feats). Test-side batches are now repull_test_<day>; train keeps repull_<day>.
    # The day is read from the last 8 characters of the name.
    for u in users:
        side = "test_" if G[u]["group"] in TEST_SIDE else ""
        batches["repull_" + side + C.et_day(anchors[u][0]).replace("-", "")].append(u)
    npos = sum(1 for u in users if not G[u]["group"].endswith("_ctl"))
    est = (npos * SEC_PER_ACCOUNT["pos"] + (len(users) - npos) * SEC_PER_ACCOUNT["ctl"]) / 3600
    print(f"{len(users)} accounts in {len(batches)} anchor-day batches ({a.only}); {skipped} without an anchor skipped; "
          f"groups: " + ", ".join(f"{k} {v}" for k, v in sorted(collections.Counter(G[u]['group'] for u in users).items()))
          + f"; estimated {est:.1f} h at {SEC_PER_ACCOUNT['ctl']:.0f} s per control and {SEC_PER_ACCOUNT['pos']:.0f} s per positive", flush=True)
    sizes = sorted(len(v) for v in batches.values())
    print(f"batch sizes: median {sizes[len(sizes) // 2]}, largest {sizes[-1]}, smallest {sizes[0]}; days {min(b[-8:] for b in batches)}..{max(b[-8:] for b in batches)}", flush=True)
    if a.dry_run:
        return
    arctic._progress = overall_progress
    OverallBar.total_all = len(users)
    parts = os.path.join(C.PULL_DIR, "_parts")
    done_user = lambda u: all(os.path.exists(os.path.join(parts, f"{u}_{k}.jsonl.done")) for k in ("posts", "comments"))
    for attempt in range(1 + a.retries):
        pending_batches = []
        for name in sorted(batches):
            us = batches[name]
            sig = hashlib.sha256("\n".join(us).encode()).hexdigest()[:12]
            marker = os.path.join(C.PULL_DIR, f"{name}.complete")
            if os.path.exists(marker) and open(marker).read().strip() == sig:
                continue
            pending_batches.append((name, us, sig, marker))
        OverallBar.offset = sum(done_user(u) for u in users)
        if not pending_batches:
            break
        if attempt:
            print(f"retry pass {attempt}: {len(pending_batches)} batches still have unfinished accounts", flush=True)
        for name, us, sig, marker in pending_batches:
            day = name[-8:]
            end = C.next_day(f"{day[:4]}-{day[4:6]}-{day[6:]}")
            seed_path = os.path.join(C.PULL_DIR, f"{name}_oldest.json")
            known = {u: oldest[u] for u in us if oldest.get(u) is not None}
            if os.path.exists(seed_path):
                known.update({k: v for k, v in json.load(open(seed_path)).items() if v is not None})
            json.dump(known, open(seed_path, "w"))
            t0 = time.time()
            print(f"batch {name}: {len(us)} accounts, end {end} (exclusive), {len(us) - len(known)} oldest to fetch", flush=True)
            raw = sys.stdout
            sys.stdout = Masked(raw)
            try:
                arctic.pull_user_histories(us, end=end, max_items=a.max_items, out_dir=C.PULL_DIR, pause=a.pause, name=name, oldest=True)
            except Exception as e:   # keep the queue moving; the retry pass picks the batch up again
                print(f"batch {name}: stopped ({type(e).__name__}: {Masked.USER.sub('u/<hidden>', str(e))[:120]}); will retry", flush=True)
                continue
            finally:
                sys.stdout = raw
            unfinished = [u for u in us if not done_user(u)]
            print(f"batch {name}: done in {(time.time() - t0) / 60:.1f} min, {len(unfinished)} accounts unfinished", flush=True)
            if not unfinished:
                open(marker, "w").write(sig + "\n")
            OverallBar.offset = sum(done_user(u) for u in users)
    left = [u for u in users if not done_user(u)]
    print(f"repull {a.only}: {len(users) - len(left)}/{len(users)} accounts finished, {len(left)} unfinished"
          + ("" if not left else " (re-run the same command to resume)"), flush=True)
    sys.exit(1 if left else 0)


if __name__ == "__main__":
    main()
