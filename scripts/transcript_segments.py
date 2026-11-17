#!/usr/bin/env python3
"""Index the parts of video transcripts that matter for the anti-Western lexicon, with timestamps and checked quotes.

  python3 scripts/transcript_segments.py data/antiwest/transcripts/*.txt
  python3 scripts/transcript_segments.py data/antiwest/transcripts/NEW_ID.txt --model gemini-3.5-flash-lite
  python3 scripts/transcript_segments.py --add my_rows.csv     # hand-written rows: same columns, quotes get checked

For each transcript (as written by scripts/yt_gemini_transcript.py) it asks a Gemini text model for the passages
where a speaker (a) explains how to recognize a faction or tells factions apart, (b) states one of the talking points
in data/antiwest/talking_points.csv, or (c) argues against one. Each row gets the timestamp, a link that opens the
video at that second, the speaker, the talking-point ids, a one-sentence paraphrase and a short verbatim quote.

Every quote is then checked against the transcript text (case, punctuation and spacing ignored, same test as
scripts/transcript_chunks.py verify). quote_ok is 1 when the words are in the transcript within two minutes of the
timestamp, 0 when they are not; rows with 0 are kept so they can be fixed by hand, and should not be cited.

Rows are appended to data/antiwest/vod_segments.csv; a video already in the file is skipped unless --force.
One request per transcript. The transcript itself is a machine transcription, so quote_ok means "matches the
transcript", not "matches the video".
"""
import argparse, csv, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yt_gemini_transcript import call, LINE

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "antiwest")
COLS = ["video_id", "start", "url", "speaker", "kind", "talking_points", "summary", "quote", "quote_ok", "indexed_by"]

PROMPT = """Below is a timestamped transcript of a political commentary video. Find every passage that does one of:
- "identify": a speaker explains how to recognize socialists, communists, "tankies", "campists" or "leftists", says what
  defines them, or gives a test for telling them from liberals or progressives.
- "factions": a speaker separates factions of the left or right from each other, or describes how a faction organizes.
- "assert": a speaker states, as their own view, one of the talking points listed below (include people in played clips).
- "rebut": a speaker argues against one of the talking points listed below or against the people who hold it.

Return only a JSON list. Each item: {{"start": "HH:MM:SS" (the timestamp of the transcript line where it starts),
"speaker": name as written in the transcript, "kind": one of identify / factions / assert / rebut,
"talking_points": list of ids from the list below (empty list if none fits),
"summary": one plain sentence saying what the speaker claims, attributed ("Destiny argues that ..."),
"quote": 8 to 30 consecutive words copied exactly from that passage}}.
Aim for 12 to 25 items per hour of video, the ones a researcher would most want to find again, spread over the
whole transcript and not only its first minutes. Skip small talk and topics
unrelated to political factions, America's standing, or foreign states.

Talking points:
{points}

Transcript:
{text}"""


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def secs(ts):
    p = [int(x) for x in ts.split(":")]
    return p[-1] + 60 * p[-2] + (3600 * p[0] if len(p) == 3 else 0)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("transcripts", nargs="*")
    p.add_argument("--add", help="CSV of hand-written rows (video_id,start,speaker,kind,talking_points,summary,quote,indexed_by)")
    p.add_argument("--model", default="gemini-3.5-flash,gemini-3-flash-preview,gemini-4-hydrogen,gemini-3.5-flash-lite",
                   help="tried in order; the lite models find far fewer passages (4-7 per hour in a Nov 17 2026 test)")
    p.add_argument("-o", "--out", default=os.path.join(DATA, "vod_segments.csv"))
    p.add_argument("--force", action="store_true")
    a = p.parse_args()
    points = "\n".join("%s: %s" % (r["id"], r["claim"])
                       for r in csv.DictReader(open(os.path.join(DATA, "talking_points.csv"), encoding="utf-8")))
    ids = set(l.split(":")[0] for l in points.split("\n"))
    rows = list(csv.DictReader(open(a.out, encoding="utf-8"))) if os.path.exists(a.out) else []
    if a.add:
        tdir, cache, new = os.path.join(DATA, "transcripts"), {}, list(csv.DictReader(open(a.add, encoding="utf-8")))
        rows = [r for r in rows if not any(n["video_id"] == r["video_id"] and n["start"] == r["start"] for n in new)]
        for r in new:
            v, t = r["video_id"], secs(r["start"])
            if v not in cache:
                cache[v] = [(secs(l[1:9]), norm(l[10:])) for l in open(os.path.join(tdir, v + ".txt"), encoding="utf-8") if LINE.match(l)]
            q = norm(r["quote"])
            r["quote_ok"] = int(len(q.split()) >= 6 and q in " ".join(x for s, x in cache[v] if t - 120 <= s <= t + 120))
            r["url"] = "https://www.youtube.com/watch?v=%s&t=%ds" % (v, t)
            if not r["quote_ok"]:
                print("  quote not found:", v, r["start"], r["quote"][:70])
            rows.append({c: r.get(c, "") for c in COLS})
        print("added", len(new), "rows,", sum(r["quote_ok"] for r in new), "quotes verified")
    for path in a.transcripts:
        v = os.path.basename(path)[:-4]
        if any(r["video_id"] == v for r in rows) and not a.force:
            print(v, "already indexed, skipping"); continue
        lines = [l.rstrip("\n") for l in open(path, encoding="utf-8") if not l.startswith("#") and l.strip()]
        timed = [(secs(l[1:9]), norm(l[10:])) for l in lines if LINE.match(l)]
        try:
            text, _, model = call(a.model.split(","), [{"text": PROMPT.format(points=points, text="\n".join(lines))}],
                                  {"response_mime_type": "application/json", "max_output_tokens": 16384})
            items = json.loads(text)
        except Exception as e:
            print(v, "FAILED:", str(e)[:200]); continue
        rows = [r for r in rows if r["video_id"] != v]
        ok = 0
        for it in items:
            try:
                t = secs(it["start"])
            except Exception:
                continue
            q = norm(it.get("quote", ""))
            window = " ".join(x for s, x in timed if t - 120 <= s <= t + 120)
            good = int(len(q.split()) >= 6 and q in window)
            ok += good
            rows.append({"video_id": v, "start": it["start"], "url": "https://www.youtube.com/watch?v=%s&t=%ds" % (v, t),
                         "speaker": it.get("speaker", ""), "kind": it.get("kind", ""),
                         "talking_points": " ".join(x for x in it.get("talking_points", []) if x in ids),
                         "summary": it.get("summary", ""), "quote": it.get("quote", ""), "quote_ok": good, "indexed_by": model})
        print("%s: %d segments, %d quotes verified (%s)" % (v, len(items), ok, model))
    rows.sort(key=lambda r: (r["video_id"], secs(r["start"])))
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(rows)
    print("wrote", a.out, len(rows), "rows")


if __name__ == "__main__":
    main()
