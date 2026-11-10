#!/usr/bin/env python3
"""Cut each history at its anchor and compute every feature (scripts/repull_run/feats.py, Nov 5 2026).

Replaces scripts/insub_run/build.py + feats.py. Differences from the old run, each one deliberate:
  * anchors: positives and pending at listed_utc (unchanged). Controls take the anchor from the file pull.py wrote
    (--anchors; required in --mode repull) or, on the old capped data, either their own last item (--control-anchor
    last, the old rule) or a matched anchor drawn the same way pull.py draws it (--control-anchor matched).
  * removed text: items whose comment body is [removed]/[deleted] are left out of the text-based prewindow features
    (median length ratio, link-share change, short-comment share); posts whose selftext is [removed]/[deleted] keep
    their title and drop the selftext. Counts and subreddit features still see every item. socialscope/history.py
    already excluded removed bodies; socialscope/prewindow.py did not. --keep-removed restores the old behaviour.
    The share of removed items in the window is recorded (pw_removed_share) but score.py does not model it: removal
    can follow from the listing itself, so it would leak the label.
  * hist_age (anchor minus first item in the cut history) and n_cut are computed here, once, and written out.
  * home_sub: the account's most frequent of the 18 study subs in its cut history (blank if none).
  * every chunk of 500 accounts then goes through history.score (the frozen v7.1 rules and metrics), in-process.

Outputs: <out>/features.csv and features.pkl (hashed ids, every feature), <work>/cut_*.jsonl, groups_*.csv,
scores_*/ (usernames, private). Never prints a username.

Usage:
  python3 -I scripts/repull_run/feats.py --mode old    [--control-anchor last|matched] [--keep-removed] [--tag NAME]
  python3 -I scripts/repull_run/feats.py --mode repull --anchors <work>/anchors_private.csv [--tag NAME]
"""
import argparse, collections, contextlib, csv, glob, io, json, os, pickle, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
from socialscope import hijack, prewindow, history  # noqa: E402
import anchors as A  # noqa: E402

NUM = ["bot_score", "items", "comments", "subs", "longest_gap_days", "interval_cv", "share_gaps_under_60s", "farm_share",
       "self_repeat", "ai_style_share", "top_sub_share", "sub_spread", "threads_revisited", "top_level_share", "words_median",
       "words_cv", "quoted_share", "ai_vocab_share", "md_share", "sentence_cv", "state_media_links", "political_early", "political_late"]


def is_removed_comment(x):
    return "body" in x and "title" not in x and (x.get("body") or "").strip() in C.REMOVED


def text_clean(x):
    """Copy of a post with a removed selftext blanked; None for a removed comment."""
    if is_removed_comment(x):
        return None
    if "title" in x and (x.get("selftext") or "").strip() in C.REMOVED:
        y = dict(x)
        y["selftext"] = ""
        return y
    return x


def prewindow_features(items, anchor, exclude_removed=True):
    f = prewindow.compute_prewindow_features(items, anchor)
    earlier, window = prewindow.partition_history(items, anchor)
    rem = sum(1 for x in window if is_removed_comment(x) or ("title" in x and (x.get("selftext") or "").strip() in C.REMOVED))
    f["removed_share"] = round(rem / len(window), 6) if window else 0.0
    if exclude_removed:
        te = [y for y in (text_clean(x) for x in earlier) if y is not None]
        tw = [y for y in (text_clean(x) for x in window) if y is not None]
        f["median_length_ratio"] = round(prewindow.compute_median_length_ratio(te, tw), 6)
        f["link_share_change"] = round(prewindow.compute_link_share_change(te, tw), 6)
        f["short_comment_share"] = round(prewindow.compute_short_comment_share(tw), 6)
    return f


def history_paths(mode):
    if mode == "old":
        hp = [os.path.join(C.HIST_DIR, f"{n}_{k}.zip") for n in C.OLD_HIST for k in ("posts", "comments")]
        op = [os.path.join(C.HIST_DIR, f"{n}_oldest.json") for n in C.OLD_HIST]
    else:
        hp = sorted(glob.glob(os.path.join(C.PULL_DIR, "repull_*_posts.zip")) + glob.glob(os.path.join(C.PULL_DIR, "repull_*_comments.zip")))
        op = sorted(glob.glob(os.path.join(C.PULL_DIR, "repull_*_oldest.json"))) + [os.path.join(C.HIST_DIR, f"{n}_oldest.json") for n in C.OLD_HIST]
    missing = [p for p in hp if not os.path.exists(p)]
    if missing:
        sys.exit("missing history files: " + ", ".join(os.path.basename(m) for m in missing))
    if not hp:
        sys.exit(f"no histories found for mode {mode}")
    return hp, op


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["old", "repull"], required=True)
    ap.add_argument("--anchors", default=None, help="anchors_private.csv from pull.py (required for --mode repull)")
    ap.add_argument("--control-anchor", choices=["last", "matched"], default="last", help="old data only: control anchor rule")
    ap.add_argument("--keep-removed", action="store_true", help="old prewindow behaviour (removed bodies counted as text)")
    ap.add_argument("--groups", default=None, help="groups_private.csv (default <work>/groups_private.csv)")
    ap.add_argument("--tag", default=None, help="name for this feature set (default: <mode>_<control-anchor>)")
    ap.add_argument("--seed", type=int, default=20261105)
    a = ap.parse_args()
    C.ensure_dirs()
    tag = a.tag or (a.mode if a.mode == "repull" else f"old_{a.control_anchor}") + ("_keepremoved" if a.keep_removed else "")
    work = os.path.join(C.WORK, tag)
    os.makedirs(work, exist_ok=True)
    G = {r["username"]: r for r in C.read_groups(a.groups)}
    print(f"[{tag}] {len(G)} accounts in cohort file", flush=True)

    hp, op = history_paths(a.mode)
    items = C.load_histories(hp, set(G))
    oldest = C.load_oldest(op)
    print(f"[{tag}] histories loaded for {len(items)} accounts from {len(hp)} files; oldest known for {sum(1 for u in G if oldest.get(u) is not None)}", flush=True)

    # anchors
    anchors, anchor_src = {}, {}
    for u, g in G.items():
        if g["anchor_utc"]:
            anchors[u], anchor_src[u] = float(g["anchor_utc"]), "listing"
    if a.anchors or a.mode == "repull":
        if not a.anchors:
            sys.exit("--mode repull needs --anchors (the file pull.py wrote); the cut must match what was pulled")
        for r in csv.DictReader(open(a.anchors, encoding="utf-8")):
            if r["username"] in G and r["username"] not in anchors:
                anchors[r["username"]], anchor_src[r["username"]] = float(r["anchor_utc"]), r["anchor_src"]
    elif a.control_anchor == "matched":
        first = {u: (oldest.get(u) if oldest.get(u) is not None else (min(float(x["created_utc"]) for x in items[u].values()) if items.get(u) else None)) for u in G}
        last = {u: (max(float(x["created_utc"]) for x in items[u].values()) if items.get(u) else None) for u in G}
        for u, (ts, src) in A.assign_control_anchors(G, first, last, seed=a.seed).items():
            anchors[u], anchor_src[u] = ts, src
    for u in G:
        if u not in anchors:
            if items.get(u):
                anchors[u], anchor_src[u] = max(float(x["created_utc"]) for x in items[u].values()), "last_item"
    names = sorted(u for u in G if u in anchors and items.get(u))
    print(f"[{tag}] {len(names)} accounts with history and an anchor; anchor sources: "
          + ", ".join(f"{k} {v}" for k, v in sorted(collections.Counter(anchor_src[u] for u in names).items())), flush=True)

    # oldest file for history.score (usernames; private)
    old_path = os.path.join(work, "oldest_all.json")
    json.dump({u: oldest.get(u) for u in names}, open(old_path, "w"))
    K = (len(names) + 499) // 500
    F = {}
    for k in range(K):
        chunk = names[k * 500:(k + 1) * 500]
        cut_path, grp_path = os.path.join(work, f"cut_{k}.jsonl"), os.path.join(work, f"groups_{k}.csv")
        with open(cut_path, "w", encoding="utf-8") as fh, open(grp_path, "w", newline="", encoding="utf-8") as gh:
            gw = csv.writer(gh)
            gw.writerow(["username", "group", "reasons"])
            for u in chunk:
                anc = anchors[u]
                cut = [x for x in items[u].values() if float(x["created_utc"]) <= anc]
                for x in cut:
                    fh.write(json.dumps(x, ensure_ascii=False) + "\n")
                gw.writerow([u, G[u]["group"], ""])
                ct = sorted(float(x["created_utc"]) for x in cut)
                try:
                    pw = prewindow_features(cut, anc, exclude_removed=not a.keep_removed)
                except Exception:
                    pw = {}
                fe = oldest.get(u)
                insub = collections.Counter(str(x.get("subreddit") or "").lower() for x in cut if str(x.get("subreddit") or "").lower() in C.SUBS)
                F[C.H(u)] = dict(
                    group=G[u]["group"], cohort_source=G[u]["cohort_source"], flair=G[u]["flair"], anchor=anc, anchor_src=anchor_src[u],
                    n_cut=len(cut), n_posts=sum(1 for x in cut if "title" in x), n_comments=sum(1 for x in cut if "title" not in x),
                    n_total_pulled=len(items[u]), n_after_anchor=len(items[u]) - len(cut),
                    hist_age=(anc - ct[0]) / 86400 if ct else None,
                    aged=bool(len(cut) >= 100 and ct and ct[-1] - ct[0] >= 365 * 86400),
                    age_days=(anc - float(fe)) / 86400 if fe is not None else None,
                    sh=bool(hijack.solicit_handle(cut)), sb=bool(hijack.solicit_broad(cut)),
                    insub_items=sum(insub.values()), home_sub=insub.most_common(1)[0][0] if insub else "",
                    pw=pw)
        with contextlib.redirect_stdout(io.StringIO()):
            history.score([cut_path], groups=grp_path, out_dir=os.path.join(work, f"scores_{k}"), salt=C.salt(), oldest=old_path)
        print(f"[{tag}] chunk {k + 1}/{K} scored", flush=True)
    S = {}
    for k in range(K):
        for r in csv.DictReader(open(os.path.join(work, f"scores_{k}", "accounts.csv"), encoding="utf-8")):
            S[r["account"]] = r
    pwk = sorted({k for v in F.values() for k in v["pw"]})
    fl = lambda x: (float(x) if x not in (None, "") else None)
    rows = []
    for h, v in F.items():
        s = S.get(h)
        if not s:
            continue
        row = dict(account=h, group=v["group"], cohort_source=v["cohort_source"], flair=v["flair"], anchor_utc=round(v["anchor"]),
                   anchor_src=v["anchor_src"], n_cut=v["n_cut"], n_posts=v["n_posts"], n_comments=v["n_comments"],
                   n_total_pulled=v["n_total_pulled"], n_after_anchor=v["n_after_anchor"], hist_age=v["hist_age"], true_age=v["age_days"],
                   aged=int(v["aged"]), sh=int(v["sh"]), sb=int(v["sb"]), primary=int("primary" in (s["tier"] or "")),
                   tier=s["tier"], flag_list=s["flag_list"], insub_items=v["insub_items"], home_sub=v["home_sub"])
        for c in NUM:
            row[c] = fl(s.get(c))
        for c in pwk:
            row["pw_" + c] = v["pw"].get(c)
        rows.append(row)
    fields = list(rows[0]) if rows else []
    out_csv = os.path.join(C.OUT, f"features_{tag}.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: r["account"]))
    pickle.dump(dict(tag=tag, num=NUM, pwk=pwk, rows=rows), open(os.path.join(C.OUT, f"features_{tag}.pkl"), "wb"))
    cnt = collections.Counter(r["group"] for r in rows if r["n_cut"] > 0)
    print(f"[{tag}] wrote {out_csv}: " + ", ".join(f"{g} {cnt[g]}" for g in ("test_pos", "test_pending", "test_ctl", "train_pos", "train_ctl")), flush=True)


if __name__ == "__main__":
    main()
