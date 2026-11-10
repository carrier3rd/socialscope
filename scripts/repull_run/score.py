#!/usr/bin/env python3
"""Train on the train side, test once on the test side, with honest thresholds and intervals
(scripts/repull_run/score.py, Nov 5 2026). Replaces scripts/insub_run/score.py.

What changed and why:
  * Threshold. The old 1% threshold was the 99th percentile of the TEST controls' scores, so the false-alarm rate
    was fixed at 1% by construction and the recall was read off the same accounts. Here the thresholds for 1/2/5%
    FPR come from the TRAINING controls' out-of-fold scores (5-fold stratified CV on the train side), the model is
    refit on all of train, and the test side reports the FPR it actually reaches at that threshold. The old
    test-control threshold is still printed for comparison.
  * Intervals. 2,000 bootstrap resamples over accounts, stratified by class (test positives, test controls, and the
    training controls whose out-of-fold scores set the threshold), threshold recomputed inside each resample, for
    recall at 1/2/5% FPR, AUC, achieved FPR, and precision at 1% and 5% bot share. Percentile intervals.
  * Ablation. "Without volume" now also drops hist_age and every feature coupled to the item count under a cap
    (the list is NOVOL below; the Spearman table in the output shows the coupling on controls). Paired bootstrap
    (same resamples) for full vs no-volume vs the age rule (younger account = higher score; the v7.1 primary tier
    is reported as a point too).
  * Recall split by aged (100+ items over a year or more at the anchor) vs throwaway positives.
  * Permutation importances on the test side (10 repeats, AUC), for the full and the no-volume model.
  * Outputs a hashed accounts csv for MATLAB with every feature column and the scores.

Usage: python3 -I scripts/repull_run/score.py --tag old_last [--boot 2000] [--seed 0]
Reads <out>/features_<tag>.pkl (from feats.py); writes <out>/results_<tag>.md, accounts_<tag>.csv, model_<tag>.pkl.
Hashed ids only; nothing here ever sees a username.
"""
import argparse, collections, csv, datetime, math, os, pickle, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402
from sklearn.impute import SimpleImputer  # noqa: E402
from sklearn.inspection import permutation_importance  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

# Features that scale with how many items the cap let through (or with the span those items cover). Under the old
# pull they carried the class artifact; under the re-pull they are legitimate but the ablation still drops them so
# the two runs stay comparable. bot_score and primary include young_account, whose "first item in the pulled
# history" is a cap artifact too.
NOVOL = {"items", "comments", "subs", "log_items", "hist_age", "longest_gap_days", "state_media_links", "bot_score", "primary",
         "pw_earlier_items", "pw_window_items", "pw_posting_rate_ratio", "pw_longest_silence_before_window"}
FPRS = (0.01, 0.02, 0.05)
GB = dict(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0)


def gb(seed=0):
    return HistGradientBoostingClassifier(random_state=seed, **GB)


def fl(x):
    return float(x) if x not in (None, "") else np.nan


def matrix(rows, num, pwk):
    names = num + ["hist_age", "true_age", "sh", "sb", "primary", "log_items"] + ["pw_" + k for k in pwk if k != "removed_share"]
    X = np.array([[fl(r.get(c)) for c in num] + [fl(r["hist_age"]), fl(r["true_age"]), float(r["sh"]), float(r["sb"]), float(r["primary"]),
                   math.log1p(r["n_cut"])] + [fl(r.get("pw_" + k)) for k in pwk if k != "removed_share"] for r in rows], dtype=float)
    return names, X


def oof_scores(X, y, tr, cols, seed, folds=5):
    """Out-of-fold scores for the training rows (balanced sample weights as in the old run)."""
    idx = np.where(tr)[0]
    oof = np.full(len(y), np.nan)
    skf = StratifiedKFold(folds, shuffle=True, random_state=seed)
    for a, b in skf.split(idx, y[idx]):
        ia, ib = idx[a], idx[b]
        w = np.where(y[ia], (~y[ia]).sum() / max(1, y[ia].sum()), 1.0)
        m = gb(seed).fit(X[ia][:, cols], y[ia], sample_weight=w)
        oof[ib] = m.predict_proba(X[ib][:, cols])[:, 1]
    return oof


def fit_full(X, y, tr, cols, seed):
    w = np.where(y[tr], (~y[tr]).sum() / max(1, y[tr].sum()), 1.0)
    return gb(seed).fit(X[tr][:, cols], y[tr], sample_weight=w)


def prec(rec, fpr, pi):
    return rec * pi / (rec * pi + fpr * (1 - pi)) if (rec * pi + fpr * (1 - pi)) > 0 else float("nan")


def ci(v, lo=2.5, hi=97.5):
    v = np.asarray(v, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return "n/a"
    return f"{np.percentile(v, lo):.3f}-{np.percentile(v, hi):.3f}"


def pct(v, lo=2.5, hi=97.5):
    v = np.asarray(v, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return "n/a"
    return f"{100 * np.percentile(v, lo):.0f}-{100 * np.percentile(v, hi):.0f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--folds", type=int, default=5)
    a = ap.parse_args()
    D = pickle.load(open(os.path.join(C.OUT, f"features_{a.tag}.pkl"), "rb"))
    rows = [r for r in D["rows"] if r["n_cut"] > 0]
    names, X = matrix(rows, D["num"], D["pwk"])
    g = np.array([r["group"] for r in rows])
    y = (g == "train_pos") | (g == "test_pos")
    tr = np.isin(g, ["train_pos", "train_ctl"])
    tp, tc, pe = g == "test_pos", g == "test_ctl", g == "test_pending"
    aged = np.array([bool(r["aged"]) for r in rows])
    ok = [j for j in range(X.shape[1]) if len(np.unique(X[tr][:, j][~np.isnan(X[tr][:, j])])) >= 2]
    names_ok = [names[j] for j in ok]
    novol = [j for j in ok if names[j] not in NOVOL]
    L = []

    def say(s=""):
        print(s, flush=True)
        L.append(s)

    say(f"# Results: {a.tag} (scored {datetime.datetime.now():%Y-%m-%d %H:%M})")
    say("")
    say(f"Train: {int((g == 'train_pos').sum())} positives, {int((g == 'train_ctl').sum())} controls. "
        f"Test: {int(tp.sum())} positives ({int((tp & aged).sum())} aged, {int((tp & ~aged).sum())} throwaway), {int(tc.sum())} controls, {int(pe.sum())} pending. "
        f"{len(ok)} features ({len(novol)} without volume).")
    say("")
    say("## Rules at the anchor (95% Wilson)")
    w = C.wilson
    PA = tp & aged
    say(f"- aged: positives {w(int(PA.sum()), int(tp.sum()))}; controls {w(int((tc & aged).sum()), int(tc.sum()))}; pending {w(int((pe & aged).sum()), int(pe.sum()))}")
    sh = np.array([bool(r["sh"]) for r in rows]); sb = np.array([bool(r["sb"]) for r in rows]); pr = np.array([bool(r["primary"]) for r in rows])
    say(f"- solicit_handle: aged positives {w(int((PA & sh).sum()), int(PA.sum()))}; all positives {w(int((tp & sh).sum()), int(tp.sum()))}; controls {w(int((tc & sh).sum()), int(tc.sum()))}")
    say(f"- solicit_broad: aged positives {w(int((PA & sb).sum()), int(PA.sum()))}; all positives {w(int((tp & sb).sum()), int(tp.sum()))}; controls {w(int((tc & sb).sum()), int(tc.sum()))}")
    say(f"- v7.1 primary tier: positives {w(int((tp & pr).sum()), int(tp.sum()))}; controls {w(int((tc & pr).sum()), int(tc.sum()))}; pending {w(int((pe & pr).sum()), int(pe.sum()))}")
    say("")

    # models
    seed = a.seed
    oof_full = oof_scores(X, y, tr, ok, seed, a.folds)
    oof_nov = oof_scores(X, y, tr, novol, seed, a.folds)
    m_full = fit_full(X, y, tr, ok, seed)
    m_nov = fit_full(X, y, tr, novol, seed)
    s_full = m_full.predict_proba(X[:, ok])[:, 1]
    s_nov = m_nov.predict_proba(X[:, novol])[:, 1]
    lr = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=3000, C=0.3, class_weight="balanced")).fit(X[tr][:, ok], y[tr])
    s_lr = lr.predict_proba(X[:, ok])[:, 1]
    age = X[:, names.index("true_age")]
    age = np.where(np.isnan(age), X[:, names.index("hist_age")], age)
    s_age = -age   # younger = more bot-like
    oof_age = s_age.copy()  # a rule has no fitting, so its "out-of-fold" score is itself
    say(f"Train-side CV (out-of-fold) AUC: full {roc_auc_score(y[tr], oof_full[tr]):.3f}, no-volume {roc_auc_score(y[tr], oof_nov[tr]):.3f}, age rule {roc_auc_score(y[tr], s_age[tr]):.3f}")
    say("")

    models = [("full", s_full, oof_full), ("no-volume", s_nov, oof_nov), ("age rule", s_age, oof_age), ("logistic (full features)", s_lr, None)]
    trc = np.where(g == "train_ctl")[0]
    ipos, ineg, ipen = np.where(tp)[0], np.where(tc)[0], np.where(pe)[0]
    thr = {}

    say("## Test-side point estimates")
    say("")
    say("Threshold from training controls' out-of-fold scores (CV); FPR is what the test controls actually reach.")
    say("")
    say("| model | AUC | FPR target | threshold | test FPR | recall | aged recall | throwaway recall | pending flagged | precision @1% bots | @5% bots |")
    say("|---|---|---|---|---|---|---|---|---|---|---|")
    for name, s, oof in models:
        auc = roc_auc_score(y[tp | tc], s[tp | tc])
        for f in FPRS:
            if oof is not None:
                t = np.quantile(oof[trc], 1 - f)
            else:
                t = np.quantile(s[ineg], 1 - f)   # logistic: old-style threshold only (kept as the old secondary readout)
            thr[(name, f)] = t
            rec = (s[ipos] > t).mean(); fpr = (s[ineg] > t).mean()
            ra = (s[ipos][aged[ipos]] > t).mean() if aged[ipos].any() else float("nan")
            rt = (s[ipos][~aged[ipos]] > t).mean() if (~aged[ipos]).any() else float("nan")
            say(f"| {name} | {auc:.3f} | {100 * f:.0f}% | {t:.4f} | {100 * fpr:.1f}% | {w(int((s[ipos] > t).sum()), len(ipos))} | "
                f"{w(int((s[ipos][aged[ipos]] > t).sum()), int(aged[ipos].sum()))} | {w(int((s[ipos][~aged[ipos]] > t).sum()), int((~aged[ipos]).sum()))} | "
                f"{100 * (s[ipen] > t).mean():.0f}% | {100 * prec(rec, fpr, 0.01):.0f}% | {100 * prec(rec, fpr, 0.05):.0f}% |")
    say("")
    say("Old method for comparison (threshold = quantile of the TEST controls, so FPR is fixed by construction):")
    say("")
    say("| model | FPR | recall | precision @1% bots |")
    say("|---|---|---|---|")
    for name, s, _ in models[:3]:
        for f in FPRS:
            t = np.quantile(s[ineg], 1 - f); rec = (s[ipos] > t).mean(); fpr = (s[ineg] > t).mean()
            say(f"| {name} | {100 * f:.0f}% | {w(int((s[ipos] > t).sum()), len(ipos))} | {100 * prec(rec, fpr, 0.01):.0f}% |")
    say("")

    # bootstrap
    rng = np.random.default_rng(seed)
    B = a.boot
    boot = {name: {f: collections.defaultdict(list) for f in FPRS} for name, _, _ in models[:3]}
    aucs = {name: [] for name, _, _ in models[:3]}
    for b in range(B):
        bp = rng.choice(ipos, len(ipos)); bn = rng.choice(ineg, len(ineg)); bt = rng.choice(trc, len(trc))
        yy = np.r_[np.ones(len(bp)), np.zeros(len(bn))]
        for name, s, oof in models[:3]:
            ss = np.r_[s[bp], s[bn]]
            aucs[name].append(roc_auc_score(yy, ss))
            for f in FPRS:
                t = np.quantile(oof[bt], 1 - f)
                rec = (s[bp] > t).mean(); fpr = (s[bn] > t).mean()
                d = boot[name][f]
                d["recall"].append(rec); d["fpr"].append(fpr)
                d["prec1"].append(prec(rec, fpr, 0.01)); d["prec5"].append(prec(rec, fpr, 0.05))
                ab = aged[bp]
                d["recall_aged"].append((s[bp][ab] > t).mean() if ab.any() else np.nan)
                d["recall_throw"].append((s[bp][~ab] > t).mean() if (~ab).any() else np.nan)
                t2 = np.quantile(s[bn], 1 - f)   # old method, recomputed inside the resample
                d["recall_old"].append((s[bp] > t2).mean())
    say(f"## Bootstrap intervals ({B} resamples over accounts, stratified by class; threshold recomputed in each)")
    say("")
    say("| model | AUC 95% CI | FPR target | recall CI | test FPR CI | precision @1% CI | @5% CI | aged recall CI | throwaway recall CI | recall CI, old threshold |")
    say("|---|---|---|---|---|---|---|---|---|---|")
    for name, _, _ in models[:3]:
        for f in FPRS:
            d = boot[name][f]
            say(f"| {name} | {ci(aucs[name])} | {100 * f:.0f}% | {pct(d['recall'])} | {pct(d['fpr'])} | {pct(d['prec1'])} | {pct(d['prec5'])} | "
                f"{pct(d['recall_aged'])} | {pct(d['recall_throw'])} | {pct(d['recall_old'])} |")
    say("")
    say("## Paired comparisons (same resamples)")
    say("")
    say("| comparison | AUC difference CI | share of resamples with A better | recall @1% difference CI | share A better |")
    say("|---|---|---|---|---|")
    for A_, B_ in (("full", "no-volume"), ("full", "age rule"), ("no-volume", "age rule")):
        da = np.array(aucs[A_]) - np.array(aucs[B_])
        dr = np.array(boot[A_][0.01]["recall"]) - np.array(boot[B_][0.01]["recall"])
        say(f"| {A_} vs {B_} | {ci(da)} | {100 * (da > 0).mean():.0f}% | {pct(dr)} | {100 * (dr > 0).mean():.0f}% |")
    say("")

    # importances
    m = tp | tc
    say("## Permutation importances on the test side (AUC drop, 10 repeats)")
    say("")
    for label, mdl, cols in (("full", m_full, ok), ("no-volume", m_nov, novol)):
        pi = permutation_importance(mdl, X[m][:, cols], y[m], n_repeats=10, random_state=seed, scoring="roc_auc")
        top = np.argsort(-pi.importances_mean)[:15]
        say(f"- {label}: " + ", ".join(f"{names[cols[i]]} {pi.importances_mean[i]:.3f}" for i in top))
    say("")
    say("## Feature coupling with log(items) on controls (Spearman |rho| >= 0.3)")
    say("")
    from scipy.stats import spearmanr
    ctl = np.isin(g, ["train_ctl", "test_ctl"])
    li = X[ctl][:, names.index("log_items")]
    cop = []
    for j in ok:
        v = X[ctl][:, j]
        mk = ~np.isnan(v)
        if mk.sum() > 30 and names[j] != "log_items":
            r = spearmanr(li[mk], v[mk]).correlation
            if abs(r) >= 0.3:
                cop.append((names[j], r))
    say(", ".join(f"{n} {r:+.2f}{' (dropped)' if n in NOVOL else ''}" for n, r in sorted(cop, key=lambda x: -abs(x[1]))) or "none")
    say("")
    rs = [r["pw_removed_share"] for r in rows if r.get("pw_removed_share") is not None]
    if rs:
        rp = np.array([fl(r.get("pw_removed_share")) for r in rows])
        say(f"Removed-item share in the 30-day window (not a model feature): positives mean {np.nanmean(rp[tp]):.3f}, controls {np.nanmean(rp[tc]):.3f}, pending {np.nanmean(rp[pe]):.3f}.")
    say("")
    say(f"Anchor sources: " + ", ".join(f"{k} {v}" for k, v in sorted(collections.Counter(r['anchor_src'] for r in rows).items())))

    # outputs
    open(os.path.join(C.OUT, f"results_{a.tag}.md"), "w").write("\n".join(L) + "\n")
    t1, t5 = thr[("full", 0.01)], thr[("full", 0.05)]
    pickle.dump(dict(tag=a.tag, model=m_full, model_novol=m_nov, num=D["num"], pwk=D["pwk"], names=names, ok=ok, novol=novol,
                     threshold_1pct=t1, threshold_2pct=thr[("full", 0.02)], threshold_5pct=t5, thresholds=thr),
                open(os.path.join(C.OUT, f"model_{a.tag}.pkl"), "wb"))
    lab = {"test_pos": "botbouncer_banned", "train_pos": "botbouncer_banned", "test_pending": "botbouncer_pending",
           "test_ctl": "unlisted", "train_ctl": "unlisted"}
    split = {"test_pos": "test", "test_ctl": "test", "test_pending": "pending", "train_pos": "train", "train_ctl": "train"}
    feat_cols = [c for c in rows[0] if c not in ("account", "group", "cohort_source", "flair", "tier", "flag_list", "home_sub")]
    out = os.path.join(C.OUT, f"accounts_{a.tag}.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        hdr = ["account", "group", "split", "label", "label_source", "bot_type", "anchor_date", "home_sub", "score_full", "score_novol",
               "score_age", "oof_score_full", "flag_1pct", "flag_2pct", "flag_5pct"] + feat_cols
        wr = csv.writer(fh); wr.writerow(hdr)
        for i, r in enumerate(rows):
            wr.writerow([r["account"], r["group"], split[r["group"]], int(y[i]), lab[r["group"]] + ("_" + r["cohort_source"] if r["group"].endswith("ctl") else ""),
                         "aged" if r["aged"] else "throwaway", datetime.datetime.fromtimestamp(r["anchor_utc"], datetime.timezone.utc).strftime("%Y-%m-%d"),
                         r["home_sub"], round(float(s_full[i]), 6), round(float(s_nov[i]), 6), round(float(s_age[i]), 2),
                         "" if np.isnan(oof_full[i]) else round(float(oof_full[i]), 6),
                         int(s_full[i] > t1), int(s_full[i] > thr[("full", 0.02)]), int(s_full[i] > t5)] + [r.get(c, "") for c in feat_cols])
    say(f"wrote {out} and results_{a.tag}.md, model_{a.tag}.pkl")


if __name__ == "__main__":
    main()
