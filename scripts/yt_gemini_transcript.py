#!/usr/bin/env python3
"""Timestamped YouTube transcripts through the Gemini API, for sessions that cannot reach YouTube.

Gemini fetches the video on Google's side, so this works in the cloud session where yt-dlp, youtube.com and the
transcript sites are all blocked. On the laptop, prefer yt-dlp captions (scripts/transcript_chunks.py reads those):
they are YouTube's own captions, while these are a model's transcription of the audio.

  python3 scripts/yt_gemini_transcript.py VIDEO_ID_OR_URL [more ...] -o data/antiwest/transcripts
  python3 scripts/yt_gemini_transcript.py VIDEO_ID --minutes 15 --duration 4998 --workers 6   # length known: parallel
  python3 scripts/yt_gemini_transcript.py VIDEO_ID --fill      # retry only the ranges marked MISSING

Per video it writes <out>/<id>.txt:
  a "# key: value" header (id, url, title, channel, duration, model, fetched date), then lines of
  [HH:MM:SS] SPEAKER: text
and appends/updates a row in <out>/index.csv (id,url,title,channel,duration_s,segments_ok,segments_total,words,fetched).

The video is read in --minutes long segments (startOffset/endOffset), because one call cannot return a whole VOD.
Segments run in order until one ends well short of its window, which is taken as the end of the video (pass
--duration SECONDS to skip that guess and run segments in parallel). A segment that fails is recorded as a
"# MISSING hh:mm:ss-hh:mm:ss" line, never guessed; --fill retries it later.

Quota (found Nov 17 2026): the project's Gemini key is on the free tier, 20 requests per model per day. One request
is one segment, so a 90-minute video at --minutes 30 costs 4 requests (3 segments + 1 for the title). --model takes a
comma-separated list and moves to the next model when one runs out for the day. Only gemini-3.5-flash has been
reliable: on Nov 17 2026 gemini-3-flash-preview / gemini-4-hydrogen got one 50-minute video right, then stopped a
long debate at 00:03:01 and cut another video at 00:08:29, so they are not in the default list. Check the last
timestamp of any transcript against the video's real length. Videos that are private, members-only or
age-restricted return HTTP 403 and cannot be read this way (3 of 14 tried).

Limits to state whenever these transcripts are used:
  - Machine transcription. Names and numbers can be wrong; speaker labels are the model's guess from voice and context.
    Check a quote against the video at its timestamp before publishing it.
  - Reaction videos mix the streamer with the clip being played. The model marks clips as "CLIP (name)" when it can
    tell, and does not always get it right.
  - Auth: the key comes from GEMINI_API_KEY; in the cloud session the proxy injects it and any dummy value works.
"""
import argparse, concurrent.futures as cf, csv, datetime, json, os, re, sys, time, urllib.request, urllib.error

API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
LINE = re.compile(r"^[*_>\- ]*\[(?:(\d{1,2}):)?(\d{1,2}):(\d\d)\][*_ ]*(.+)$")   # [HH:MM:SS] or [MM:SS], markdown tolerated
MISSING = re.compile(r"^# MISSING (\d\d):(\d\d):(\d\d)-(\d\d):(\d\d):(\d\d)")
SPENT = set()   # models whose daily quota is gone

META_PROMPT = ("This is the first two minutes of a video. Return only JSON with keys: title (the video's title if "
               "shown or stated, else a short neutral description), channel (the channel or main speaker), speakers "
               "(list of names of people speaking, best guess), kind (one of: solo, conversation, debate, reaction, panel).")

SEG_PROMPT = """Transcribe the speech in this video segment, which runs from {a} to {b} of the full video.

Rules:
- Verbatim. Keep the speaker's actual words, including false starts that matter to meaning. Drop filler like "um".
- One line per speaker turn or per roughly 20-30 seconds, whichever comes first, in exactly this form:
  [HH:MM:SS] SPEAKER: text
- Timestamps are absolute positions in the full video (this segment starts at {a}), not positions within the segment.
- SPEAKER is the person's name when it is clear from the video (known speakers: {speakers}); otherwise SPEAKER 1,
  SPEAKER 2. When the host plays a clip, video or reads a post aloud, label it CLIP (name of who is speaking in it) or
  READING (source).
- Do not summarize, comment, translate or add headings. Do not invent speech: if a stretch is silent, music or
  unintelligible, write a line like [HH:MM:SS] [music] or [HH:MM:SS] [inaudible].
- If the video ends before {b}, stop at the last words spoken. If this segment lies wholly beyond the end of the
  video, output exactly: END"""


class Denied(Exception):
    pass


def hms(s):
    s = int(s)
    return "%02d:%02d:%02d" % (s // 3600, s % 3600 // 60, s % 60)


def vid(x):
    m = re.search(r"(?:v=|youtu\.be/|/live/|/shorts/|/embed/)([\w-]{11})", x)
    return m.group(1) if m else x.strip()


def call(models, parts, cfg=None, tries=5, timeout=900):
    """Try each model in turn. Returns (text, finish_reason, model). Raises Denied on 403, RuntimeError otherwise."""
    body = json.dumps({"contents": [{"parts": parts}],
                       "generationConfig": dict({"temperature": 0}, **(cfg or {}))}).encode()
    err = "all models out of quota for today"
    for model in [m for m in models if m not in SPENT]:
        for i in range(tries):
            req = urllib.request.Request(API.format(model=model), body,
                                         {"content-type": "application/json",
                                          "x-goog-api-key": os.environ.get("GEMINI_API_KEY", "proxy-injected")})
            try:
                d = json.load(urllib.request.urlopen(req, timeout=timeout))
                c = d.get("candidates") or [{}]
                text = "".join(p.get("text", "") for p in c[0].get("content", {}).get("parts", []))
                if text.strip():
                    return text, c[0].get("finishReason", ""), model
                err = "empty response (%s)" % (c[0].get("finishReason") or d.get("promptFeedback"))
            except urllib.error.HTTPError as e:
                msg = e.read().decode("utf-8", "ignore")
                err = "HTTP %s %s" % (e.code, re.sub(r"\s+", " ", msg)[:160])
                if e.code == 403:
                    raise Denied(err)
                if e.code == 429 and "per day" in msg:
                    SPENT.add(model); print("  %s: daily quota used up" % model, file=sys.stderr); break
                if e.code in (400, 404):
                    break
            except Exception as e:  # timeouts, resets
                err = repr(e)
            time.sleep(min(90, 10 * 2 ** i))
    raise RuntimeError(err)


def video_part(v, a, b):
    return {"file_data": {"file_uri": "https://www.youtube.com/watch?v=" + v},
            "video_metadata": {"start_offset": "%ds" % a, "end_offset": "%ds" % b}}


def one(v, a, speakers, seg, depth=0):
    """Transcribe one (start, end) range. Returns (seg, lines or None, note)."""
    s, e = seg
    try:
        text, fin, model = call(a.models, [video_part(v, s, e),
                                           {"text": SEG_PROMPT.format(a=hms(s), b=hms(e), speakers=speakers)}],
                                {"max_output_tokens": 65536, "media_resolution": "MEDIA_RESOLUTION_LOW"})
    except Exception as ex:
        return seg, None, str(ex)
    lines, recent = [], []
    for ln in text.splitlines():
        m = LINE.match(ln.strip())
        if not m:
            continue
        t = int(m[1] or 0) * 3600 + int(m[2]) * 60 + int(m[3])
        if t < s - 5 and t <= e - s + 5:   # model gave segment-relative times; shift to absolute
            t += s
        if s - 5 <= t <= e + 30 and m[4] not in recent:   # a looping model repeats a line; keep the first copy only
            lines.append("[%s] %s" % (hms(t), m[4]))
            recent = (recent + [m[4]])[-5:]
    if not lines and text.strip() != "END":
        os.makedirs(a.out, exist_ok=True)   # keep what the model said, so the failure can be read
        open(os.path.join(a.out, "%s_%d.raw" % (v, s)), "w", encoding="utf-8").write(text)   # .raw is gitignored
        return seg, None, "no parseable lines (finish %s, %s)" % (fin, model)
    if fin == "MAX_TOKENS" and lines and depth < 4 and s + 60 < last_t(lines) < e - 60:
        # The model ran out of output before the end of the window (seen Nov 17 2026: a 30-minute window cut at
        # 05:07). The last line is cut mid-sentence, so drop it and ask again from its timestamp.
        t = last_t(lines)
        _, more, note = one(v, a, speakers, (t, e), depth + 1)
        if more is None:
            return seg, lines, "transcribed to %s only: %s" % (hms(t), note[:80])
        return seg, lines[:-1] + more, note
    return seg, lines, "cut at the model's output limit" if fin == "MAX_TOKENS" else ""


def last_t(lines):
    m = LINE.match(lines[-1])
    return int(m[1] or 0) * 3600 + int(m[2]) * 60 + int(m[3])


def fill(v, a):
    """Retry only the '# MISSING' ranges of an existing transcript and splice them in."""
    out = os.path.join(a.out, v + ".txt")
    old = open(out, encoding="utf-8").read().split("\n")
    sp = next((l[12:] for l in old if l.startswith("# speakers: ")), "unknown")
    new, left = [], 0
    for l in old:
        m = MISSING.match(l)
        if not m:
            new.append(l); continue
        g = [int(x) for x in m.groups()]
        seg = (g[0] * 3600 + g[1] * 60 + g[2], g[3] * 3600 + g[4] * 60 + g[5])
        _, lines, note = one(v, a, sp, seg)
        if lines is None:
            new.append("# MISSING %s-%s (%s)" % (hms(seg[0]), hms(seg[1]), note[:120])); left += 1
        else:
            new += lines
    open(out, "w", encoding="utf-8").write("\n".join(new))
    print(v, "filled;", left, "ranges still missing")


def fetch(v, a):
    out = os.path.join(a.out, v + ".txt")
    if os.path.exists(out) and a.fill:
        return fill(v, a)
    if os.path.exists(out) and not a.force:
        print(v, "exists, skipping (use --force, or --fill to retry missing ranges)"); return
    step, meta = a.minutes * 60, {}
    # first segment before the title request: a 403 here means the video cannot be read at all
    first = one(v, a, "unknown", (0, step))
    if first[1] is None:
        print(v, "FAILED:", first[2]); return first[2]
    try:
        t, _, _ = call(a.models, [video_part(v, 0, 120), {"text": META_PROMPT}],
                       {"response_mime_type": "application/json", "media_resolution": "MEDIA_RESOLUTION_LOW"})
        meta = json.loads(t)
        meta = meta[0] if isinstance(meta, list) else meta
    except Exception as e:
        print(v, "title request failed:", e)
    speakers = ", ".join(meta.get("speakers") or []) or "unknown"
    res = [first]
    if a.duration:
        segs = [(s, min(s + step, a.duration)) for s in range(step, a.duration, step)]
        with cf.ThreadPoolExecutor(a.workers) as ex:
            res += sorted(ex.map(lambda g: one(v, a, speakers, g), segs))
    else:
        s = step
        while res[-1][1] and last_t(res[-1][1]) > s - 150 and s < 12 * 3600:   # previous window was full: keep going
            res.append(one(v, a, speakers, (s, s + step)))
            if res[-1][1] is None and (len(SPENT) == len(a.models) or "HTTP 400" in res[-1][2]):
                if "HTTP 400" in res[-1][2]:
                    res.pop()      # asked for a range past the end
                break
            s += step
        if res[-1][1] == []:
            res.pop()              # model answered END
    dur = a.duration or max([last_t(l) for _, l, _ in res if l] or [0])
    ok = sum(1 for _, l, _ in res if l is not None)
    body, words = [], 0
    for (s, e), lines, note in res:
        if lines is None:
            body.append("# MISSING %s-%s (%s)" % (hms(s), hms(e), note[:120]))
        else:
            if note:
                body.append("# NOTE %s-%s %s" % (hms(s), hms(e), note))
            body += lines
            words += sum(len(l.split()) - 1 for l in lines)
    stopped = not a.duration and res[-1][1] is None
    today = datetime.date.today().isoformat()
    head = ["# id: " + v, "# url: https://www.youtube.com/watch?v=" + v, "# title: " + str(meta.get("title", "")),
            "# channel: " + str(meta.get("channel", "")), "# kind: " + str(meta.get("kind", "")),
            "# speakers: " + speakers,
            "# duration: " + hms(dur) + (" (transcribed so far; stopped early, the video may run longer)" if stopped
                                         else "" if a.duration else " (time of the last line transcribed)"),
            "# source: machine transcript by %s from the video audio, fetched %s; unverified, check quotes against the video"
            % ("/".join(a.models), today),
            "# segments: %d of %d transcribed" % (ok, len(res)), ""]
    os.makedirs(a.out, exist_ok=True)
    open(out, "w", encoding="utf-8").write("\n".join(head + body) + "\n")
    idx = os.path.join(a.out, "index.csv")
    rows = list(csv.DictReader(open(idx, encoding="utf-8"))) if os.path.exists(idx) else []
    cols = ["id", "url", "title", "channel", "duration_s", "segments_ok", "segments_total", "words", "fetched",
            "model", "note"]   # note is filled in by hand (what the video is, known defects)
    rows = [r for r in rows if r["id"] != v] + [dict(zip(cols, [v, "https://www.youtube.com/watch?v=" + v,
            meta.get("title", ""), meta.get("channel", ""), dur, ok, len(res), words, today, "/".join(a.models), ""]))]
    with open(idx, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print("%s  %s  %d/%d segments, %d words -> %s" % (v, hms(dur), ok, len(res), words, out), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("videos", nargs="+")
    p.add_argument("-o", "--out", default="data/antiwest/transcripts")
    p.add_argument("--model", default="gemini-3.5-flash",
                   help="comma-separated; the next one is used when a model's daily quota runs out (see Quota above)")
    p.add_argument("--minutes", type=int, default=30, help="segment length")
    p.add_argument("--workers", type=int, default=4, help="parallel segments, only with --duration")
    p.add_argument("--duration", type=int, help="video length in seconds, if known")
    p.add_argument("--force", action="store_true")
    p.add_argument("--fill", action="store_true", help="retry only the MISSING ranges of transcripts already on disk")
    a = p.parse_args()
    a.models = a.model.split(",")
    for x in a.videos:
        fetch(vid(x), a)
        if len(SPENT) == len(a.models):
            print("All models are out of quota for today; stopping. Remaining videos were not attempted."); break
