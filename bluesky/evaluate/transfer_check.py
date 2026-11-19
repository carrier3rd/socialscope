#!/usr/bin/env python3
"""Phase 1 plumbing check for the frozen v7.1 transfer (reading (a)). Written Nov 19 2026 (laptop session).

Pilot days are development data and nothing from them is scored (docs/bluesky-politics-predictions.md). So this
runs the whole path (Bluesky history -> Reddit-shaped items -> frozen v7.1 features -> mask -> model) and reports
only whether it works: accounts processed, errors, and for each model input how many accounts got a value. Each
score is checked to be a number in [0, 1] and then thrown away: no score, distribution or label comparison is
printed or saved.

  --perturb N   also rerun the features for N accounts with random subreddits and random scores, and list every
                model input that moves. Those are the inputs shared.MASKED must blank.

Output: counts only (no DID, handle or text), to stdout and <data>/processed/transfer_check.json.
"""
import argparse, collections, contextlib, glob, gzip, hashlib, io, json, math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "bluesky"))
from socialscope import history, lookup_core as LC, signals  # noqa: E402
from features import shared  # noqa: E402

DATA = os.path.expanduser("~/socialscope_data/bluesky")


def hid(did):
    return "acct_" + hashlib.sha256(did.encode()).hexdigest()[:10]


def plc_oldest(did):
    p = glob.glob(os.path.join(DATA, "raw", "plc", "*", did.replace(":", "_") + ".json"))
    if not p:
        return None
    try:
        ops = json.load(open(p[0]))
    except ValueError:
        return None
    ts = [shared._ts(o.get("createdAt")) for o in ops if isinstance(o, dict)]
    ts = [t for t in ts if t]
    return min(ts) if ts else None


def model_inputs(M):
    names = list(M["num"]) + ["hist_age", "true_age", "sh", "sb", "primary", "log_items"] + \
        ["pw_" + k for k in M["pwk"] if k != "removed_share"]
    return [names[j] for j in M["ok"]]


def row_for(user, items, oldest, anchor):
    with contextlib.redirect_stdout(io.StringIO()):
        return LC.features(user, items, oldest, anchor=anchor)


def isnum(v):
    try:
        return not math.isnan(float(v))
    except (TypeError, ValueError):
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--perturb", type=int, default=0)
    a = ap.parse_args()
    M = json.load(open(os.path.join(REPO, "site", "public", "lookup", "model.json")))
    names = model_inputs(M)
    files = sorted(glob.glob(os.path.join(DATA, "raw", "histories", "*", "*.jsonl.gz")))
    if a.limit:
        files = files[:a.limit]
    n = collections.Counter()
    filled = collections.Counter()
    moved = {"subreddit": set(), "score": set()}
    errors = collections.Counter()
    rng = random.Random(20261119)
    for i, f in enumerate(files):
        did = os.path.basename(f)[:-len(".jsonl.gz")].replace("_", ":", 2)
        done = f[:-len(".jsonl.gz")] + ".done.json"
        try:
            meta = json.load(open(done))
            recs = [json.loads(l) for l in gzip.open(f, "rt", encoding="utf-8")]
        except (OSError, ValueError) as e:
            errors["read: " + type(e).__name__] += 1
            continue
        if meta.get("gone") or not recs:
            n["skipped_empty_or_gone"] += 1
            continue
        user = hid(did)
        items, bad_time = shared.to_items(recs, user)
        anchor = meta["anchor_us"] / 1e6
        n["records"] += len(recs)
        n["records_no_time"] += bad_time
        n["created_after_anchor"] += sum(x["created_utc"] > anchor for x in items)
        n["created_before_launch"] += sum(x["created_utc"] < shared.BSKY_LAUNCH for x in items)
        items = [x for x in items if shared.BSKY_LAUNCH <= x["created_utc"] <= anchor]
        if not items:
            n["skipped_no_usable_items"] += 1
            continue
        oldest = plc_oldest(did)
        n["with_plc_age"] += oldest is not None
        try:
            row = row_for(user, items, oldest, anchor)
        except Exception as e:  # report and go on: this is what the check is for
            errors["features: " + type(e).__name__ + ": " + str(e)[:80]] += 1
            continue
        if i < a.perturb:
            # Real names from the frozen code's own lists, so rules keyed to political, karma-farm or NSFW subs
            # can fire (random names alone would never touch them), plus ordinary random names.
            subs = sorted(history.POLSUB) + sorted(signals.FARM_SUBS)[:25] + ["gonewild", "nsfw_r4r", "onlyfans101"] + \
                [f"s{k}" for k in range(40)]
            for kind in ("subreddit", "score"):
                alt = [dict(x) for x in items]
                for x in alt:
                    if kind == "subreddit":
                        x["subreddit"] = rng.choice(subs)
                    else:
                        x["score"] = rng.randint(-5, 400)
                r2 = row_for(user, alt, oldest, anchor)
                for c in names:
                    v1, v2 = row.get(c), r2.get(c)
                    if c == "log_items":
                        continue
                    if str(v1) != str(v2):
                        moved[kind].add(c)
            n["perturbed"] += 1
        shared.mask(row)
        try:
            x = LC.feature_vector(row, M)
            p = LC.predict(M, x)
        except Exception as e:
            errors["model: " + type(e).__name__ + ": " + str(e)[:80]] += 1
            continue
        if isinstance(p, float) and 0.0 <= p <= 1.0:
            n["scored_valid"] += 1
        else:
            n["scored_invalid"] += 1
        del p  # never printed, never saved
        for c, v in zip(names, x):
            filled[c] += isnum(v)
        n["accounts"] += 1
    out = {"history_files": len(files), **dict(n), "errors": dict(errors),
           "model_inputs": len(names),
           "inputs_filled_accounts": {c: filled[c] for c in names},
           "inputs_never_filled": [c for c in names if filled[c] == 0],
           "masked_now": list(shared.MASKED)}
    if a.perturb:
        out["moved_by_subreddit"] = sorted(moved["subreddit"])
        out["moved_by_score"] = sorted(moved["score"] - moved["subreddit"])
    os.makedirs(os.path.join(DATA, "processed"), exist_ok=True)
    json.dump(out, open(os.path.join(DATA, "processed", "transfer_check.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
