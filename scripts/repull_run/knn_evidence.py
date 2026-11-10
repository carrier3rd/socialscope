#!/usr/bin/env python3
"""Nearest confirmed-ban neighbours for flagged accounts, and a calibration check (scripts/repull_run/knn_evidence.py).

For every account the full model flags at the 1% threshold on the test or pending side, list its 5 nearest
training positives (Bot Bouncer bans) in standardized feature space (median imputation and scaling fit on the
training side only), with Euclidean distances, and the share of its k nearest training accounts (bans and
controls together) that are bans. That share is evidence a reader can inspect: "this account sits among known
bans" rather than "the model says 0.93". The training side is about 4-5% bans, so a share of 0.5 is ten times the
base rate; the report prints the base rate next to each number.

Calibration: on the test side (where labels are known and the model never trained), does the neighbour ban share
track the actual ban rate? Accounts are binned by share and the observed ban rate per bin is printed, with the
test prevalence (positives / (positives + controls)) as the reference, plus the AUC of the share as a score.

Usage: python3 -I scripts/repull_run/knn_evidence.py --tag old_last [--k 10]
Reads <out>/accounts_<tag>.csv and model_<tag>.pkl; writes <out>/knn_<tag>.csv and knn_<tag>.md. Hashed ids only.
"""
import argparse, collections, csv, math, os, pickle, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
from sklearn.impute import SimpleImputer  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402
from sklearn.neighbors import NearestNeighbors  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--k", type=int, default=10, help="neighbourhood size for the ban share")
    ap.add_argument("--all-test", action="store_true", help="list neighbours for every test account, not only flagged ones")
    a = ap.parse_args()
    M = pickle.load(open(os.path.join(C.OUT, f"model_{a.tag}.pkl"), "rb"))
    rows = list(csv.DictReader(open(os.path.join(C.OUT, f"accounts_{a.tag}.csv"), encoding="utf-8")))
    names, ok = M["names"], M["ok"]
    cols = [names[j] for j in ok]

    def val(r, c):
        if c == "log_items":
            return math.log1p(float(r["n_cut"]))
        v = r.get(c, "")
        return float(v) if v not in ("", None) else np.nan
    X = np.array([[val(r, c) for c in cols] for r in rows], dtype=float)
    g = np.array([r["group"] for r in rows])
    acc = np.array([r["account"] for r in rows])
    score = np.array([float(r["score_full"]) for r in rows])
    tr = np.isin(g, ["train_pos", "train_ctl"])
    trpos = g == "train_pos"
    imp = SimpleImputer(strategy="median").fit(X[tr])
    sc = StandardScaler().fit(imp.transform(X[tr]))
    Z = sc.transform(imp.transform(X))
    nn_pos = NearestNeighbors(n_neighbors=5).fit(Z[trpos])
    nn_all = NearestNeighbors(n_neighbors=a.k).fit(Z[tr])
    pos_ids = acc[trpos]; tr_lab = trpos[tr].astype(float)
    base = trpos.sum() / tr.sum()
    thr = M["threshold_1pct"]
    flagged = (score > thr) & np.isin(g, ["test_pos", "test_ctl", "test_pending"])
    show = np.isin(g, ["test_pos", "test_ctl", "test_pending"]) if a.all_test else flagged
    d5, i5 = nn_pos.kneighbors(Z)
    dk, ik = nn_all.kneighbors(Z)
    share = tr_lab[ik].mean(axis=1)
    out = os.path.join(C.OUT, f"knn_{a.tag}.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["account", "group", "score_full", "flag_1pct", f"knn{a.k}_ban_share", "knn_share_over_base"] + [f"nn{i}_{x}" for i in range(1, 6) for x in ("id", "dist")])
        for j in np.where(show)[0]:
            w.writerow([acc[j], g[j], f"{score[j]:.4f}", int(score[j] > thr), f"{share[j]:.2f}", f"{share[j] / base:.1f}"]
                       + [v for i in range(5) for v in (pos_ids[i5[j, i]], f"{d5[j, i]:.2f}")])
    L = [f"# Nearest-ban evidence: {a.tag}", "",
         f"Training side: {int(trpos.sum())} bans among {int(tr.sum())} accounts (base rate {100 * base:.1f}%). Feature space: {len(cols)} standardized features, "
         f"scaler fit on training accounts only. Flagged (full model > 1% threshold {thr:.4f}) on test+pending: {int(flagged.sum())}.", ""]
    for grp in ("test_pos", "test_ctl", "test_pending"):
        m = flagged & (g == grp)
        if m.any():
            L.append(f"- flagged {grp}: {int(m.sum())}; median nearest-ban distance {np.median(d5[m, 0]):.2f}; median k={a.k} ban share {np.median(share[m]):.2f} ({np.median(share[m]) / base:.1f}x base)")
    L.append("")
    L.append("## Calibration on the test side")
    L.append("")
    tp, tc = g == "test_pos", g == "test_ctl"
    tm = tp | tc
    prev = tp.sum() / tm.sum()
    L.append(f"Test prevalence {100 * prev:.0f}% ({int(tp.sum())} bans, {int(tc.sum())} controls); a share that tracks the ban rate should rise across bins. "
             f"The last column reweights each bin's ban rate to a 1% bot share.")
    L.append("")
    L.append(f"| k={a.k} ban share | accounts | bans | observed ban rate | at 1% prevalence |")
    L.append("|---|---|---|---|---|")
    edges = [0, 0.001, 0.1, 0.2, 0.3, 0.5, 1.01]
    for lo, hi in zip(edges, edges[1:]):
        m = tm & (share >= lo) & (share < hi)
        if m.any():
            n, b = int(m.sum()), int((m & tp).sum())
            rate = b / n
            # reweight: odds scale by (0.01/0.99) / (prev/(1-prev))
            odds = (rate / (1 - rate)) * (0.01 / 0.99) / (prev / (1 - prev)) if rate < 1 else float("inf")
            L.append(f"| {lo:.1f}-{min(hi, 1):.1f} | {n} | {b} | {C.wilson(b, n)} | {100 * odds / (1 + odds):.0f}% |")
    L.append("")
    L.append(f"AUC of the k={a.k} ban share on the test side: {roc_auc_score(tp[tm], share[tm]):.3f} (full model: {roc_auc_score(tp[tm], score[tm]):.3f}). "
             f"Nearest-ban distance AUC (closer = more bot-like): {roc_auc_score(tp[tm], -d5[tm, 0]):.3f}.")
    from scipy.stats import spearmanr
    L.append(f"Spearman between ban share and model score on test: {spearmanr(share[tm], score[tm]).correlation:.2f}.")
    L.append("")
    L.append(f"Per-account neighbours: {out}")
    open(os.path.join(C.OUT, f"knn_{a.tag}.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
