"""Record-level check of pulled week zips (laptop session, Nov 11 2026; see docs/ram-fault-checks.md).

Usage: python3 -I scripts/integrity/week_records.py <zip> [<zip> ...]
Zip names must look like r_<sub>_<posts|comments>_<start>_to_<end>.zip.

A zip CRC only proves the file hasn't changed since it was written; a bit flipped in RAM before writing passes.
This reads each zip with O_DIRECT (disk, not the page cache), parses every JSON line and flags: bad JSON;
created_utc missing or outside the week +-2/3 days; subreddit not matching the file name; malformed id; and
key names outside the file's usual keys that are one or two characters off a usual key (e.g. "areated_utc").
A CRC error while decompressing (RAM corrupting this process's copy) is retried up to 4 times.
Prints file names, key names and counts only (no usernames, no text).
"""
import collections, datetime as dt, io, json, mmap, os, re, sys, zipfile

ID = re.compile(r"^[a-z0-9]{4,14}$")


def direct_bytes(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECT)
    size = os.fstat(fd).st_size; bs = 1 << 20
    buf = mmap.mmap(-1, bs); out = bytearray()
    try:
        while True:
            n = os.readv(fd, [buf])
            if n <= 0: break
            out += buf[:n]
            if n < bs: break
    finally:
        os.close(fd)
    return bytes(out[:size])


tot = collections.Counter(); flagged = 0
for z in sorted(sys.argv[1:]):
    name = os.path.basename(z)
    m = re.match(r"r_(.+)_(posts|comments)_(\d{4}-\d\d-\d\d)_to_(\d{4}-\d\d-\d\d)\.zip", name)
    sub = m[1].lower()
    lo = dt.datetime.fromisoformat(m[3]).replace(tzinfo=dt.timezone.utc).timestamp() - 2 * 86400
    hi = dt.datetime.fromisoformat(m[4]).replace(tzinfo=dt.timezone.utc).timestamp() + 3 * 86400
    for attempt in range(4):
        c = collections.Counter(); keysets = collections.Counter()
        try:
            with zipfile.ZipFile(io.BytesIO(direct_bytes(z))) as zf:
                for member in zf.namelist():
                    for line in zf.open(member):
                        if not line.strip(): continue
                        c["lines"] += 1
                        try: d = json.loads(line)
                        except Exception: c["bad_json"] += 1; continue
                        keysets[frozenset(d)] += 1
                        t = d.get("created_utc")
                        if not isinstance(t, (int, float)) or not lo <= float(t) <= hi: c["bad_time"] += 1
                        if str(d.get("subreddit", "")).lower() != sub: c["bad_sub"] += 1
                        if not ID.match(str(d.get("id", ""))): c["bad_id"] += 1
            if attempt: print(f"  {name}: read ok on try {attempt + 1}")
            break
        except zipfile.BadZipFile:
            print(f"  {name}: CRC error in memory on try {attempt + 1}")
    else:
        c["unreadable"] += 1
    known = set().union(*[k for k, n in keysets.items() if n >= 3]) if keysets else set()
    for k, n in keysets.items():
        for key in k - known:
            if any(len(key) == len(kn) and sum(a != b for a, b in zip(key, kn)) <= 2 for kn in known):
                c["flipped_key"] += n; print(f"  {name}: key {key!r} x{n}")
    bad = sum(v for k, v in c.items() if k != "lines")
    tot.update(c); flagged += bool(bad)
    if bad: print(f"FLAG {name}: " + ", ".join(f"{k}={v}" for k, v in c.items() if k != "lines"))
print(f"files {len(sys.argv) - 1}, flagged {flagged}; totals: " + ", ".join(f"{k}={v}" for k, v in sorted(tot.items())))
