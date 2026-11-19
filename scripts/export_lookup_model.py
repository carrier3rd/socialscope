#!/usr/bin/env python3
"""Export the frozen v7.1 full model as plain trees for the lookup (written Nov 13, 2026).

Reads repull/out/model_repull.pkl and features_repull.pkl, writes site/public/lookup/model.json. The JSON holds tree
splits, the flag lines, and the sorted scores of the 478 test controls (numbers only, no ids, used for the "higher
than N% of ordinary accounts" line). Before writing, it checks socialscope.lookup_core.predict against sklearn's
predict_proba on every account in features_repull.pkl and stops if any score differs by more than 1e-12.

Run with the scoring venv: ~/socialscope_data/scoreenv/bin/python -I scripts/export_lookup_model.py
"""
import csv, json, os, pickle, sys

REPO = os.path.expanduser("~/socialscope")
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts", "repull_run"))
import common as C  # noqa: E402
import score as SC  # noqa: E402
from socialscope import lookup_core as LC  # noqa: E402

OUT = os.path.join(REPO, "site", "public", "lookup", "model.json")


def main():
    P = pickle.load(open(os.path.join(C.OUT, "model_repull.pkl"), "rb"))
    m = P["model"]
    assert m.n_trees_per_iteration_ == 1
    trees = []
    for (pred,) in m._predictors:
        t = []
        for n in pred.nodes:
            t.append([int(n["feature_idx"]), float(n["num_threshold"]), int(n["missing_go_to_left"]), int(n["left"]),
                      int(n["right"]), float(n["value"]), int(n["is_leaf"])])
            assert not n["is_categorical"]
        trees.append(t)
    ctl = sorted(float(r["score_full"]) for r in csv.DictReader(open(os.path.join(C.OUT, "accounts_repull.csv"), encoding="utf-8"))
                 if r["group"] == "test_ctl" and r["score_full"] not in ("", None))
    M = dict(tag="repull (v7.1 full model, scored 2026-11-09)", baseline=float(m._baseline_prediction.ravel()[0]),
             num=P["num"], pwk=P["pwk"], names=P["names"], ok=[int(j) for j in P["ok"]], trees=trees,
             thresholds={"1%": float(P["threshold_1pct"]), "2%": float(P["threshold_2pct"]), "5%": float(P["threshold_5pct"])},
             control_scores=ctl)
    M = json.loads(json.dumps(M))     # check the round-tripped copy, which is what the browser gets

    D = pickle.load(open(os.path.join(C.OUT, "features_repull.pkl"), "rb"))
    rows = [r for r in D["rows"] if r["n_cut"] > 0]
    names, X = SC.matrix(rows, D["num"], D["pwk"])
    assert names == M["names"]
    sk = m.predict_proba(X[:, P["ok"]])[:, 1]
    worst = 0.0
    for r, s in zip(rows, sk):
        worst = max(worst, abs(LC.predict(M, LC.feature_vector(r, M)) - float(s)))
    print(f"parity: {len(rows)} accounts, largest difference from sklearn {worst:.2e}")
    if worst > 1e-12:
        sys.exit("exported trees disagree with sklearn; model.json not written")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(M, fh, separators=(",", ":"))
    print(f"wrote {OUT} ({os.path.getsize(OUT) / 1e6:.2f} MB, {len(trees)} trees, {len(ctl)} control scores)")


if __name__ == "__main__":
    main()
