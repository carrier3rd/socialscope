#!/usr/bin/env python3
"""Talking-point detection v2: meaning-based clusters of comments across subs (replaces exact 8-word matching).

Method (after Hanley & Durumeric 2025, adapted; see docs/research-methods.md and docs/talking-points-v2-predictions.md):
  1. Comments with 12+ words after removing quoted lines, URLs and markdown; mods, AutoModerator, *bot accounts and
     [deleted]/[removed] dropped; one copy per account of any exact text.
  2. Sentence embeddings (default sentence-transformers/all-mpnet-base-v2, L2-normalised), 20 nearest neighbours per
     comment within the same week by exact blocked cosine (numpy).
  3. Leader clustering (DP-means style): comments in time order; an unassigned comment opens a cluster and takes every
     unassigned neighbour with cosine >= --threshold.
  4. Kept as a talking point only if: 3+ distinct accounts, 2+ subs, no account supplies over half the comments, no single
     thread supplies over half (Hanley's single-source rule), and the comments do not share a verbatim 10-word span in
     over half of them (that marks a shared quote or copypasta; those go to a separate quotes file).
Outputs (accounts hashed with the project salt, never names): <out>/clusters_<week>.csv and gemini_sample.txt (150 random
kept clusters, 3 redacted examples each) for blind labelling.

  pip install sentence-transformers
  python3 scripts/tp_embed.py --weeks aug18=<dir> sep08=<dir> ... --out ~/socialscope_data/tp_v2
"""
import argparse, collections, csv, glob, hashlib, io, json, os, random, re, sys, zipfile
import numpy as np

URL = re.compile(r"https?://\S+|\[([^\]]*)\]\([^)]*\)")
MD = re.compile(r"[*_~`#>|]")
WORD = re.compile(r"[a-z0-9']+")


def rows(d):
    for f in sorted(glob.glob(os.path.join(d, "**", "*comments*"), recursive=True)):
        if f.endswith(".zip"):
            z = zipfile.ZipFile(f)
            srcs = [z.open(n) for n in z.namelist() if n.endswith((".jsonl", ".json"))]
        elif f.endswith(".jsonl"):
            if os.path.exists(f[:-6] + ".zip"):
                continue  # the zip has the same data
            srcs = [open(f, "rb")]
        else:
            continue
        for fh in srcs:
            for l in fh:
                try:
                    yield json.loads(l)
                except Exception:
                    pass


def clean(b):
    b = "\n".join(x for x in (b or "").split("\n") if not x.lstrip().startswith(">"))
    b = URL.sub(lambda m: m.group(1) or " ", b)
    return " ".join(MD.sub(" ", b).split())


def load(d, skip_subs):
    out, seen = [], set()
    for r in rows(d):
        a = r.get("author") or ""
        s = r.get("subreddit") or ""
        if (not a or a in ("[deleted]", "AutoModerator") or a.lower().endswith("bot") or s.lower() in skip_subs
                or r.get("distinguished") in ("moderator", "admin")):
            continue
        t = clean(r.get("body"))
        if len(t.split()) < 12 or t in ("[deleted]", "[removed]"):
            continue
        k = (a, t)
        if k in seen or r.get("id") in seen:
            continue
        seen.add(k); seen.add(r.get("id"))
        out.append(dict(id=r.get("id"), a=a, s=s, t=float(r.get("created_utc") or 0), link=r.get("link_id"), text=t))
    return out


def shared_span(texts, n=10):
    grams = collections.Counter()
    for t in texts:
        w = WORD.findall(t.lower())
        grams.update({" ".join(w[i:i + n]) for i in range(len(w) - n + 1)})
    return max(grams.values()) / len(texts) if grams else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weeks", nargs="+", required=True, help="label=dir (dirs searched recursively; several dirs per label allowed with commas)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="sentence-transformers/all-mpnet-base-v2")
    ap.add_argument("--threshold", type=float, default=0.80)
    ap.add_argument("--k", type=int, default=20)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--skip-subs", default="h3snark")
    ap.add_argument("--salt-file", default=".socialscope_salt")
    ap.add_argument("--fake", action="store_true", help="random embeddings, for testing the pipeline only")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    salt = open(a.salt_file).read().strip() if os.path.exists(a.salt_file) else "socialscope"
    H = lambda x: "acct_" + hashlib.sha256((salt + x).encode()).hexdigest()[:10]
    model = None
    if not a.fake:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(a.model)
    skip = {s.strip().lower() for s in a.skip_subs.split(",") if s.strip()}
    sample_pool = []
    for spec in a.weeks:
        label, _, dirs = spec.partition("=")
        data = []
        for d in dirs.split(","):
            data += load(os.path.expanduser(d), skip)
        data.sort(key=lambda r: r["t"])
        n = len(data)
        print(f"[{label}] {n} comments", flush=True)
        if n < 2:
            continue
        if a.fake:
            E = np.random.default_rng(0).standard_normal((n, 64)).astype("float32")
        elif os.path.exists(os.path.join(a.out, f"emb_{label}.npy")) and len(np.load(os.path.join(a.out, f"emb_{label}.npy"), mmap_mode="r")) == n:
            E = np.load(os.path.join(a.out, f"emb_{label}.npy")).astype("float32")  # cached: rerun with another --threshold is fast
        else:
            E = model.encode([r["text"] for r in data], batch_size=a.batch, show_progress_bar=True,
                             convert_to_numpy=True, normalize_embeddings=True).astype("float32")
            np.save(os.path.join(a.out, f"emb_{label}.npy"), E.astype("float16"))
        E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-12
        kk = min(a.k + 1, n); D = np.zeros((n, kk), "float32"); I = np.zeros((n, kk), "int64")
        for s0 in range(0, n, 512):  # exact top-k by blocked matrix product (no faiss needed)
            S = E[s0:s0 + 512] @ E.T
            np.negative(S, out=S); top = np.argpartition(S, kk - 1, axis=1)[:, :kk]; np.negative(S, out=S)
            vals = np.take_along_axis(S, top, 1); o = np.argsort(-vals, 1)
            I[s0:s0 + 512] = np.take_along_axis(top, o, 1); D[s0:s0 + 512] = np.take_along_axis(vals, o, 1)
        assigned = np.full(n, -1); cid = 0
        for i in range(n):
            if assigned[i] >= 0:
                continue
            assigned[i] = cid
            for sim, j in zip(D[i], I[i]):
                if j != i and j >= 0 and sim >= a.threshold and assigned[j] < 0:
                    assigned[j] = cid
            cid += 1
        groups = collections.defaultdict(list)
        for i, c in enumerate(assigned):
            groups[c].append(i)
        kept, quotes = [], []
        for c, ids in groups.items():
            if len(ids) < 3:
                continue
            rs = [data[i] for i in ids]
            acc = collections.Counter(r["a"] for r in rs); thr = collections.Counter(r["link"] for r in rs)
            subs = {r["s"] for r in rs}
            if len(acc) < 3 or len(subs) < 2 or acc.most_common(1)[0][1] > len(rs) / 2 or thr.most_common(1)[0][1] > len(rs) / 2:
                continue
            firsts = {}
            for r in rs:
                firsts.setdefault(r["s"], r["t"])
            order = sorted(firsts, key=firsts.get)
            rec = dict(week=label, cluster=c, n_comments=len(rs), n_accounts=len(acc), n_subs=len(subs),
                       order=" > ".join(order), first_sub=order[0], first_utc=int(rs[0]["t"]),
                       span_hours=round((rs[-1]["t"] - rs[0]["t"]) / 3600, 1),
                       first_account=H(rs[0]["a"]),
                       examples=" || ".join(re.sub(r"/?u/[A-Za-z0-9_-]+", "u/[user]", r["text"])[:280] for r in rs[:3]))
            (quotes if shared_span([r["text"] for r in rs]) > 0.5 else kept).append(rec)
        for name, L in (("clusters", kept), ("quotes", quotes)):
            with open(os.path.join(a.out, f"{name}_{label}_t{a.threshold:.2f}.csv"), "w", newline="", encoding="utf-8") as fh:
                if L:
                    w = csv.DictWriter(fh, fieldnames=list(L[0])); w.writeheader(); w.writerows(L)
        print(f"[{label}] {len(groups)} raw groups -> {len(kept)} talking-point clusters, {len(quotes)} quote/copypasta clusters", flush=True)
        sample_pool += kept
        del E, D, I
    rnd = random.Random(1102)
    samp = rnd.sample(sample_pool, min(150, len(sample_pool)))
    with open(os.path.join(a.out, f"gemini_sample_t{a.threshold:.2f}.txt"), "w", encoding="utf-8") as fh:
        for n, r in enumerate(samp):
            fh.write(f"CLUSTER {n}\n" + "".join(f"- {e}\n" for e in r["examples"].split(" || ")) + "\n")
    with open(os.path.join(a.out, f"gemini_sample_key_t{a.threshold:.2f}.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["sample", "week", "cluster"])
        w.writerows([(n, r["week"], r["cluster"]) for n, r in enumerate(samp)])
    print(f"wrote {len(samp)} sampled clusters for Gemini to {a.out}/gemini_sample.txt")


if __name__ == "__main__":
    main()
