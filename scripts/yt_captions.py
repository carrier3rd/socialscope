#!/usr/bin/env python3
"""YouTube captions with yt-dlp, for the laptop. This is the reliable route; run it there, not in the cloud session.

Why the laptop: YouTube answers cloud servers with "Sign in to confirm you're not a bot" (tested Nov 17 2026 from the
cloud session with youtube.com allowed), and the transcript sites want a logged-in browser. A home connection is not
blocked. scripts/yt_gemini_transcript.py is the cloud fallback and is limited by the Gemini quota.

  list a channel's recent uploads (videos and past live streams) into a CSV:
    python3 scripts/yt_captions.py list https://www.youtube.com/@destiny --since 2026-08-17
  fetch captions for given videos, or for everything in the queue / channel list not yet on disk:
    python3 scripts/yt_captions.py fetch DGs4Nq4dOEw NEF0VNPZ7lU
    python3 scripts/yt_captions.py fetch --from data/antiwest/vod_queue.csv
    python3 scripts/yt_captions.py fetch --from data/antiwest/vod_channel.csv --match "tankie|leftis|hasan|china|america"

Output matches the Gemini script so every other tool reads both: data/antiwest/transcripts/<id>.txt with "# key: value"
header lines, then "[HH:MM:SS] text" lines about every 30 seconds, and a row in transcripts/index.csv.

Differences from the Gemini transcripts:
  - The words are YouTube's captions (creator-uploaded when they exist, otherwise auto-generated), so nothing is
    invented or skipped, and the whole video is always covered.
  - No speaker labels. In a reaction video the streamer and the clip run together.
  - A transcript already on disk is kept unless --force. Gemini transcripts are replaced only with --force; the
    header's "source" line says which kind a file is.

Needs: pip install -U yt-dlp (keep it current; YouTube changes often). If YouTube asks for a sign-in even at home, add
--cookies-from-browser firefox (or chrome). The list command reads each video's page for its date, so a channel with
hundreds of uploads takes a few minutes; it stops at the first video older than --since.
"""
import argparse, csv, datetime, glob, html, os, re, subprocess, sys, tempfile, time

TS = re.compile(r"^(\d\d):(\d\d):(\d\d)\.\d+ --> ")
TAG = re.compile(r"<[^>]+>")


def clean_vtt(path):
    """Same cleaning as scripts/transcript_chunks.py (which cannot be imported: it parses arguments on import)."""
    out, last, t = [], "", 0
    for line in open(path, encoding="utf-8", errors="ignore"):
        m = TS.match(line)
        if m:
            t = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]); continue
        # Fixed Nov 16 2026 (laptop session): YouTube's VTT escapes text ("[&nbsp;__&nbsp;]", "&gt;&gt;", "&amp;"),
        # which was copied into the transcripts as-is. Unescape after stripping tags.
        s = html.unescape(TAG.sub("", line)).replace("\xa0", " ").strip()
        if not s or s.startswith(("WEBVTT", "Kind:", "Language:")) or s == last:
            continue
        if last and s.startswith(last):  # rolling captions repeat the previous line
            s = s[len(last):].strip()
        last = html.unescape(TAG.sub("", line)).replace("\xa0", " ").strip()
        if s:
            out.append((t, s))
    return out

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "antiwest")
COLS = ["id", "url", "title", "channel", "duration_s", "segments_ok", "segments_total", "words", "fetched", "model", "note"]


def hms(s):
    s = int(s)
    return "%02d:%02d:%02d" % (s // 3600, s % 3600 // 60, s % 60)


def vid(x):
    m = re.search(r"(?:v=|youtu\.be/|/live/|/shorts/|/embed/)([\w-]{11})", x)
    return m.group(1) if m else x.strip()


def ytdlp(args, extra):
    return subprocess.run(["yt-dlp", "--no-warnings"] + extra + args, capture_output=True, text=True)


def lines_from_vtt(path, every=30):
    """Caption fragments -> one line per `every` seconds, stamped with the time of its first words."""
    out, start, buf = [], None, []
    for t, s in clean_vtt(path):
        if start is None:
            start = t
        if t - start >= every and buf:
            out.append("[%s] %s" % (hms(start), " ".join(buf))); start, buf = t, []
        buf.append(s)
    if buf:
        out.append("[%s] %s" % (hms(start), " ".join(buf)))
    return out


def write(v, meta, lines, out, kind):
    today = datetime.date.today().isoformat()
    dur = int(float(meta.get("duration") or 0))
    head = ["# id: " + v, "# url: https://www.youtube.com/watch?v=" + v, "# title: " + meta.get("title", ""),
            "# channel: " + meta.get("channel", ""), "# uploaded: " + meta.get("upload_date", ""),
            "# duration: " + hms(dur),
            "# source: YouTube %s captions via yt-dlp, fetched %s; no speaker labels" % (kind, today), ""]
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, v + ".txt"), "w", encoding="utf-8").write("\n".join(head + lines) + "\n")
    idx = os.path.join(out, "index.csv")
    rows = list(csv.DictReader(open(idx, encoding="utf-8"))) if os.path.exists(idx) else []
    words = sum(len(l.split()) - 1 for l in lines)
    rows = [r for r in rows if r["id"] != v] + [dict(zip(COLS, [v, "https://www.youtube.com/watch?v=" + v,
            meta.get("title", ""), meta.get("channel", ""), dur, 1, 1, words, today, "yt-dlp %s captions" % kind,
            "uploaded " + meta.get("upload_date", "")]))]
    with open(idx, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLS, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print("%s  %s  %d words (%s captions)  %s" % (v, hms(dur), words, kind, meta.get("title", "")[:60]), flush=True)


def fetch(a):
    ids = [vid(x) for x in a.videos]
    if a.source:
        pat = re.compile(a.match, re.I) if a.match else None
        for r in csv.DictReader(open(a.source, encoding="utf-8")):
            title = r.get("title") or r.get("title_from_search") or ""
            if not pat or pat.search(title):
                ids.append(r.get("video_id") or r.get("id"))
    extra = ["--cookies-from-browser", a.cookies_from_browser] if a.cookies_from_browser else []
    failed = []
    for v in dict.fromkeys(i for i in ids if i):
        dest = os.path.join(a.out, v + ".txt")
        if os.path.exists(dest) and not a.force:
            print(v, "already on disk, skipping (--force to replace)"); continue
        with tempfile.TemporaryDirectory() as tmp:
            # Fixed Nov 16 2026 (laptop session): back-to-back fetches got "HTTP Error 429: Too Many Requests" on the
            # subtitle download and the video was just marked failed. Now sleeps between subtitle requests and
            # retries a 429 up to 3 times with a growing wait.
            for attempt in range(4):
                r = ytdlp(["--skip-download", "--write-subs", "--write-auto-subs", "--sub-langs", "en.*,-live_chat",
                           "--sub-format", "vtt", "--sleep-subtitles", "3", "-o", os.path.join(tmp, "%(id)s"),
                           "--print", "after_video:%(title)s\t%(channel)s\t%(upload_date)s\t%(duration)s\t%(subtitles)s",
                           "https://www.youtube.com/watch?v=" + v], extra)
                if "429" not in r.stderr or attempt == 3:
                    break
                print(v, "HTTP 429, waiting %ds and retrying" % (60 * (attempt + 1)), flush=True)
                time.sleep(60 * (attempt + 1))
            vtts = sorted(glob.glob(os.path.join(tmp, "*.vtt")), key=lambda p: ("-orig" not in p, len(p)))
            if r.returncode or not vtts:
                why = (r.stderr.strip().splitlines() or ["no English captions on this video"])[-1][:160]
                print(v, "FAILED:", why); failed.append((v, why)); continue
            f = (r.stdout.strip().splitlines() or [""])[-1].split("\t") + [""] * 5
            meta = {"title": f[0], "channel": f[1], "upload_date": f[2], "duration": f[3]}
            kind = "creator" if "'en" in f[4] else "auto-generated"   # %(subtitles)s lists creator tracks only
            write(v, meta, lines_from_vtt(vtts[0]), a.out, kind)
    if failed:
        print("\n%d failed:" % len(failed)); [print(" ", v, w) for v, w in failed]


def listing(a):
    since = a.since.replace("-", "")
    extra = ["--cookies-from-browser", a.cookies_from_browser] if a.cookies_from_browser else []
    rows = {}
    for tab in ("videos", "streams"):
        r = ytdlp(["--skip-download", "--dateafter", since, "--break-on-reject", "--ignore-errors",
                   "--print", "%(id)s\t%(upload_date)s\t%(duration)s\t%(title)s",
                   a.channel.rstrip("/") + "/" + tab], extra)
        for l in r.stdout.splitlines():
            p = l.split("\t")
            if len(p) == 4:
                rows[p[0]] = {"video_id": p[0], "uploaded": p[1], "duration_s": p[2], "title": p[3], "tab": tab}
        if not r.stdout.strip():
            print(tab, "tab: nothing listed.", (r.stderr.strip().splitlines() or [""])[-1][:160])
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["video_id", "uploaded", "duration_s", "title", "tab"]); w.writeheader()
        w.writerows(sorted(rows.values(), key=lambda r: r["uploaded"], reverse=True))
    hours = sum(float(r["duration_s"] or 0) for r in rows.values()) / 3600
    print("%d uploads since %s, %.0f hours -> %s" % (len(rows), a.since, hours, a.out))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch"); f.add_argument("videos", nargs="*")
    f.add_argument("--from", dest="source", help="CSV with a video_id (or id) column: vod_queue.csv, vod_channel.csv")
    f.add_argument("--match", help="with --from: only titles matching this regex")
    f.add_argument("-o", "--out", default=os.path.join(DATA, "transcripts"))
    f.add_argument("--force", action="store_true")
    l = sub.add_parser("list"); l.add_argument("channel"); l.add_argument("--since", required=True, help="YYYY-MM-DD")
    l.add_argument("-o", "--out", default=os.path.join(DATA, "vod_channel.csv"))
    for s in (f, l):
        s.add_argument("--cookies-from-browser", help="e.g. firefox; only if YouTube asks for a sign-in")
    a = p.parse_args()
    # Fixed Nov 16 2026 (laptop session): on Windows the console is cp1252, so titles printed as "Shill � Get" and
    # a title with an emoji would raise UnicodeEncodeError mid-run. Files were always written as UTF-8.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass
    fetch(a) if a.cmd == "fetch" else listing(a)
