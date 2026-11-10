#!/usr/bin/env python3
"""Brigade alarm: hourly outsider-activity anomaly detection per subreddit.

Usage: python3 -I brigade_alarm.py <compact_dir> <out_dir> [--test-week oct27]

Input: <week>.npz files from load_week.py (hashed authors only) plus bb_banned.npy.
Method (as pre-registered in claude/brigade-alarm-predictions.md):
  1. Home community per account: sub with most comments across all weeks, >=5 comments
     and top sub >=40% of them, else "no home" (excluded from outsider counts).
  2. Outsider activity per sub per UTC hour: comment count and distinct accounts.
  3. Baseline on weeks before the test week: per sub, multiplicative model
     mu = level[sub, week] * profile[sub, hour-of-day x weekday/weekend], fit by
     alternating (iterative proportional fitting). Dispersion phi = sum((y-mu)^2)/sum(mu).
  4. Alarms at the 99.9th percentile under Poisson and under a negative binomial
     whose extra variance (alpha, var = mu + alpha mu^2) is fit on baseline residuals.
     Leave-one-week-out false-alarm rate on the baseline weeks; then the test week.
  5. For each test-week alarm hour: observed vs expected, top home subs of the outsiders,
     biggest-thread share, Bot Bouncer share, each against normal hours.
No usernames exist in the inputs; outputs contain only sub names, hours, counts and thread ids.
"""
import sys, os, json, glob, argparse
from collections import Counter, defaultdict
import numpy as np
from scipy import stats

SUBS = ["Asmongold", "atrioc", "Conservative", "Destiny", "dsa", "h3h3productions",
        "Hasan_Piker", "IsraelPalestine", "LeftoversH3", "LivestreamFail", "neoliberal",
        "Palestine", "PoliticalCompassMemes", "samharris", "TankieTheDeprogram",
        "thebulwark", "thedavidpakmanshow", "ukraine"]
NS = len(SUBS)
Q = 0.999
MIN_COMMENTS, MIN_SHARE = 5, 0.40


def b36enc(n):
    n = int(n)
    if n == 0:
        return "0"
    s = ""
    while n:
        n, r = divmod(n, 36)
        s = "0123456789abcdefghijklmnopqrstuvwxyz"[r] + s
    return s


def load(compact):
    weeks = {}
    for f in sorted(glob.glob(os.path.join(compact, "*_meta.json"))):
        m = json.load(open(f))
        w = m["week"]
        z = np.load(os.path.join(compact, f"{w}.npz"))
        weeks[w] = dict(ah=z["ah"], t=z["t"], link=z["link"], sub=z["sub"], meta=m)
    return weeks


def cell_of(hour_idx):
    """hour index (epoch hours) -> cell 0..47: hod + 24*weekend."""
    hod = hour_idx % 24
    day = (hour_idx // 24 + 3) % 7  # epoch day 0 = Thursday -> Monday=0
    we = (day >= 5).astype(int)
    return hod + 24 * we


def covered_hours(meta_sub):
    """Fully covered epoch-hours for one (week, sub) file: ceil(tmin/3600) .. floor(tmax/3600)-1."""
    if meta_sub["tmin"] is None:
        return np.arange(0)
    h0 = -(-meta_sub["tmin"] // 3600)
    h1 = meta_sub["tmax"] // 3600  # exclusive
    return np.arange(h0, h1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("compact"); ap.add_argument("out")
    ap.add_argument("--test-week", default="oct27")
    ap.add_argument("--home-from", default="baseline", choices=["all", "baseline"],
                    help="which weeks define home communities (v1 pre-registered: all; v2 default: baseline)")
    ap.add_argument("--exposure", default="total", choices=["hours", "total"],
                    help="hours: mu = level*profile (v1); total: mu = total_comments*share_profile (v2 default)")
    ap.add_argument("--exclude-weeks", default="aug25",
                    help="comma-separated weeks to drop from the baseline (v2 default: aug25, truncated pull)")
    ap.add_argument("--alarm", default="nb", choices=["nb", "nbcal"],
                    help="nb: NB 99.9th pct (v1); nbcal: NB tail p-value cutoff calibrated by leave-one-week-out to 0.1%% of baseline hours (v2)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    weeks = load(a.compact)
    for w in [x for x in a.exclude_weeks.split(",") if x]:
        if w != a.test_week: weeks.pop(w, None)
    test = a.test_week
    base_weeks = [w for w in weeks if w != test]
    banned = set(np.load(os.path.join(a.compact, "bb_banned.npy")).tolist())
    R = {"test_week": test, "baseline_weeks": base_weeks, "excluded_weeks": a.exclude_weeks, "home_from": a.home_from, "exposure": a.exposure}
    def expo(r):
        return r["total"].astype(float) if a.exposure == "total" else np.ones(len(r["hours"]))

    # ---- 1. home community -------------------------------------------------
    home_weeks = list(weeks) if a.home_from == "all" else base_weeks
    AH = np.concatenate([weeks[w]["ah"] for w in home_weeks])
    SB = np.concatenate([weeks[w]["sub"] for w in home_weeks]).astype(np.int64)
    uniq, inv = np.unique(AH, return_inverse=True)
    M = np.zeros((len(uniq), NS), dtype=np.int64)
    np.add.at(M, (inv, SB), 1)
    tot = M.sum(1); top = M.argmax(1); topn = M.max(1)
    has_home = (tot >= MIN_COMMENTS) & (topn >= MIN_SHARE * tot)
    home_of = np.where(has_home, top, -1)
    home_map = dict(zip(uniq.tolist(), home_of.tolist()))
    n_acc = len(uniq)
    R["home"] = {
        "accounts_total": int(n_acc),
        "accounts_with_home": int(has_home.sum()),
        "accounts_no_home_share": float(1 - has_home.mean()),
        "accounts_under_5_comments_share": float((tot < MIN_COMMENTS).mean()),
        "accounts_5plus_but_under_40pct_share": float(((tot >= MIN_COMMENTS) & ~has_home).mean()),
        "comments_total": int(tot.sum()),
        "comments_by_no_home_accounts_share": float(tot[~has_home].sum() / tot.sum()),
        "home_sub_counts": {SUBS[i]: int((home_of == i).sum()) for i in range(NS)},
    }

    # ---- 2. hourly tables --------------------------------------------------
    # rows: (week, sub, hour) -> outsider comments, outsider accounts, total comments
    rows = []  # dicts per (week, sub)
    for w, d in weeks.items():
        home = np.array([home_map.get(x, -1) for x in d["ah"].tolist()], dtype=np.int64)
        hr = d["t"] // 3600
        for s in range(NS):
            ms = d["meta"]["coverage"].get(SUBS[s])
            if not ms or ms["tmin"] is None:
                continue
            hours = covered_hours(ms)
            if len(hours) == 0:
                continue
            sel = d["sub"] == s
            h_s = hr[sel]; home_s = home[sel]; ah_s = d["ah"][sel]; lk_s = d["link"][sel]
            inwin = (h_s >= hours[0]) & (h_s < hours[-1] + 1)
            h_s, home_s, ah_s, lk_s = h_s[inwin], home_s[inwin], ah_s[inwin], lk_s[inwin]
            idx = h_s - hours[0]
            total = np.bincount(idx, minlength=len(hours))
            out = (home_s >= 0) & (home_s != s)
            oc = np.bincount(idx[out], minlength=len(hours))
            # distinct outsider accounts per hour
            pairs = np.unique(np.stack([idx[out], ah_s[out].astype(np.int64)], 1), axis=0)
            oa = np.bincount(pairs[:, 0], minlength=len(hours)) if len(pairs) else np.zeros(len(hours), int)
            rows.append(dict(week=w, sub=s, hours=hours, total=total, oc=oc, oa=oa,
                             # keep per-comment detail for alarm drill-down
                             idx=idx[out], home=home_s[out], ah=ah_s[out], link=lk_s[out]))
    R["outsider_share_by_sub"] = {}
    for s in range(NS):
        oc = sum(r["oc"].sum() for r in rows if r["sub"] == s and r["week"] != test)
        tt = sum(r["total"].sum() for r in rows if r["sub"] == s and r["week"] != test)
        R["outsider_share_by_sub"][SUBS[s]] = float(oc / tt) if tt else None

    # ---- 3/4. model fitting helpers -----------------------------------------
    def fit_profile(sub, fit_weeks, measure):
        """IPF for mu = level[week] * prof[cell]. Returns prof (48,) with weighted mean 1."""
        rs = [r for r in rows if r["sub"] == sub and r["week"] in fit_weeks]
        if not rs:
            return None
        prof = np.ones(48)
        for _ in range(25):
            # levels given profile
            lev = {}
            for r in rs:
                c = cell_of(r["hours"]); y = r[measure]; e = expo(r)
                lev[r["week"]] = y.sum() / max((prof[c] * e).sum(), 1e-9)
            num = np.zeros(48); den = np.zeros(48)
            for r in rs:
                c = cell_of(r["hours"]); y = r[measure]; e = expo(r)
                np.add.at(num, c, y); np.add.at(den, c, lev[r["week"]] * e)
            prof = np.where(den > 0, num / np.maximum(den, 1e-9), prof)
            # normalise: exposure-weighted mean 1
            wts = np.zeros(48)
            for r in rs:
                np.add.at(wts, cell_of(r["hours"]), expo(r))
            prof = prof / max((prof * wts).sum() / wts.sum(), 1e-9)
        # pooled residual dispersion on the fit weeks
        ys, mus = [], []
        for r in rs:
            c = cell_of(r["hours"]); y = r[measure]; e = expo(r)
            lev = y.sum() / max((prof[c] * e).sum(), 1e-9)
            ys.append(y); mus.append(lev * prof[c] * e)
        y = np.concatenate(ys); mu = np.concatenate(mus)
        ok = mu > 0
        phi = float(((y[ok] - mu[ok]) ** 2).sum() / mu[ok].sum())
        alpha = float(max(((y[ok] - mu[ok]) ** 2 - mu[ok]).sum() / (mu[ok] ** 2).sum(), 0.0))
        return dict(prof=prof, phi=phi, alpha=alpha, n_hours=int(ok.sum()), mean=float(mu[ok].mean()))

    def expected(r, prof, measure):
        c = cell_of(r["hours"]); y = r[measure]; e = expo(r)
        lev = y.sum() / max((prof[c] * e).sum(), 1e-9)  # scaled by this week's own level
        return lev * prof[c] * e

    def thresholds(mu, alpha):
        """Alarm if y > q. Returns Poisson q and NB q (99.9th percentile)."""
        mu = np.maximum(mu, 1e-9)
        qp = stats.poisson.ppf(Q, mu)
        if alpha <= 1e-9:
            qn = qp
        else:
            n = 1.0 / alpha; p = n / (n + mu)
            qn = stats.nbinom.ppf(Q, n, p)
        return qp, qn

    def nb_sf(y, mu, alpha):
        """P(Y >= y) under NB (or Poisson if alpha ~ 0)."""
        mu = np.maximum(mu, 1e-9)
        if alpha <= 1e-9:
            return stats.poisson.sf(y - 1, mu)
        n = 1.0 / alpha; p = n / (n + mu)
        return stats.nbinom.sf(y - 1, n, p)

    measures = ["oc", "oa"]
    lowo_p = {m: [] for m in measures}
    MIN_ACC = 5
    lowo_v2 = [0, 0]
    # dispersion table (fit on all baseline weeks)
    fits = {}
    R["dispersion"] = {}
    for s in range(NS):
        for m in measures:
            f = fit_profile(s, base_weeks, m)
            fits[(s, m)] = f
            if f:
                R["dispersion"].setdefault(SUBS[s], {})[m] = dict(
                    phi=round(f["phi"], 2), alpha=round(f["alpha"], 4), mean_per_hour=round(f["mean"], 2),
                    n_hours=f["n_hours"])

    # leave-one-week-out false alarm rate on baseline weeks
    lowo = {m: {"poisson": [0, 0], "nb": [0, 0]} for m in measures}
    lowo_sub = {m: {"poisson": Counter(), "nb": Counter(), "hours": Counter()} for m in measures}
    for w in base_weeks:
        others = [x for x in base_weeks if x != w]
        for s in range(NS):
            r = next((r for r in rows if r["sub"] == s and r["week"] == w), None)
            if r is None:
                continue
            for m in measures:
                f = fit_profile(s, others, m)
                if f is None:
                    continue
                mu = expected(r, f["prof"], m)
                qp, qn = thresholds(mu, f["alpha"])
                y = r[m]
                lowo_p[m].append(nb_sf(y, mu, f["alpha"]))
                if m == "oa":
                    lowo_v2[0] += int(((y > qn) & (y >= MIN_ACC)).sum()); lowo_v2[1] += len(y)
                lowo[m]["poisson"][0] += int((y > qp).sum()); lowo[m]["poisson"][1] += len(y)
                lowo[m]["nb"][0] += int((y > qn).sum()); lowo[m]["nb"][1] += len(y)
                lowo_sub[m]["poisson"][SUBS[s]] += int((y > qp).sum())
                lowo_sub[m]["nb"][SUBS[s]] += int((y > qn).sum())
                lowo_sub[m]["hours"][SUBS[s]] += len(y)
    R["false_alarm_lowo"] = {
        m: {k: dict(alarms=v[0], hours=v[1], rate=round(v[0] / v[1], 5) if v[1] else None,
                    rate_x_nominal=round((v[0] / v[1]) / (1 - Q), 1) if v[1] else None)
            for k, v in lowo[m].items()} for m in measures}
    R["false_alarm_lowo_by_sub"] = {
        m: {s: dict(poisson=lowo_sub[m]["poisson"][s], nb=lowo_sub[m]["nb"][s], hours=lowo_sub[m]["hours"][s])
            for s in SUBS if lowo_sub[m]["hours"][s]} for m in measures}

    R["false_alarm_lowo_v2_rule"] = dict(alarms=lowo_v2[0], hours=lowo_v2[1], rate=round(lowo_v2[0] / max(lowo_v2[1], 1), 5),
        rate_x_nominal=round(lowo_v2[0] / max(lowo_v2[1], 1) / (1 - Q), 2), rule="NB 99.9% on outsider accounts AND >=5 outsider accounts")
    pstar = {m: float(np.quantile(np.concatenate(lowo_p[m]), 1 - Q)) for m in measures}
    R["calibrated_p_cutoff"] = pstar
    # ---- 5. test week alarms -------------------------------------------------
    alarms = []
    test_summary = {m: {"poisson": 0, "nb": 0, "hours": 0} for m in measures}
    normal_stats = {}  # per sub: biggest-thread share and bb share in non-alarm hours
    for s in range(NS):
        r = next((r for r in rows if r["sub"] == s and r["week"] == test), None)
        if r is None:
            continue
        flags = {}
        mus = {}
        for m in measures:
            f = fits[(s, m)]
            if f is None:
                continue
            mu = expected(r, f["prof"], m); mus[m] = mu
            qp, qn = thresholds(mu, f["alpha"])
            y = r[m]
            cal = nb_sf(y, mu, f["alpha"]) < pstar[m]
            flags[m] = dict(poisson=(y > qp), nb=(y > qn), nbcal=cal, qp=qp, qn=qn)
            test_summary[m]["poisson"] += int((y > qp).sum()); test_summary[m]["nb"] += int((y > qn).sum())
            test_summary[m]["nbcal"] = test_summary[m].get("nbcal", 0) + int(cal.sum())
            test_summary[m]["hours"] += len(y)
        if not flags:
            continue
        nb_any = np.zeros(len(r["hours"]), bool)
        for m in flags:
            nb_any |= flags[m][a.alarm]
        # per-hour drill-down data
        n_h = len(r["hours"])
        # biggest-thread share and bb share for every hour with >=5 outsider comments
        thread_share = np.full(n_h, np.nan); bb_share = np.full(n_h, np.nan)
        for h in range(n_h):
            sel = r["idx"] == h
            if sel.sum() == 0:
                continue
            lk = r["link"][sel]
            cnt = Counter(lk.tolist())
            thread_share[h] = cnt.most_common(1)[0][1] / sel.sum()
            accs = set(r["ah"][sel].tolist())
            bb_share[h] = len(accs & banned) / len(accs)
        normal = (~nb_any) & (r["oc"] >= 5)
        normal10 = (~nb_any) & (r["oc"] >= 10)
        normal_stats[SUBS[s]] = dict(
            n_normal_hours=int(normal.sum()),
            biggest_thread_share_mean=float(np.nanmean(thread_share[normal])) if normal.any() else None,
            biggest_thread_share_median=float(np.nanmedian(thread_share[normal])) if normal.any() else None,
            biggest_thread_over_half_share=float(np.nanmean(thread_share[normal] > 0.5)) if normal.any() else None,
            bb_share_mean=float(np.nanmean(bb_share[normal])) if normal.any() else None,
            n_normal_hours_10plus=int(normal10.sum()),
            biggest_thread_share_mean_10plus=float(np.nanmean(thread_share[normal10])) if normal10.any() else None,
            biggest_thread_over_half_share_10plus=float(np.nanmean(thread_share[normal10] > 0.5)) if normal10.any() else None,
        )
        # pooled normal-hour accounts for BB share (accounts, not hour means)
        nsel = np.isin(r["idx"], np.where(normal)[0])
        naccs = set(r["ah"][nsel].tolist())
        normal_stats[SUBS[s]]["normal_outsider_accounts"] = len(naccs)
        normal_stats[SUBS[s]]["normal_bb_accounts"] = len(naccs & banned)
        # pooled bb share over normal hours (accounts pooled)
        for h in np.where(nb_any)[0]:
            sel = r["idx"] == h
            homes = Counter(SUBS[int(x)] for x in r["home"][sel].tolist())
            tot_o = max(sel.sum(), 1)
            lk = r["link"][sel]
            cnt = Counter(lk.tolist())
            top_thread, top_n = (cnt.most_common(1)[0] if cnt else (0, 0))
            accs = set(r["ah"][sel].tolist())
            alarms.append(dict(
                sub=SUBS[s], hour_utc=int(r["hours"][h]),
                hour_iso=np.datetime64(int(r["hours"][h]) * 3600, "s").astype(str),
                triggered=[m for m in flags if flags[m]["nb"][h]],
                poisson_also=[m for m in flags if flags[m]["poisson"][h]],
                outsider_comments=int(r["oc"][h]), expected_comments=round(float(mus["oc"][h]), 1),
                nb_threshold_comments=int(flags["oc"]["qn"][h]) if "oc" in flags else None,
                outsider_accounts=int(r["oa"][h]), expected_accounts=round(float(mus["oa"][h]), 1),
                nb_threshold_accounts=int(flags["oa"]["qn"][h]) if "oa" in flags else None,
                total_comments=int(r["total"][h]),
                top_home_subs=[(k, round(v / tot_o, 2)) for k, v in homes.most_common(3)],
                biggest_thread_id="t3_" + b36enc(top_thread), biggest_thread_share=round(top_n / tot_o, 2),
                n_threads=len(cnt),
                bb_share_accounts=round(len(accs & banned) / max(len(accs), 1), 3), n_outsider_accounts=len(accs),
                n_bb_accounts=len(accs & banned),
            ))
    alarms.sort(key=lambda d: (d["sub"], d["hour_utc"]))
    R["test_alarm_summary"] = {m: dict(v, poisson_rate=round(v["poisson"] / v["hours"], 5) if v["hours"] else None,
                                       nb_rate=round(v["nb"] / v["hours"], 5) if v["hours"] else None)
                               for m, v in test_summary.items()}
    R["alarms_nb"] = alarms
    R["normal_hours_test_week"] = normal_stats
    # pooled comparisons for predictions 5 and 6
    if alarms:
        material = [d for d in alarms if d["outsider_comments"] >= 10]
        # hour-weighted normal comparisons (pool hours across subs)
        def pooled(key_n, key_mean):
            n = sum(v[key_n] for v in normal_stats.values() if v[key_mean] is not None)
            return round(sum(v[key_n] * v[key_mean] for v in normal_stats.values() if v[key_mean] is not None) / max(n, 1), 3), n
        nm5, n5 = pooled("n_normal_hours", "biggest_thread_share_mean")
        nh5, _ = pooled("n_normal_hours", "biggest_thread_over_half_share")
        nm10, n10 = pooled("n_normal_hours_10plus", "biggest_thread_share_mean_10plus")
        nh10, _ = pooled("n_normal_hours_10plus", "biggest_thread_over_half_share_10plus")
        R["pred5"] = dict(
            alarm_hours=len(alarms),
            alarm_hours_biggest_thread_over_half=sum(1 for d in alarms if d["biggest_thread_share"] > 0.5),
            alarm_biggest_thread_share_mean=round(float(np.mean([d["biggest_thread_share"] for d in alarms])), 3),
            material_alarm_hours=len(material),
            material_over_half=sum(1 for d in material if d["biggest_thread_share"] > 0.5),
            material_biggest_thread_share_mean=round(float(np.mean([d["biggest_thread_share"] for d in material])), 3) if material else None,
            normal5_hours=n5, normal5_biggest_thread_share_mean=nm5, normal5_over_half_share=nh5,
            normal10_hours=n10, normal10_biggest_thread_share_mean=nm10, normal10_over_half_share=nh10,
        )
        bb_tot = sum(d["n_bb_accounts"] for d in alarms); acc_tot = sum(d["n_outsider_accounts"] for d in alarms)
        nbb = sum(v["normal_bb_accounts"] for v in normal_stats.values()); nacc = sum(v["normal_outsider_accounts"] for v in normal_stats.values())
        R["pred6"] = dict(alarm_bb_accounts=bb_tot, alarm_outsider_accounts=acc_tot,
                          alarm_bb_share=round(bb_tot / max(acc_tot, 1), 4),
                          normal_bb_accounts=nbb, normal_outsider_accounts=nacc,
                          normal_bb_share=round(nbb / max(nacc, 1), 4))
        R["alarms_by_sub"] = dict(Counter(d["sub"] for d in alarms))
        R["material_alarms_by_sub"] = dict(Counter(d["sub"] for d in material))
    # test-week overall BB share among outsider accounts, all hours
    allacc = set();
    for r in rows:
        if r["week"] == test:
            allacc |= set(r["ah"].tolist())
    R["test_week_outsider_accounts_bb_share_all_hours"] = round(len(allacc & banned) / max(len(allacc), 1), 4)
    R["banned_list_size"] = len(banned)

    with open(os.path.join(a.out, f"results_{test}_{a.home_from}_{a.exposure}_ex{a.exclude_weeks.replace(',','-') or 'none'}.json"), "w") as f:
        json.dump(R, f, indent=1, default=str)
    print(json.dumps({k: R[k] for k in ("home", "false_alarm_lowo", "test_alarm_summary")}, indent=1))
    print("alarms:", len(alarms))


if __name__ == "__main__":
    main()
