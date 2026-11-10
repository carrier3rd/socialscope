#!/usr/bin/env python3
"""Compact one staged week of Arctic Shift comment pulls into a small npz.

Usage: python3 -I load_week.py <week_label> <staged_dir> <out_dir> <salt_file>

Keeps only: hashed author (sha256(salt+author), first 8 bytes as uint64),
created_utc, link_id (base36 -> uint64), subreddit code, comment id (base36).
Raw usernames never leave this function. Excludes [deleted]/[removed],
AutoModerator and names ending in "bot" (case-insensitive), and reports counts.
Deletes the staged zip/jsonl after processing.
"""
import sys, os, json, zipfile, hashlib, re, io
import numpy as np

SUBS = ["Asmongold", "atrioc", "Conservative", "Destiny", "dsa", "h3h3productions",
        "Hasan_Piker", "IsraelPalestine", "LeftoversH3", "LivestreamFail", "neoliberal",
        "Palestine", "PoliticalCompassMemes", "samharris", "TankieTheDeprogram",
        "thebulwark", "thedavidpakmanshow", "ukraine"]
SUBCODE = {s.lower(): i for i, s in enumerate(SUBS)}
BOT_RE = re.compile(r"bot$", re.I)
SERVICE = {"[deleted]", "[removed]", "automoderator"}


def b36(s):
    return int(s, 36)


def main():
    week, staged, out_dir, salt_file = sys.argv[1:5]
    with open(salt_file, "rb") as f:
        salt = f.read().strip()
    files = sorted(f for f in os.listdir(staged) if "_comments_" in f and (f.endswith(".zip") or f.endswith(".jsonl")))
    # prefer zip if both exist
    by_sub = {}
    for f in files:
        m = re.match(r"r_(.+?)_comments_", f)
        sub = m.group(1)
        if sub not in by_sub or f.endswith(".zip"):
            by_sub[sub] = f
    AH, T, LK, SC, CID = [], [], [], [], []
    excl = {"deleted": 0, "automod": 0, "botname": 0, "badjson": 0, "dupe": 0, "wrongsub": 0}
    coverage = {}
    seen = set()
    for sub, f in sorted(by_sub.items()):
        path = os.path.join(staged, f)
        if f.endswith(".zip"):
            zf = zipfile.ZipFile(path)
            name = [n for n in zf.namelist() if n.endswith(".jsonl")][0]
            fh = io.TextIOWrapper(zf.open(name), encoding="utf-8", errors="replace")
        else:
            fh = open(path, encoding="utf-8", errors="replace")
        n_ok = 0
        tmin, tmax = None, None
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                excl["badjson"] += 1
                continue
            a = d.get("author") or "[deleted]"
            al = a.lower()
            if al in ("[deleted]", "[removed]"):
                excl["deleted"] += 1
                continue
            if al == "automoderator":
                excl["automod"] += 1
                continue
            if BOT_RE.search(a):
                excl["botname"] += 1
                continue
            if (d.get("subreddit") or "").lower() != sub.lower():
                excl["wrongsub"] += 1
                continue
            cid = d.get("id")
            if cid in seen:
                excl["dupe"] += 1
                continue
            seen.add(cid)
            t = int(d["created_utc"])
            lk = d.get("link_id", "t3_0").split("_", 1)[-1]
            h = hashlib.sha256(salt + a.encode("utf-8")).digest()[:8]
            AH.append(int.from_bytes(h, "big"))
            T.append(t)
            LK.append(b36(lk))
            SC.append(SUBCODE[sub.lower()])
            CID.append(b36(cid))
            n_ok += 1
            tmin = t if tmin is None or t < tmin else tmin
            tmax = t if tmax is None or t > tmax else tmax
        fh.close()
        coverage[sub] = {"file": f, "kind": "zip" if f.endswith(".zip") else "jsonl_partial", "n": n_ok,
                         "tmin": tmin, "tmax": tmax}
        os.remove(path)
        print(f"{week} {sub:22s} {n_ok:7d} rows  {coverage[sub]['kind']}", file=sys.stderr)
    np.savez_compressed(os.path.join(out_dir, f"{week}.npz"),
                        ah=np.array(AH, dtype=np.uint64), t=np.array(T, dtype=np.int64),
                        link=np.array(LK, dtype=np.uint64), sub=np.array(SC, dtype=np.uint8),
                        cid=np.array(CID, dtype=np.uint64))
    with open(os.path.join(out_dir, f"{week}_meta.json"), "w") as f:
        json.dump({"week": week, "coverage": coverage, "excluded": excl}, f, indent=1)
    print(json.dumps(excl), file=sys.stderr)


if __name__ == "__main__":
    main()
