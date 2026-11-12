import csv, json, os, sys, math
from collections import Counter
d = sys.argv[1]; out = sys.argv[2]
items = {str(j["item"]): j for j in (json.loads(l) for l in open(os.path.join(d, "items.jsonl")))}
def load(name):
    r = {}
    with open(os.path.join(d, "runs", name + "_codes.csv"), newline="") as f:
        for row in csv.DictReader(f):
            k = {kk.strip().lower(): (v or "").strip() for kk, v in row.items() if kk}
            try: r[k["item"]] = (k.get("view", "").lower(), k["code"].upper())
            except (KeyError, ValueError): pass
    return r
runs = {n: load(n) for n in ("C0_r1", "C0_r2", "C1_r1", "C1_r2")}
reply = [i for i, j in items.items() if j["parent"]]
top = [i for i, j in items.items() if not j["parent"]]
def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k / n; den = 1 + z*z/n; c = p + z*z/(2*n); h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return ((c-h)/den, (c+h)/den)
def rate(a, b, ids):
    ids = [i for i in ids if i in runs[a] and i in runs[b]]
    k = sum(runs[a][i][1] != runs[b][i][1] for i in ids)
    lo, hi = wilson(k, len(ids)); return k, len(ids), k/len(ids) if ids else 0, lo, hi
L = []; P = lambda *x: L.append(" ".join(str(y) for y in x))
P("coverage:", {n: len(r) for n, r in runs.items()}, "codes:", {n: dict(Counter(c for _, c in r.values())) for n, r in runs.items()})
res = {}
for lab, a, b, ids in (("context_reply", "C0_r1", "C1_r1", reply), ("context_reply_r2", "C0_r2", "C1_r2", reply),
                       ("rerun_C0_reply", "C0_r1", "C0_r2", reply), ("rerun_C1_reply", "C1_r1", "C1_r2", reply),
                       ("placebo_top", "C0_r1", "C1_r1", top), ("rerun_C0_top", "C0_r1", "C0_r2", top)):
    k, n, p, lo, hi = rate(a, b, ids); res[lab] = p
    P(f"{lab}: {k}/{n} = {p:.1%} (95% CI {lo:.1%}-{hi:.1%})")
noise = (res["rerun_C0_reply"] + res["rerun_C1_reply"]) / 2
P(f"context-attributable (primary minus mean rerun): {100*(res['context_reply']-noise):.1f} points")
# robust flips: stable within both conditions and different across
st = [i for i in reply if all(i in runs[n] for n in runs) and runs["C0_r1"][i][1] == runs["C0_r2"][i][1] and runs["C1_r1"][i][1] == runs["C1_r2"][i][1]]
rob = [i for i in st if runs["C0_r1"][i][1] != runs["C1_r1"][i][1]]
P(f"stable-in-both items: {len(st)}; robust context flips among them: {len(rob)} ({len(rob)/max(1,len(st)):.1%})")
flips = [i for i in reply if i in runs["C0_r1"] and i in runs["C1_r1"] and runs["C0_r1"][i][1] != runs["C1_r1"][i][1]]
tr = Counter(f"{runs['C0_r1'][i][1]}->{runs['C1_r1'][i][1]}" for i in flips)
P("transitions (C0r1->C1r1):", dict(tr.most_common()))
pol = set(os.environ.get("POLAR_LABELS", "P,A,B").split(","))
n2p = sum(1 for i in flips if runs["C0_r1"][i][1] == "N" and runs["C1_r1"][i][1] in pol)
p2n = sum(1 for i in flips if runs["C0_r1"][i][1] in pol and runs["C1_r1"][i][1] == "N")
cross = sum(1 for i in flips if {runs["C0_r1"][i][1], runs["C1_r1"][i][1]} == {"P", "A"})
P(f"N->polar {n2p}, polar->N {p2n}, ratio {n2p/max(1,p2n):.2f}; cross-polar P<->A {cross} ({cross/max(1,len(flips)):.0%} of flips)")
trob = Counter(f"{runs['C0_r1'][i][1]}->{runs['C1_r1'][i][1]}" for i in rob); P("robust-flip transitions:", dict(trob))
def sub(pred, name):
    g = [i for i in reply if pred(items[i])]; h = [i for i in reply if not pred(items[i])]
    fg = sum(i in flips for i in g); fh = sum(i in flips for i in h)
    P(f"{name}: yes {fg}/{len(g)} = {fg/max(1,len(g)):.0%}; no {fh}/{len(h)} = {fh/max(1,len(h)):.0%}")
sub(lambda j: j["comment_has_quote"], "has '>' quote")
sub(lambda j: len(j["comment"]) >= 597, "comment truncated at cap")
sub(lambda j: j["parent_truncated"], "parent truncated")
sub(lambda j: len(j["comment"].split()) < 20, "comment < 20 words")
for s in ("Ukraine", "Israel", "Hasan"): sub(lambda j, s=s: j["subject"] == s, f"subject {s}")
e0 = sum(runs["C0_r1"].get(i, ("", ""))[0] == "echo" for i in reply); e1 = sum(runs["C1_r1"].get(i, ("", ""))[0] == "echo" for i in reply)
P(f"VIEW=echo on replies: C0r1 {e0}, C1r1 {e1}")
open(os.path.join(out, "analysis.txt"), "w").write("\n".join(L) + "\n")
json.dump({"flips": flips, "robust": rob}, open(os.path.join(d, "flip_ids.json"), "w"))
print("\n".join(L))
