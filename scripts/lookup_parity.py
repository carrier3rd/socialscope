#!/usr/bin/env python3
"""Check socialscope.lookup_core against the re-pull pipeline (written Nov 13, 2026).

For a random sample of re-pull accounts, rebuilds each feature row from the same cut history the pipeline used
(repull/work/repull/cut_*.jsonl and oldest_all.json) with lookup_core.features, scores it with the exported trees,
and compares every model feature and the score with features_repull.pkl / accounts_repull.csv. Counts only; never
prints a username.

Known difference: history.score's batch_id rule compares account-ID numbers across the accounts scored together.
A single-account lookup has no batch, so batch_id never fires there, which can move bot_score and the score.

Usage: ~/socialscope_data/scoreenv/bin/python -I scripts/lookup_parity.py [--n 400] [--seed 1]
"""
import argparse, collections, csv, glob, json, math, os, pickle, random, sys

REPO = os.path.expanduser("~/socialscope")
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts", "repull_run"))
import common as C  # noqa: E402
from socialscope import lookup_core as LC  # noqa: E402


def same(a, b):
    a, b = LC._fl(a), LC._fl(b)
    return (math.isnan(a) and math.isnan(b)) or abs(a - b) <= 1e-9 * max(1, abs(a), abs(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    M = json.load(open(os.path.join(REPO, "site", "public", "lookup", "model.json")))
    W = os.path.join(C.WORK, "repull")
    D = pickle.load(open(os.path.join(C.OUT, "features_repull.pkl"), "rb"))
    ref = {r["account"]: r for r in D["rows"] if r["n_cut"] > 0}
    sc = {r["account"]: float(r["score_full"]) for r in csv.DictReader(open(os.path.join(C.OUT, "accounts_repull.csv"), encoding="utf-8"))}
    oldest = json.load(open(os.path.join(W, "oldest_all.json")))
    users = []
    for g in sorted(glob.glob(os.path.join(W, "groups_*.csv"))):
        users += [r["username"] for r in csv.DictReader(open(g, encoding="utf-8"))]
    random.Random(a.seed).shuffle(users)
    want = {u for u in users if C.H(u) in ref}
    want = set(list(want)[:a.n]) if a.n else want
    items = collections.defaultdict(list)
    for p in sorted(glob.glob(os.path.join(W, "cut_*.jsonl"))):
        for r in C.iter_jsonl(p):
            if r.get("author") in want:
                items[r["author"]].append(r)
    cols = [M["names"][j] for j in M["ok"]]
    bad_feat, worst, n, off, batch = collections.Counter(), 0.0, 0, 0, 0
    for u in sorted(want):
        h = C.H(u)
        row = LC.features(u, items[u], oldest.get(u), anchor=ref[h]["anchor_utc"])
        x = LC.feature_vector(row, M)
        xr = LC.feature_vector(ref[h], M)
        diff = [c for c, v1, v2 in zip(cols, x, xr) if not same(v1, v2)]
        b = "batch_id" in (ref[h].get("flag_list") or "")
        batch += b
        for c in diff:
            bad_feat[c + (" (batch_id account)" if b else "")] += 1
        d = abs(LC.predict(M, x) - sc[h])
        worst = max(worst, d) if not b else worst
        off += d > 1e-9
        n += 1
    print(f"accounts checked: {n}; with batch_id in the study: {batch}")
    print(f"accounts whose lookup score differs from the pipeline: {off}; largest difference among non-batch accounts: {worst:.2e}")
    print("features that differed (count of accounts):", dict(bad_feat) or "none")


if __name__ == "__main__":
    main()
