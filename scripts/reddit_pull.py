#!/usr/bin/env python3
"""
reddit_pull.py - download subreddit posts and comments from Arctic Shift for a date range,
zip them, and save them into your Google Drive folder.

Runs anywhere with plain Python 3.8+ (no installs needed), including Google Colab on a phone.

Examples
  # one week, six subs, posts and comments, saved into Google Drive
  python3 reddit_pull.py --subs LivestreamFail h3h3productions Destiny Hasan_Piker atrioc h3snark \
      --start 2026-10-06 --end 2026-10-13

  # Bot Bouncer listings (posts only) for the calibration study
  python3 reddit_pull.py --subs BotBouncer --kinds posts --start 2026-09-01 --end 2026-10-27

Dates are in Eastern time; --end is exclusive (2026-10-13 means "through Oct 12").

Where files go
  By default the script looks for your Google Drive for desktop folder ("My Drive") and saves into
  My Drive/reddit_pulls/<start>_to_<end>/. Install Google Drive for desktop and sign in first, or pass
  --out with any folder. Each sub and kind becomes one zip, e.g. r_Destiny_comments_2026-10-06_to_2026-10-12.zip,
  which the social-coordination skill reads directly.

Re-running the same command resumes where it stopped, so an interrupted pull doesn't start over.
"""
import argparse, glob, json, os, platform, sys, time, urllib.error, urllib.parse, urllib.request, zipfile
from datetime import datetime, timedelta, timezone

API = "https://arctic-shift.photon-reddit.com/api/{kind}/search"
ET = timezone(timedelta(hours=-4))  # EDT; good enough for day boundaries in Mar-Nov
# Only the fields the analysis uses: keeps files about a tenth of full size.
FIELDS = {
    "posts": "id,author,author_fullname,subreddit,created_utc,title,selftext,url,url_overridden_by_dest,domain,"
             "score,num_comments,link_flair_text,distinguished,removed_by_category,crosspost_parent_list,"
             "permalink,over_18,stickied",
    "comments": "id,author,author_fullname,subreddit,created_utc,body,link_id,parent_id,score,distinguished,permalink",
}


def find_drive():
    home = os.path.expanduser("~")
    candidates = []
    if platform.system() == "Darwin":
        candidates += glob.glob(os.path.join(home, "Library", "CloudStorage", "GoogleDrive-*", "My Drive"))
    if platform.system() == "Windows":
        for letter in "GHIJKLMNOPQRSTUVWXYZ":
            candidates.append(f"{letter}:\\My Drive")
    candidates += [os.path.join(home, "Google Drive", "My Drive"), os.path.join(home, "Google Drive"),
                   os.path.join(home, "My Drive")]
    for c in candidates:
        if os.path.isdir(c):
            return c
    return None


class BadRequest(Exception):
    pass


# The API's exact parameter rules aren't fully documented, so the first request tries a few request
# styles and remembers the one the server accepts.
STYLE = {}


def _iso(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _variants(kind, sub, after, before, fields):
    base = {"subreddit": sub, "sort": "asc"}
    for dates in ("epoch", "iso"):
        for lim in (100, "auto"):
            for use_fields in ((True, False) if fields else (False,)):
                q = dict(base, limit=lim)
                q["after"] = int(after) if dates == "epoch" else _iso(after)
                q["before"] = int(before) if dates == "epoch" else _iso(before)
                if use_fields:
                    q["fields"] = fields
                yield (dates, lim, use_fields), q


def _get(url, tries=6):
    delay = 2
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "reddit_pull/1.1 (research)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode("utf-8"))
            if isinstance(data, dict) and data.get("error"):
                raise BadRequest(str(data["error"]))
            return data.get("data", data) if isinstance(data, dict) else data
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            if e.code in (400, 404, 422):
                raise BadRequest(f"{e.code}: {body}")
            if attempt == tries - 1:
                raise
            print(f"    retrying in {delay}s ({e.code} {body[:80]})", flush=True)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if attempt == tries - 1:
                raise
            print(f"    retrying in {delay}s ({e})", flush=True)
        time.sleep(delay)
        delay = min(delay * 2, 60)


def fetch(kind, sub, after, before, fields, tries=6):
    key = kind
    errors = []
    for style, q in _variants(kind, sub, after, before, fields):
        if key in STYLE and style != STYLE[key]:
            continue
        url = API.format(kind=kind) + "?" + urllib.parse.urlencode(q)
        try:
            data = _get(url, tries)
            if key not in STYLE:
                STYLE[key] = style
                print(f"  ({kind}: server accepted dates={style[0]}, limit={style[1]}, "
                      f"fields={'trimmed' if style[2] else 'all'})", flush=True)
            return data
        except BadRequest as e:
            errors.append(f"{style}: {e}")
            if key in STYLE:
                raise
    raise BadRequest("every request style was refused:\n      " + "\n      ".join(errors))


def pull(kind, sub, start, end, path, fields, pause):
    """Append everything in [start, end) to path as JSON lines, resuming from the last line if present."""
    after, seen_at_edge, count = start, set(), 0
    if os.path.exists(path):
        last_t, edge, good, broken = None, set(), [], False
        with open(path, "rb") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    broken = True  # a half-written last line from an interrupted run
                    continue
                good.append(line)
                count += 1
                t = int(float(rec["created_utc"]))
                edge = edge | {rec["id"]} if t == last_t else {rec["id"]}
                last_t = t
        if broken:
            with open(path, "wb") as fh:
                fh.writelines(good)
        if last_t is not None:
            after, seen_at_edge = last_t, edge
            print(f"  resuming {os.path.basename(path)} at {datetime.fromtimestamp(after, ET):%Y-%m-%d %H:%M} ({count} so far)")
    with open(path, "a", encoding="utf-8") as out:
        while after < end:
            page = fetch(kind, sub, after, end, fields)
            fresh = [r for r in page if r.get("id") not in seen_at_edge]
            if not fresh:
                if len(page) < 100:
                    break
                after += 1  # a full page all in one second: step past it
                seen_at_edge = set()
                continue
            for r in fresh:
                out.write(json.dumps(r, ensure_ascii=False) + "\n")
            count += len(fresh)
            newest = int(float(fresh[-1]["created_utc"]))
            # items sharing the newest second may continue on the next page; remember them to skip repeats
            edge = {r["id"] for r in fresh if int(float(r["created_utc"])) == newest}
            seen_at_edge = edge | (seen_at_edge if newest == after else set())
            after = newest
            print(f"  r/{sub} {kind}: {count:,} through {datetime.fromtimestamp(newest, ET):%Y-%m-%d %H:%M}", end="\r", flush=True)
            if len(page) < 100:
                break
            time.sleep(pause)
    print(f"  r/{sub} {kind}: {count:,} items" + " " * 30)
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subs", nargs="+", required=True, help="subreddit names without r/")
    ap.add_argument("--start", required=True, help="first day, YYYY-MM-DD (Eastern)")
    ap.add_argument("--end", required=True, help="day after the last day, YYYY-MM-DD (exclusive)")
    ap.add_argument("--kinds", nargs="+", default=["posts", "comments"], choices=["posts", "comments"])
    ap.add_argument("--out", default=None, help="folder to save into (default: Google Drive/My Drive/reddit_pulls)")
    ap.add_argument("--all-fields", action="store_true", help="keep every field (files get much bigger)")
    ap.add_argument("--pause", type=float, default=0.5, help="seconds between requests, to be polite to the API")
    ap.add_argument("--keep-jsonl", action="store_true", help="keep the unzipped .jsonl next to each zip")
    a = ap.parse_args()

    start = datetime.fromisoformat(a.start).replace(tzinfo=ET).timestamp()
    end = datetime.fromisoformat(a.end).replace(tzinfo=ET).timestamp()
    last_day = (datetime.fromisoformat(a.end) - timedelta(days=1)).date().isoformat()
    label = f"{a.start}_to_{last_day}"
    base = a.out
    if not base:
        drive = find_drive()
        if not drive:
            sys.exit("Couldn't find a Google Drive folder. Install Google Drive for desktop and sign in, "
                     "or pass --out with a folder path.")
        base = os.path.join(drive, "reddit_pulls")
    folder = os.path.join(base, label)
    os.makedirs(folder, exist_ok=True)
    print(f"saving to {folder}")

    for sub in a.subs:
        for kind in a.kinds:
            name = f"r_{sub}_{kind}_{label}"
            jsonl = os.path.join(folder, name + ".jsonl")
            zpath = os.path.join(folder, name + ".zip")
            if os.path.exists(zpath) and not os.path.exists(jsonl):
                print(f"  {name}.zip already done, skipping")
                continue
            try:
                n = pull(kind, sub, start, end, jsonl, None if a.all_fields else FIELDS[kind], a.pause)
            except (BadRequest, urllib.error.HTTPError, urllib.error.URLError) as e:
                print(f"  r/{sub} {kind}: failed\n      {e}")
                if os.path.exists(jsonl) and os.path.getsize(jsonl) == 0:
                    os.remove(jsonl)
                continue
            with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                z.write(jsonl, arcname=name + ".jsonl")
            if not a.keep_jsonl:
                os.remove(jsonl)
            print(f"  saved {name}.zip ({os.path.getsize(zpath) / 1e6:.1f} MB, {n:,} items)")
    print("done")


if __name__ == "__main__":
    main()
