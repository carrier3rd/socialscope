import json, os, sys, math, csv, statistics as st
from collections import Counter
d = sys.argv[1]; outdir = sys.argv[2]
items = {j["item"]: j for j in (json.loads(l) for l in open(os.path.join(d, "items.jsonl")))}
R = {}
for l in open(os.path.join(d, "runs", "gemini_raw.jsonl")):
    r = json.loads(l)
    if r.get("label") in ("P", "A", "B", "N"): R[(r["cond"], r["run"], r["item"])] = r
L = []; P = lambda *x: L.append(" ".join(str(y) for y in x))
errs = sum(1 for l in open(os.path.join(d, "runs", "gemini_raw.jsonl")) if "error" in json.loads(l))
P("valid responses:", len(R), "of 600; error rows:", errs)
reply = [i for i in items if items[i]["parent"]]; top = [i for i in items if not items[i]["parent"]]
def lab(c, r, i): return R.get((c, r, i), {}).get("label")
def norm(dist):
    if not dist: return None
    s = sum(dist.values()); return {k: dist.get(k, 0) / s for k in "PABN"}
def wil(k, n, z=1.96):
    p = k / n; den = 1 + z*z/n; c = p + z*z/(2*n); h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)); return (c-h)/den, (c+h)/den
def rate(a, b, ids, name):
    ids = [i for i in ids if lab(*a, i) and lab(*b, i)]
    k = sum(lab(*a, i) != lab(*b, i) for i in ids); lo, hi = wil(k, len(ids))
    P(f"{name}: {k}/{len(ids)} = {k/len(ids):.1%} (95% CI {lo:.1%}-{hi:.1%})"); return k/len(ids)
g1 = rate(("C0",1), ("C1",1), reply, "G1 context flips, replies (C0r1 vs C1r1)")
rate(("C0",2), ("C1",2), reply, "   replicate (C0r2 vs C1r2)")
n0 = rate(("C0",1), ("C0",2), reply, "G2 rerun noise C0, replies"); n1 = rate(("C1",1), ("C1",2), reply, "G2 rerun noise C1, replies")
rate(("C0",1), ("C1",1), top, "   placebo top-level (C0r1 vs C1r1)")
def tv(i):
    a = norm(R.get(("C0",1,i), {}).get("dist")); b = norm(R.get(("C1",1,i), {}).get("dist"))
    return None if a is None or b is None else 0.5 * sum(abs(a[k]-b[k]) for k in "PABN")
def cxmi(i):
    y = lab("C1",1,i); a = R.get(("C0",1,i), {}).get("dist") or {}; b = R.get(("C1",1,i), {}).get("dist") or {}
    pa, pb = a.get(y, 1e-7), b.get(y, 1e-7)
    return math.log(pb) - math.log(max(pa, 1e-7))
tr = [tv(i) for i in reply if tv(i) is not None]; tt = [tv(i) for i in top if tv(i) is not None]
P(f"G3 median TV shift: replies {st.median(tr):.4f} (mean {st.mean(tr):.4f}, n {len(tr)}); placebo {st.median(tt):.4f} (mean {st.mean(tt):.4f}, n {len(tt)})")
P(f"   replies with TV shift > 0.5: {sum(x > 0.5 for x in tr)}; placebo: {sum(x > 0.5 for x in tt)}")
fl = [i for i in reply if lab("C0",1,i) and lab("C1",1,i) and lab("C0",1,i) != lab("C1",1,i)]
nf = [i for i in reply if lab("C0",1,i) and lab("C1",1,i) and lab("C0",1,i) == lab("C1",1,i)]
mf = st.mean(abs(cxmi(i)) for i in fl) if fl else float("nan"); mn = st.mean(abs(cxmi(i)) for i in nf)
P(f"G4 mean |P-CXMI|: flipped {mf:.2f} (n {len(fl)}), not flipped {mn:.2f} (n {len(nf)})")
P("   transitions:", dict(Counter(f"{lab('C0',1,i)}->{lab('C1',1,i)}" for i in fl)))
cl = {int(r["item"]): r["code"] for r in csv.DictReader(open(os.path.join(d, "runs", "C1_r1_codes.csv")))}
both = [i for i in items if lab("C1",1,i) and i in cl]
P(f"G5 Gemini vs Claude agreement, C1 run 1: {sum(lab('C1',1,i)==cl[i] for i in both)}/{len(both)} = {sum(lab('C1',1,i)==cl[i] for i in both)/len(both):.1%}")
for i in (301, 779):
    a = norm(R.get(("C0",1,i), {}).get("dist")); b = norm(R.get(("C1",1,i), {}).get("dist"))
    P(f"G6 item {i}: labels C0 {lab('C0',1,i)}/{lab('C0',2,i)} C1 {lab('C1',1,i)}/{lab('C1',2,i)}; p(P) C0 {a and round(a['P'],4)} -> C1 {b and round(b['P'],4)}")
uns = [i for i in reply if norm(R.get(("C0",1,i),{}).get("dist")) and max(norm(R[("C0",1,i)]["dist"]).values()) < 0.9 and lab("C1",1,i)]
con = [i for i in reply if norm(R.get(("C0",1,i),{}).get("dist")) and max(norm(R[("C0",1,i)]["dist"]).values()) >= 0.9 and lab("C1",1,i)]
fu = sum(lab("C0",1,i) != lab("C1",1,i) for i in uns); fc = sum(lab("C0",1,i) != lab("C1",1,i) for i in con)
P(f"G7 flips: unsure (<0.9) {fu}/{len(uns)}; confident {fc}/{len(con)}")
P("code mix:", {f"{c}r{r}": dict(Counter(R[(c,r,i)]["label"] for i in items if (c,r,i) in R)) for c in ("C0","C1") for r in (1,2)})
open(os.path.join(outdir, "gemini_analysis.txt"), "w").write("\n".join(L) + "\n"); print("\n".join(L))
