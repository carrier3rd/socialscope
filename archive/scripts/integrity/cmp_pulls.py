"""Compare two pulls of the same sub and week record by record (laptop session, Nov 11 2026).

Usage: python3 -I scripts/integrity/cmp_pulls.py <old.zip> <new.zip>
Matches records by id. Prints counts and key names only (no text, no usernames): records only in one copy,
identical records, which keys differ, and the rarest sets of differing keys (where a flipped value shows up,
as opposed to fields that change between pulls, such as score).
"""
import collections, json, sys, zipfile


def load(p):
    out = {}
    with zipfile.ZipFile(p) as z:
        for m in z.namelist():
            for line in z.open(m):
                if line.strip():
                    d = json.loads(line); out[d["id"]] = d
    return out


old, new = load(sys.argv[1]), load(sys.argv[2])
both = old.keys() & new.keys()
print(f"old {len(old):,} records, new {len(new):,}; only old {len(old.keys() - new.keys()):,}, "
      f"only new {len(new.keys() - old.keys()):,}")
same = 0; diffkeys = collections.Counter(); shapes = collections.Counter()
for i in both:
    a, b = old[i], new[i]
    if a == b: same += 1; continue
    ks = tuple(sorted(k for k in a.keys() | b.keys() if a.get(k, "<missing>") != b.get(k, "<missing>")))
    diffkeys.update(ks); shapes[ks] += 1
print(f"shared {len(both):,}: identical {same:,}, different {sum(shapes.values()):,}")
for k, n in diffkeys.most_common(15): print(f"  key {k!r}: differs in {n:,}")
print("rarest sets of differing keys:")
for ks, n in sorted(shapes.items(), key=lambda x: x[1])[:12]: print(f"  {n:>6,} x {list(ks)}")
