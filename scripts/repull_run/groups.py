#!/usr/bin/env python3
"""Rebuild the in-sub cohorts (train_pos, test_pos, test_pending, train_ctl, test_ctl) with listing dates.

Same rules as scripts/insub_run/build.py, reconstructed from what the laptop holds (the cloud session's
groups.csv files, bbinv/private_all.csv, bbnov/private_nov.csv and seen_all.pkl are not here):

  inventory   latest Bot Bouncer verdict per account from every r/BotBouncer posts pull under reddit_pulls/bb_*/
              (scripts/bb_inventory.build_inventory, latest created_utc wins). build.py used an inventory through
              Oct 28 plus the Nov pull; the laptop has Jul 1-Aug 31, Sep 1-Oct 19 and Oct 28-Nov 2. Listings from
              Oct 20-27 are MISSING until the gap pull in RUNBOOK step 1 exists; this script says how many
              accounts that affects and refuses to write a cohort file unless --allow-gap is given.
  insub list  users_to_pull_insub.txt (480): banned -> test_pos, pending -> test_pending, anchor = listed_utc.
              build.py read the verdict as of Oct 28 (flair_oct28); here it is the verdict at each pull's capture
              (Oct 29 for the Sep-Oct pull, Nov 2 for the Nov pull, today for the gap pull). flair_source says which.
  train list  users_to_pull_train.txt: accounts with no listing at all are the 1,000 random in-sub accounts;
              hash parity splits them (odd -> test_ctl, even -> train_ctl). The list also holds ~995 sitewide bans
              and ~214 organic verdicts, which only the inventory can separate from the random accounts; with the
              Oct 20-27 listings missing about 100 of them would pass as random. As a check, each candidate is
              tested for activity in the 18 subs during Oct 20-26 (how the random accounts were drawn).
  panels      users_to_pull_{augpanel,septest,round4}.txt. screen.shortlist writes each group as a sorted block
              (shortlist, control, known_bot), and the panel builders did the same (bots, then controls), so the
              block boundaries recover the group column: augpanel [32 bots, 1000 controls], septest [53 later
              bots, 17 known bots, 400 controls], round4 [300 shortlist, 300 controls, 17 known bots]. The script
              checks those block lengths and stops if they differ. Rule as in build.py: listed banned -> train_pos
              (anchor = listed_utc); unlisted and in a control block -> train_ctl. build.py also required the
              account to be in seen_all.pkl (seen in the six pulled weeks); every panel account was drawn from a
              pulled week's activity, so that holds by construction and is not re-checked here.
  first wins  an account in several lists keeps its first assignment, in the order insub, train, augpanel,
              septest, round4 (build.py's order).

Writes <data>/repull/work/groups_private.csv (usernames; stays on the laptop) and <data>/repull/out/groups_summary.md
(counts only). Prints counts next to the documented ones. Never prints a username.

Usage: python3 -I scripts/repull_run/groups.py [--allow-gap] [--skip-random-check]
"""
import argparse, collections, csv, glob, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C

sys.path.insert(0, os.path.join(C.REPO, "scripts"))
import bb_inventory as bi  # noqa: E402

GAP_START, GAP_END = "2026-10-20", "2026-10-28"   # listings build.py had that the laptop lacks (end exclusive)
PANEL_BLOCKS = {"augpanel": [("bot", 32), ("control", 1000)],
                "septest": [("later_bot", 53), ("known_bot", 17), ("control", 400)],
                "round4": [("shortlist", 300), ("control", 300), ("known_bot", 17)]}


def sorted_blocks(names):
    """Lengths of maximal runs where the list is in ascending order (how screen.shortlist wrote the groups)."""
    runs, start = [], 0
    for i in range(1, len(names) + 1):
        if i == len(names) or names[i] < names[i - 1]:
            runs.append(i - start)
            start = i
    return runs


def file_dates(path):
    m = re.search(r"(\d{4}-\d\d-\d\d)_to_(\d{4}-\d\d-\d\d)", os.path.basename(path))
    return (m.group(1), m.group(2)) if m else (None, None)


def build_inventory(files):
    """lowercase name -> (flair, listed_utc, source). Latest listing wins across files, as bb_inventory does."""
    inv = {}
    for f in sorted(files):
        latest, _ = bi.build_inventory(bi.iter_records([f]))
        tag = os.path.basename(os.path.dirname(os.path.dirname(f))) or os.path.basename(f)
        for key, (_u, flair, ts) in latest.items():
            if key not in inv or ts >= inv[key][1]:
                inv[key] = (flair, ts, tag)
    return inv


def random_activity_check(candidates):
    """Which candidate random accounts have an item in the 18 subs during Oct 20-26 (ET) in their pulled history."""
    from socialscope import arctic
    t0, t1 = arctic.to_ts("2026-10-20"), arctic.to_ts("2026-10-27")
    hit = set()
    cand = set(candidates)
    for kind in ("posts", "comments"):
        p = os.path.join(C.HIST_DIR, f"train_{kind}.zip")
        if not os.path.exists(p):
            return None
        for r in C.iter_jsonl(p):
            a = r.get("author")
            if a in cand and a not in hit:
                try:
                    ts = float(r.get("created_utc") or 0)
                except (TypeError, ValueError):
                    continue
                if t0 <= ts < t1 and str(r.get("subreddit") or "").lower() in C.SUBS:
                    hit.add(a)
    return hit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-gap", action="store_true", help="write the cohort file even if the Oct 20-27 Bot Bouncer pull is missing "
                    "(random controls are then limited to accounts with an in-sub item Oct 20-26; the ~27 insub and ~10 panel accounts listed in the gap stay out)")
    ap.add_argument("--skip-random-check", action="store_true", help="skip the Oct 20-26 in-sub activity check on random candidates")
    ap.add_argument("--out", default=None, help="private cohort csv (default <data>/repull/work/groups_private.csv)")
    a = ap.parse_args()
    C.ensure_dirs()
    out_path = a.out or os.path.join(C.WORK, "groups_private.csv")
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    files = sorted(glob.glob(C.BB_GLOB))
    if not files:
        sys.exit(f"no Bot Bouncer pulls found under {C.BB_GLOB}")
    spans = [file_dates(f) for f in files]
    say("Bot Bouncer pulls: " + ", ".join(f"{s}..{e}" for s, e in spans))
    gap_covered = any(s and s <= GAP_START and e >= "2026-10-27" for s, e in spans)
    inv = build_inventory(files)
    say(f"inventory: {len(inv):,} accounts, " + ", ".join(f"{k} {v}" for k, v in sorted(collections.Counter(v[0] for v in inv.values()).items())))
    if not gap_covered:
        say(f"WARNING: no pull covers {GAP_START}..2026-10-27. Accounts listed in that window look unlisted here. "
            f"Run RUNBOOK step 1 (reddit_pull.py --subs BotBouncer --kinds posts --start {GAP_START} --end {GAP_END}).")

    lists = {k: C.read_names(p) for k, p in C.LISTS.items() if os.path.exists(p)}
    for k in C.LISTS:
        if k not in lists:
            sys.exit(f"missing cohort list {k}: {C.LISTS[k]}")
    G = {}      # username -> dict(group, anchor_utc, flair, listed_utc, flair_source, cohort_source, panel_role)

    def put(u, group, anchor, flair, listed, src, cohort, role):
        if u in G:
            return
        G[u] = dict(username=u, group=group, anchor_utc=anchor, flair=flair, listed_utc=listed, flair_source=src,
                    cohort_source=cohort, panel_role=role)

    # 1. in-sub fresh listings (test side)
    c = collections.Counter()
    for u in lists["insub"]:
        v = inv.get(u.lower())
        if not v:
            c["not_in_inventory"] += 1
            continue
        flair, ts, src = v
        c[flair] += 1
        g = "test_pos" if flair == "banned" else "test_pending" if flair == "pending" else None
        if g:
            put(u, g, float(ts), flair, ts, src, "insub", "")
    say(f"insub list ({len(lists['insub'])}): " + ", ".join(f"{k} {v}" for k, v in sorted(c.items()))
        + "  [documented as of Oct 28: banned 190, pending 264, unflaired 22, purged 4]")

    # 2. random in-sub controls from the train list
    cand = [u for u in lists["train"] if u.lower() not in inv]
    listed = collections.Counter(inv[u.lower()][0] for u in lists["train"] if u.lower() in inv)
    say(f"train list ({len(lists['train'])}): listed " + ", ".join(f"{k} {v}" for k, v in sorted(listed.items()))
        + f"; unlisted (random candidates) {len(cand)}  [documented: 995 banned, 214 organic, 1,000 random]")
    active = None if a.skip_random_check else random_activity_check(cand)
    if active is not None:
        say(f"  random candidates with an in-sub item Oct 20-26 in their pulled history: {len(active)} of {len(cand)}")
        if len(cand) - len(active) > 20 and not gap_covered:
            say("  -> the excess over ~1,000 is almost certainly sitewide listings from the missing Oct 20-27 pull")
    dropped = 0
    for u in cand:
        if not gap_covered and active is not None and u not in active:
            dropped += 1   # substitute rule while the gap pull is missing: a random account must show the activity it was drawn for
            continue
        put(u, "test_ctl" if C.hash_parity(u) else "train_ctl", None, "", "", "", "train_random", "")
    if dropped:
        say(f"  dropped {dropped} unlisted train-list accounts with no in-sub Oct 20-26 item (stand-in for the missing listings)")

    # 3. earlier in-sub panels (train side)
    for panel in ("augpanel", "septest", "round4"):
        names = lists[panel]
        want = [n for _, n in PANEL_BLOCKS[panel]]
        got = sorted_blocks(names)
        if got != want:
            sys.exit(f"{panel}: expected sorted blocks {want}, found {got}; cannot recover the group column")
        role, i = {}, 0
        for r, n in PANEL_BLOCKS[panel]:
            for u in names[i:i + n]:
                role[u] = r
            i += n
        pc = collections.Counter()
        for u in names:
            v = inv.get(u.lower())
            if v and v[0] == "banned":
                put(u, "train_pos", float(v[1]), v[0], v[1], v[2], panel, role[u]); pc["train_pos"] += 1
            elif not v and role[u] == "control":
                put(u, "train_ctl", None, "", "", "", panel, role[u]); pc["train_ctl"] += 1
            elif v:
                pc[f"listed_{v[0]}_dropped"] += 1
            else:
                pc[f"unlisted_{role[u]}_dropped"] += 1
        say(f"{panel} ({len(names)}; blocks {got}): " + ", ".join(f"{k} {v}" for k, v in sorted(pc.items())))

    counts = collections.Counter(v["group"] for v in G.values())
    say("")
    say("cohorts (before dropping accounts without history; documented counts are accounts with history):")
    for g in ("test_pos", "test_pending", "test_ctl", "train_pos", "train_ctl"):
        say(f"  {g:13s} {counts[g]:5d}   documented {C.DOCUMENTED[g]}")
    src = collections.Counter((v["group"], v["flair_source"]) for v in G.values() if v["flair_source"])
    say("listing source per positive group: " + ", ".join(f"{g}/{s} {n}" for (g, s), n in sorted(src.items())))
    if not gap_covered and not a.allow_gap:
        say("")
        say("NOT written: the Oct 20-27 Bot Bouncer pull is missing (see WARNING). Re-run with --allow-gap to write anyway.")
        open(os.path.join(C.OUT, "groups_summary.md"), "w").write("# Cohort rebuild (dry run, gap pull missing)\n\n```\n" + "\n".join(lines) + "\n```\n")
        sys.exit(2)
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["username", "group", "anchor_utc", "flair", "listed_utc", "flair_source", "cohort_source", "panel_role"])
        w.writeheader()
        for u in sorted(G):
            w.writerow(G[u])
    say(f"wrote {out_path} ({len(G)} accounts; private, usernames)")
    open(os.path.join(C.OUT, "groups_summary.md"), "w").write("# Cohort rebuild\n\n```\n" + "\n".join(lines) + "\n```\n")


if __name__ == "__main__":
    main()
