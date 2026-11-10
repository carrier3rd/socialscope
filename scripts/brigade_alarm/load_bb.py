#!/usr/bin/env python3
"""Hash r/BotBouncer ban-list posts into a set of hashed account ids.

Usage: python3 -I load_bb.py <out_npz> <salt_file> <zip> [<zip> ...]
Only posts flaired 'banned' count. Usernames are hashed on load and never printed.
"""
import sys, os, json, zipfile, hashlib, io, re
from collections import Counter
import numpy as np

out, salt_file = sys.argv[1:3]
salt = open(salt_file, "rb").read().strip()
flairs = Counter()
banned = set()
for zp in sys.argv[3:]:
    zf = zipfile.ZipFile(zp)
    for name in zf.namelist():
        if not name.endswith(".jsonl"):
            continue
        for line in io.TextIOWrapper(zf.open(name), encoding="utf-8", errors="replace"):
            try:
                d = json.loads(line)
            except Exception:
                continue
            fl = (d.get("link_flair_text") or "").lower()
            flairs[fl] += 1
            m = re.match(r"Overview for (\S+)", d.get("title") or "")
            if not m:
                flairs["_notitle"] += 1
                continue
            if fl == "banned":
                h = hashlib.sha256(salt + m.group(1).encode("utf-8")).digest()[:8]
                banned.add(int.from_bytes(h, "big"))
    os.remove(zp)
np.save(out, np.array(sorted(banned), dtype=np.uint64))
print("flairs:", dict(flairs.most_common(8)), "banned accounts:", len(banned))
