"""Arctic Shift pullers: subreddits over a date range, full user histories, and thread context.

Runs anywhere with plain Python 3.8+ (Google Colab included). The workspace Claude runs in usually
can't reach Arctic Shift, so pulls happen in Colab or on your own machine and the zips get attached.

    from socialscope import arctic
    arctic.pull_subreddits(["Destiny", "atrioc"], "2026-10-06", "2026-10-13", out_dir="pulls")
    arctic.pull_user_histories(["some_user"], out_dir="pulls/histories", max_items=2000)
    arctic.pull_thread_context("pulls/histories/user_comments.zip", out_dir="pulls/context")

Every function resumes if interrupted: re-run the same call and it continues where it stopped.
Dates are YYYY-MM-DD in US Eastern time; `end` is exclusive.
"""
import glob, http.client, json, re, os, time, urllib.error, urllib.parse, urllib.request, zipfile
from datetime import datetime, timedelta, timezone

BASE = "https://arctic-shift.photon-reddit.com/api/"
UA = {"User-Agent": "socialscope/1.0 (research)"}


# ---------- dates ----------
def _et_offset(day):
    """US Eastern offset for a date: EDT (-4) from the second Sunday of March to the first Sunday of November."""
    y = day.year
    mar = datetime(y, 3, 8) + timedelta(days=(6 - datetime(y, 3, 8).weekday()) % 7)
    nov = datetime(y, 11, 1) + timedelta(days=(6 - datetime(y, 11, 1).weekday()) % 7)
    return timedelta(hours=-4) if mar <= day.replace(tzinfo=None) < nov else timedelta(hours=-5)


def to_ts(date_str):
    d = datetime.fromisoformat(date_str)
    return d.replace(tzinfo=timezone(_et_offset(d))).timestamp()


def _fmt(ts):
    d = datetime.fromtimestamp(ts, timezone.utc)
    return d.astimezone(timezone(_et_offset(d))).strftime("%Y-%m-%d %H:%M")


# ---------- HTTP ----------
class BadRequest(Exception):
    pass


# ---------- progress ----------
class _TextBar:
    """Fallback when tqdm isn't installed: one line, redrawn in place."""
    def __init__(self, total, initial=0, desc="", unit="it"):
        self.total, self.n, self.desc, self.unit, self.note = total, initial, desc, unit, ""
        self._draw()
    def _draw(self):
        pct = f"{100 * self.n / self.total:3.0f}%" if self.total else ""
        print(f"\r{self.desc}: {pct} {self.n:,.0f}/{self.total:,.0f} {self.unit} {self.note}"[:120].ljust(120), end="", flush=True)
    def update(self, k=1):
        self.n += k; self._draw()
    def set_postfix_str(self, t, refresh=True):
        self.note = t; self._draw()
    def close(self):
        print(flush=True)
    write = staticmethod(print)


_BAR = None  # the bar that "server busy" notes go to


def _progress(total, initial=0, desc="", unit="it"):
    global _BAR
    try:
        from tqdm.auto import tqdm
        _BAR = tqdm(total=total, initial=initial, desc=desc, unit=unit, dynamic_ncols=True,
                    bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {unit} [{elapsed}<{remaining}] {postfix}")
    except Exception:
        _BAR = _TextBar(total, initial, desc, unit)
    return _BAR


def _note(msg):
    """Status line: shown beside the progress bar when there is one, printed otherwise."""
    if _BAR is not None:
        _BAR.set_postfix_str(msg, refresh=True)
    else:
        print("    " + msg, flush=True)


def _done(bar):
    global _BAR
    bar.close()
    _BAR = None


class Throttled(Exception):
    """Server said it was busy ("Timeout. Maybe slow down a bit", 429, 5xx)."""


def _busy(code, body):
    b = body.lower()
    return code in (429, 500, 502, 503, 504, 520, 522, 524) or "timeout" in b or "slow down" in b


def _get(endpoint, params, tries=8):
    url = BASE + endpoint + "?" + urllib.parse.urlencode(params)
    delay = 5
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                data = json.loads(r.read().decode("utf-8"))
            if isinstance(data, dict) and data.get("error"):
                if _busy(0, str(data["error"])):
                    raise Throttled(str(data["error"]))
                raise BadRequest(str(data["error"]))
            return data.get("data", data) if isinstance(data, dict) else data
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            if e.code == 429:
                try:
                    delay = max(delay, min(int(float(e.headers.get("X-RateLimit-Reset") or 0)) + 1, 600))
                except (TypeError, ValueError):
                    pass
            if not _busy(e.code, body):
                if e.code in (400, 404, 422):
                    raise BadRequest(f"{e.code}: {body}")
            if attempt == tries - 1:
                raise Throttled(f"{e.code}: {body}") if _busy(e.code, body) else e
            _note(f"server busy, waiting {delay}s")
        except Throttled as e:
            if attempt == tries - 1:
                raise
            _note(f"server busy, waiting {delay}s")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ConnectionError, OSError,
                http.client.HTTPException) as e:   # dropped connections (ConnectionResetError, IncompleteRead)
            if attempt == tries - 1:
                raise
            _note(f"connection hiccup, retrying in {delay}s")
        time.sleep(delay)
        delay = min(delay * 2, 120)


_STYLE = {}  # request style the server accepted, per kind
_NO_AUTO = []  # set if the server refuses limit=auto
_NO_FIELDS = []  # set if posts/ids refuses a field list
MIN_SLICE = 3600  # shortest time slice (seconds) when the server is busy


def _search(kind, filt, after, before, order, fields=None, tries=8, limit="auto"):
    """One page of posts/comments matching filt between after and before.
    limit="auto" asks Arctic Shift for 100-1000 items per call (it decides by load); 100 is the light mode."""
    def variants():
        for dates in ("epoch", "iso"):
            for use_fields in ((True, False) if fields else (False,)):
                q = dict(filt, sort=order, limit=limit)
                fmt = (lambda t: int(t)) if dates == "epoch" else \
                      (lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"))
                if after is not None:
                    q["after"] = fmt(after)
                if before is not None:
                    q["before"] = fmt(before)
                if use_fields:
                    q["fields"] = fields
                yield dates, q   # the server remembers date style per kind; fields may still be refused
    if limit == "auto" and _NO_AUTO:
        limit = 100
    errors = []
    for style, q in variants():
        if kind in _STYLE and style != _STYLE[kind]:
            continue
        try:
            data = _get(f"{kind}/search", q, tries=tries)
            _STYLE.setdefault(kind, style)
            return data
        except BadRequest as e:
            if limit == "auto" and "limit" in str(e).lower():
                _NO_AUTO.append(True)   # server doesn't take "auto": use 100 from now on
                return _search(kind, filt, after, before, order, fields, tries, 100)
            errors.append(f"{style}: {e}")
            if kind in _STYLE and "fields" not in q:
                raise
    raise BadRequest("every request style was refused:\n  " + "\n  ".join(errors))


def _resume(path):
    """Read an interrupted JSONL; return (count, last_ts, ids at last_ts), trimming a half-written line."""
    if not os.path.exists(path):
        return 0, None, set()
    good, last, edge, broken = [], None, set(), False
    with open(path, "rb") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                broken = True
                continue
            good.append(line)
            t = int(float(rec["created_utc"]))
            edge = edge | {rec["id"]} if t == last else {rec["id"]}
            last = t
    if broken:
        with open(path, "wb") as fh:
            fh.writelines(good)
    return len(good), last, edge


def _page_all(kind, filt, start, end, path, order="asc", max_items=None, pause=0.8, label="", on_progress=None):
    """Write every match in [start, end) to path as JSON lines. order='desc' walks newest first.
    on_progress(count, position_ts) is called after each page."""
    tell = on_progress or (lambda c, t: None)
    count, last, seen = _resume(path)
    lo, hi = start, end
    if last is not None:
        if order == "asc":
            lo = last
        else:
            hi = last + 1
    # When Arctic Shift says it's busy: first ask for smaller pages (auto -> 100), then for shorter time
    # slices (down to MIN_SLICE). After a few successes in a row, step back up. Fewer, bigger calls otherwise.
    limit, window, streak = "auto", None, 0
    with open(path, "a", encoding="utf-8") as out:
        while (max_items is None or count < max_items) and (hi is None or lo is None or lo < hi):
            windowed = order == "asc" and window is not None and lo is not None and hi is not None
            qhi = min(hi, lo + window) if windowed else hi
            can_slice = order == "asc" and lo is not None and hi is not None and (window is None or window > MIN_SLICE)
            can_step = limit == "auto" or can_slice
            try:
                page = _search(kind, filt, lo, qhi, order, tries=3 if can_step else 8, limit=limit)
                streak += 1
                if streak >= 5:
                    streak = 0
                    if window is not None and lo is not None and hi is not None and window < hi - lo:
                        window = min(window * 2, hi - lo)
                    elif window is None and limit != "auto":
                        limit = "auto"
            except Throttled:
                if not can_step:
                    raise
                streak = 0
                if limit == "auto":
                    limit = 100
                    _note("server busy: asking for smaller pages")
                else:
                    window = max(MIN_SLICE, (hi - lo) // 4 if window is None else window // 2)
                    _note(f"server busy: asking for {window / 3600:g}-hour slices")
                time.sleep(max(pause, 5))
                continue
            if len(page) < 100 and windowed and qhi < hi:
                # this slice is finished: write what's new and move to the next slice
                for r in page:
                    if r.get("id") not in seen and (max_items is None or count < max_items):
                        out.write(json.dumps(r, ensure_ascii=False) + "\n")
                        count += 1
                lo = qhi - 1
                seen = {r.get("id") for r in page if int(float(r["created_utc"])) >= qhi - 1}
                tell(count, qhi)
                time.sleep(pause)
                continue
            fresh = [r for r in page if r.get("id") not in seen]
            if not fresh:
                if len(page) < 100:
                    break
                if order == "asc":   # a full page inside one second: step past it
                    lo, seen = (lo if lo is not None else int(float(page[0]["created_utc"]))) + 1, set()
                else:
                    hi, seen = (hi if hi is not None else int(float(page[0]["created_utc"])) + 1) - 1, set()
                continue
            if max_items is not None:
                fresh = fresh[:max_items - count]
            for r in fresh:
                out.write(json.dumps(r, ensure_ascii=False) + "\n")
            count += len(fresh)
            edge_t = int(float(fresh[-1]["created_utc"]))
            edge = {r["id"] for r in fresh if int(float(r["created_utc"])) == edge_t}
            boundary = lo if order == "asc" else (hi - 1 if hi else None)
            seen = edge | (seen if edge_t == boundary else set())
            if order == "asc":
                lo = edge_t
            else:
                hi = edge_t + 1
            tell(count, edge_t)
            if len(page) < 100 and not windowed:
                break
            time.sleep(pause)
    return count


def _zip(jsonl, keep=False):
    z = jsonl[:-6] + ".zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(jsonl, arcname=os.path.basename(jsonl))
    if not keep:
        os.remove(jsonl)
    return z


# ---------- public functions ----------
def pull_subreddits(subs, start, end, kinds=("posts", "comments"), out_dir="pulls", pause=0.8):
    """All posts/comments in each subreddit between start and end (YYYY-MM-DD, end exclusive).
    Writes one zip per sub and kind, named r_<sub>_<kind>_<start>_to_<last day>.zip. Returns the zip paths."""
    last_day = (datetime.fromisoformat(end) - timedelta(days=1)).date().isoformat()
    label = f"{start}_to_{last_day}"
    folder = os.path.join(out_dir, label)
    os.makedirs(folder, exist_ok=True)
    made = []
    for sub in subs:
        for kind in kinds:
            name = os.path.join(folder, f"r_{sub}_{kind}_{label}")
            if os.path.exists(name + ".zip") and not os.path.exists(name + ".jsonl"):
                print(f"r/{sub} {kind}: already done")
                made.append(name + ".zip")
                continue
            t0, t1 = to_ts(start), to_ts(end)
            hours = (t1 - t0) / 3600
            bar = _progress(round(hours), 0, desc=f"r/{sub} {kind}", unit="hours")
            def tell(count, ts, bar=bar):
                bar.update(max(0, round((ts - t0) / 3600) - bar.n))
                bar.set_postfix_str(f"{count:,} items", refresh=False)
            try:
                n = _page_all(kind, {"subreddit": sub}, t0, t1, name + ".jsonl", pause=pause, on_progress=tell)
                bar.update(bar.total - bar.n); bar.set_postfix_str(f"{n:,} items, done")
                made.append(_zip(name + ".jsonl"))
            except (BadRequest, Throttled) as e:
                bar.set_postfix_str("stopped: server too busy. Rerun this cell later; it resumes")
                bar.write(f"r/{sub} {kind}: {e}")
            finally:
                _done(bar)
    print(f"saved to {folder}")
    return made


def pull_user_histories(users, kinds=("posts", "comments"), start=None, end=None, max_items=2000,
                        out_dir="pulls/histories", pause=0.8, name="users", overview=False, oldest=True):
    """Each user's history across ALL subreddits, newest first, up to max_items per user and kind
    (None = everything). Optional start/end limit the dates. Writes <name>_<kind>.zip holding every user,
    With overview=True also saves <name>_overview.json (Arctic Shift's per-subreddit counts; one extra
    call per user, and the history already shows the same thing).
    With oldest=True (default) also saves <name>_oldest.json: each user's oldest post and comment time, so
    account age is right even when max_items cuts the history short (two small extra calls per user).
    `users` can be a list or a path to a text file with one username per line."""
    if isinstance(users, str):
        users = [re.sub(r"^/?u/", "", u.strip()) for u in open(users) if u.strip() and not u.startswith("#")]
    os.makedirs(out_dir, exist_ok=True)
    tmp = os.path.join(out_dir, "_parts")
    os.makedirs(tmp, exist_ok=True)
    s = to_ts(start) if start else None
    e = to_ts(end) if end else None
    overview_path = os.path.join(out_dir, f"{name}_overview.json")
    ov = json.load(open(overview_path)) if os.path.exists(overview_path) else {}
    oldest_path = os.path.join(out_dir, f"{name}_oldest.json")
    old = json.load(open(oldest_path)) if os.path.exists(oldest_path) else {}
    finished = lambda u: all(os.path.exists(os.path.join(tmp, f"{u}_{k}.jsonl.done")) for k in kinds) and \
        (not oldest or u in old)
    already = sum(finished(u) for u in users)
    bar = _progress(len(users), already, desc="user histories", unit="users")
    failed = []
    for i, u in enumerate(users, 1):
        if finished(u) and (not overview or u in ov):
            continue
        for kind in kinds:
            part = os.path.join(tmp, f"{u}_{kind}.jsonl")
            done = part + ".done"
            if os.path.exists(done):
                continue
            try:
                _page_all(kind, {"author": u}, s, e, part, order="desc", max_items=max_items, pause=pause,
                          on_progress=lambda c, t, u=u, kind=kind: bar.set_postfix_str(f"u/{u} {kind}: {c:,}", refresh=False))
                open(done, "w").close()
            except (BadRequest, Throttled) as err:
                failed.append(f"u/{u} {kind}")
                bar.set_postfix_str(f"u/{u} {kind} failed, moving on")
        if oldest and u not in old:
            first = []
            for kind in kinds:
                try:
                    page = _search(kind, {"author": u}, None, None, "asc", fields="id,created_utc", tries=4, limit=1)
                    first += [float(r["created_utc"]) for r in page[:1]]
                except (BadRequest, Throttled):
                    pass
            old[u] = min(first) if first else None
            json.dump(old, open(oldest_path, "w"))
        if overview and u not in ov:
            try:
                ov[u] = _get("users/interactions/subreddits", {"author": u, "limit": 200})
            except Exception as err:  # the overview is optional
                ov[u] = {"error": str(err)[:200]}
            json.dump(ov, open(overview_path, "w"))
        if finished(u):
            bar.update(1)
    _done(bar)
    if failed:
        print(f"{len(failed)} pulls failed (rerun this cell to retry just those): " + ", ".join(failed[:10]) + (" ..." if len(failed) > 10 else ""))
    made = []
    for kind in kinds:
        jsonl = os.path.join(out_dir, f"{name}_{kind}.jsonl")
        with open(jsonl, "w", encoding="utf-8") as out:
            for u in users:
                p = os.path.join(tmp, f"{u}_{kind}.jsonl")
                if os.path.exists(p):
                    out.write(open(p, encoding="utf-8").read())
        made.append(_zip(jsonl))
    if oldest and os.path.exists(oldest_path):
        made.append(oldest_path)
    print(f"saved {', '.join(os.path.basename(m) for m in made)} to {out_dir}")
    return made


LIGHT_FIELDS = "id,created_utc,subreddit,title,score,num_comments,author"


def pull_thread_context(source, out_dir="pulls/context", with_comments=False, comment_limit=200,
                        max_threads=None, name="context", pause=0.8, light=True):
    """The posts that comments were made in: title, body, subreddit, score, link.
    `source` is a comments zip/jsonl (e.g. from pull_user_histories) or a list of post ids.
    With with_comments=True, also saves up to comment_limit comments from each thread's tree.
    light=True (default) asks only for id, time, subreddit, title, score, comment count and author:
    files a fraction of the size, small enough to attach without phone-sized copies.
    Writes <name>_posts.zip (and <name>_trees.zip)."""
    ids = []
    if isinstance(source, (list, tuple, set)):
        ids = [str(x) for x in source]
    else:
        opener = zipfile.ZipFile(source).open(zipfile.ZipFile(source).namelist()[0]) if source.endswith(".zip") \
            else open(source, "rb")
        with opener as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("link_id"):
                    ids.append((r.get("author"), r["link_id"]))
        # take threads round-robin across users, so a max_threads cap samples every user evenly
        per = {}
        for a, i in ids:
            per.setdefault(a, []).append(i)
        ids, lists = [], list(per.values())
        for k in range(max((len(l) for l in lists), default=0)):
            ids += [l[k] for l in lists if k < len(l)]
    ids = list(dict.fromkeys(i[3:] if i.startswith("t3_") else i for i in ids))
    if max_threads:
        ids = ids[:max_threads]
    os.makedirs(out_dir, exist_ok=True)
    posts = os.path.join(out_dir, f"{name}_posts.jsonl")
    have = set()
    if os.path.exists(posts):
        for line in open(posts, encoding="utf-8"):
            try:
                have.add(json.loads(line)["id"])
            except Exception:
                pass
    missing_path = os.path.join(out_dir, f"{name}_missing.txt")  # ids Arctic Shift has no post for
    if os.path.exists(missing_path):
        have |= {l.strip() for l in open(missing_path) if l.strip()}
    todo = [i for i in ids if i not in have]
    bar = _progress(len(ids), len(ids) - len(todo), desc="threads", unit="threads")
    with open(posts, "a", encoding="utf-8") as out:
        # 500 ids per call is the most Arctic Shift takes. When it's busy, ask for fewer per call
        # (down to 50), then grow back after a few successes.
        k, size, streak = 0, 500, 0
        miss = open(missing_path, "a")
        while k < len(todo):
            batch = todo[k:k + size]
            try:
                q = {"ids": ",".join(batch)}
                if light and not _NO_FIELDS:
                    q["fields"] = LIGHT_FIELDS
                try:
                    got = _get("posts/ids", q, tries=3 if size > 50 else 8) or []
                except BadRequest:
                    if "fields" not in q:
                        raise
                    _NO_FIELDS.append(True)   # server refused the field list: fetch full posts instead
                    continue
            except Throttled:
                if size <= 50:
                    bar.set_postfix_str("stopped: server too busy. Rerun this cell later; it resumes")
                    _done(bar)
                    raise Throttled("server still busy at 50 ids per call: rerun this cell later; it resumes")
                size, streak = max(50, size // 2), 0
                _note(f"server busy: {size} per call")
                time.sleep(max(pause, 5))
                continue
            for r in got:
                out.write(json.dumps(r, ensure_ascii=False) + "\n")
            out.flush()
            back = {str(r.get("id")) for r in got}
            miss.writelines(i + "\n" for i in batch if i not in back)
            miss.flush()
            k += len(batch)
            bar.update(len(batch))
            bar.set_postfix_str(f"{size} per call", refresh=False)
            streak += 1
            if streak >= 5 and size < 500:
                size, streak = min(500, size * 2), 0
            time.sleep(pause)
        miss.close()
    _done(bar)
    print("zipping (a big file takes a minute)...", flush=True)
    made = [_zip(posts, keep=True)]
    print(f"saved {os.path.basename(made[0])} to {out_dir}")
    if with_comments:
        trees = os.path.join(out_dir, f"{name}_trees.jsonl")
        done = set()
        if os.path.exists(trees):
            for line in open(trees, encoding="utf-8"):
                try:
                    done.add(json.loads(line)["link_id"])
                except Exception:
                    pass
        tbar = _progress(len(ids), sum(("t3_" + i) in done for i in ids), desc="comment trees", unit="threads")
        with open(trees, "a", encoding="utf-8") as out:
            for n, i in enumerate(ids, 1):
                if "t3_" + i in done:
                    continue
                try:
                    tree = _get("comments/tree", {"link_id": "t3_" + i, "limit": comment_limit})
                except (BadRequest, Throttled) as err:
                    tree = {"error": str(err)[:200]}
                out.write(json.dumps({"link_id": "t3_" + i, "tree": tree}, ensure_ascii=False) + "\n")
                tbar.update(1)
                time.sleep(pause)
        _done(tbar)
        made.append(_zip(trees, keep=True))
    return made


# ---------- shrink for upload ----------
TOPICS = (r"\b(?:hasan|hasanabi|destiny|ethan klein|h3h3|h3 ?podcast|asmongold|xqc|streamers?|twitch|kick\.com|"
          r"israel\w*|gaza|palestin\w*|hamas|idf|netanyahu|ukrain\w*|russia\w*|putin|zelensk\w*|"
          r"ice|immigration|deport\w*|trump|elon|musk|mamdani|dsa|aipac)\b")


def pull_matched_threads(posts, pattern=TOPICS, min_comments=20, max_threads=300, comment_cap=2000,
                         out_dir="pulls/matched", name="matched", pause=0.8):
    """Comments for only the threads that matter. `posts` is one or more posts zips/jsonl (for example a
    posts-only week of r/politics and r/worldnews from pull_subreddits). Picks posts whose title or text
    matches `pattern` (default TOPICS: the people and issues the drama-sub analysis tracks) with at least
    min_comments comments, biggest first, up to max_threads; then saves up to comment_cap comments from each.
    Writes <name>_threads.csv (which threads were picked and why) and <name>_comments.zip. Resumes if rerun."""
    import csv as _csv
    rx = re.compile(pattern, re.I)
    picked = {}
    for src in ([posts] if isinstance(posts, str) else posts):
        for f in sorted(glob.glob(src)) or [src]:
            opener = zipfile.ZipFile(f).open(zipfile.ZipFile(f).namelist()[0]) if f.endswith(".zip") else open(f, "rb")
            with opener as fh:
                for line in fh:
                    try:
                        r = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    text = (r.get("title") or "") + " " + (r.get("selftext") or "")[:500]
                    m = rx.search(text)
                    if m and (r.get("num_comments") or 0) >= min_comments and r.get("id"):
                        picked[r["id"]] = (r.get("num_comments") or 0, r.get("subreddit"), float(r.get("created_utc") or 0),
                                           m.group(0).lower(), (r.get("title") or "")[:200])
    order = sorted(picked, key=lambda i: -picked[i][0])[:max_threads]
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"{name}_threads.csv"), "w", newline="", encoding="utf-8") as fh:
        w = _csv.writer(fh); w.writerow(["id", "subreddit", "num_comments", "matched", "title"])
        for i in order:
            n, sub, t, hit, title = picked[i]; w.writerow([i, sub, n, hit, title])
    print(f"{len(picked)} matching threads; pulling comments for the top {len(order)}", flush=True)
    part = os.path.join(out_dir, f"{name}_parts"); os.makedirs(part, exist_ok=True)
    done_path = os.path.join(out_dir, f"{name}_done.txt")
    done = {l.strip() for l in open(done_path)} if os.path.exists(done_path) else set()
    global _BAR
    bar = _progress(len(order), sum(i in done for i in order), desc="threads", unit="threads")
    failed = []
    for i in order:
        if i in done:
            continue
        t0 = picked[i][2]
        try:
            _BAR = bar
            _page_all("comments", {"link_id": "t3_" + i}, t0 - 60, t0 + 60 * 86400,
                      os.path.join(part, i + ".jsonl"), max_items=comment_cap, pause=pause)
            with open(done_path, "a") as fh:
                fh.write(i + "\n")
            done.add(i)
        except (Throttled, BadRequest) as e:
            failed.append(i); _note(f"skipped a thread ({type(e).__name__}); rerun to retry")
        bar.update(1)
    _done(bar)
    out = os.path.join(out_dir, f"{name}_comments.jsonl")
    with open(out, "w", encoding="utf-8") as o:
        for i in order:
            pth = os.path.join(part, i + ".jsonl")
            if i in done and os.path.exists(pth):
                o.writelines(open(pth, encoding="utf-8"))
    made = [_zip(out), os.path.join(out_dir, f"{name}_threads.csv")]
    if failed:
        print(f"{len(failed)} threads failed (server busy); rerun this cell to fill them in")
    print("saved", ", ".join(os.path.basename(m) for m in made))
    return made


POST_KEEP = ("id", "author", "author_fullname", "subreddit", "created_utc", "title", "selftext", "url", "score",
             "num_comments", "link_flair_text", "distinguished", "removed_by_category", "over_18", "crosspost_parent")
COMMENT_KEEP = ("id", "author", "author_fullname", "subreddit", "created_utc", "body", "link_id", "parent_id",
                "score", "distinguished", "removed_by_category")


def slim(src, max_mb=25, selftext_chars=500):
    """Copy a pulled zip keeping only the fields the analysis uses, split into parts under about max_mb each
    (for attaching from a phone). Writes <name>_slim_1.zip, _2.zip ... next to the source. Returns the paths."""
    base = src[:-4] if src.endswith(".zip") else src.rsplit(".", 1)[0]
    zf = zipfile.ZipFile(src)
    made, part, out, size = [], 0, None, 0
    budget = max_mb * 4 * 1024 * 1024  # JSON text zips about 4-6x; 4x keeps each part under max_mb

    def close():
        if out:
            out.close()
            made.append(_zip(out.name))
            print(f"  {os.path.basename(made[-1])}: {os.path.getsize(made[-1]) / 1e6:.1f} MB", flush=True)
    with zf.open(zf.namelist()[0]) as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            keep = POST_KEEP if "title" in r else COMMENT_KEEP
            r = {k: r[k] for k in keep if r.get(k) not in (None, "")}
            if selftext_chars and len(r.get("selftext") or "") > selftext_chars:
                r["selftext"] = r["selftext"][:selftext_chars]
            s = json.dumps(r, ensure_ascii=False) + "\n"
            if out is None or size + len(s.encode()) > budget:
                close()
                part += 1
                out = open(f"{base}_slim_{part}.jsonl", "w", encoding="utf-8")
                size = 0
            out.write(s)
            size += len(s.encode())
    close()
    return made
