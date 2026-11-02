#!/usr/bin/env python3
"""Turn yt-dlp .vtt captions into Gemini-sized text chunks about US actions, and verify Gemini's quotes.

  chunk:  python3 scripts/transcript_chunks.py chunk ~/socialscope_data/transcripts -o ~/socialscope_data/gemini_chunks
          Cleans each .vtt (drops rolling-caption duplicates), keeps [mm:ss] marks every ~30 s, cuts ~1,500-word chunks,
          and keeps only chunks that mention the US / America / a US agency or official. Writes one .txt per chunk
          named <upload_date>_<channel>_<id>_<n>.txt, and bundles of 10 chunks per file for pasting/uploading.
  verify: python3 scripts/transcript_chunks.py verify gemini_out.csv ~/socialscope_data/gemini_chunks
          Checks every quote in Gemini's CSV (columns chunk,timestamp,action,valence,default,quote) appears in the named
          chunk (case and punctuation ignored). Prints the match rate and writes gemini_out_verified.csv.
"""
import argparse, csv, glob, os, re, sys

US = re.compile(r"\b(america|american|united states|the us\b|the u\.s\.|usa|pentagon|white house|cia|fbi|ice\b|"
                r"state department|trump|biden|hegseth|rubio|vance|congress|senate|us military|u\.s\. military|"
                r"washington|nato)\b", re.I)
TS = re.compile(r"^(\d\d):(\d\d):(\d\d)\.\d+ --> ")
TAG = re.compile(r"<[^>]+>")


def clean_vtt(path):
    out, last, t = [], "", 0
    for line in open(path, encoding="utf-8", errors="ignore"):
        m = TS.match(line)
        if m:
            t = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]); continue
        s = TAG.sub("", line).strip()
        if not s or s.startswith(("WEBVTT", "Kind:", "Language:")) or s == last:
            continue
        if last and s.startswith(last):  # rolling captions repeat the previous line
            s = s[len(last):].strip()
        last = TAG.sub("", line).strip()
        if s:
            out.append((t, s))
    return out


def chunk(a):
    os.makedirs(a.out, exist_ok=True)
    allf = sorted(glob.glob(os.path.join(a.src, "**", "*.vtt"), recursive=True))
    # yt-dlp writes several caption tracks per video (en, en-en, en-orig...). Keep one per video:
    # prefer en-orig (the original auto-captions), then en, then whatever else exists.
    rank = lambda f: (0 if ".en-orig." in f else 1 if re.search(r"\.en\.vtt$", f) else 2, f)
    pick = {}
    for f in allf:
        vid = os.path.basename(f).split(".")[0]
        if vid not in pick or rank(f) < rank(pick[vid]):
            pick[vid] = f
    files = [pick[v] for v in sorted(pick)]
    kept = []
    for f in files:
        base = os.path.basename(f).split(".")[0]
        lines = clean_vtt(f); words, buf, n, mark = 0, [], 0, -999
        def flush():
            nonlocal buf, words, n
            text = " ".join(buf)
            if US.search(text):
                name = f"{base}_{n:03d}"
                open(os.path.join(a.out, name + ".txt"), "w").write(text); kept.append((name, text))
            buf, words, n = [], 0, n + 1
        for t, s in lines:
            if t - mark >= 30:
                buf.append(f"[{t//60:02d}:{t%60:02d}]"); mark = t
            buf.append(s); words += len(s.split())
            if words >= a.words:
                flush()
        if buf:
            flush()
    for i in range(0, len(kept), a.bundle):
        with open(os.path.join(a.out, f"BUNDLE_{i//a.bundle+1:03d}.txt"), "w") as fh:
            for name, text in kept[i:i + a.bundle]:
                fh.write(f"=== CHUNK {name} ===\n{text}\n\n")
    print(f"{len(allf)} caption files, {len(files)} videos -> {len(kept)} chunks mentioning the US -> {-(-len(kept)//a.bundle)} bundles in {a.out}")


def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).split()


def verify(a):
    rows = list(csv.DictReader(open(a.csv, encoding="utf-8")))
    ok = 0
    for r in rows:
        q = norm(r.get("quote", "")); p = os.path.join(a.chunks, r.get("chunk", "") + ".txt")
        txt = " ".join(norm(open(p).read())) if os.path.exists(p) else ""
        r["verified"] = "yes" if q and q != ["no", "quote"] and " ".join(q) in txt else "no"
        ok += r["verified"] == "yes"
    out = a.csv.replace(".csv", "_verified.csv")
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"{ok}/{len(rows)} quotes found verbatim ({100*ok/max(1,len(rows)):.0f}%) -> {out}")


ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
c = sub.add_parser("chunk"); c.add_argument("src"); c.add_argument("-o", "--out", required=True)
c.add_argument("--words", type=int, default=1500); c.add_argument("--bundle", type=int, default=10)
v = sub.add_parser("verify"); v.add_argument("csv"); v.add_argument("chunks")
a = ap.parse_args(); chunk(a) if a.cmd == "chunk" else verify(a)
