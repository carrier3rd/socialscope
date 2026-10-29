"""Shared loader for Reddit dumps (Arctic Shift / Pushshift NDJSON, .json/.jsonl/.zst)."""
import glob, io, json, re, subprocess

SKIP = {"[deleted]", "AutoModerator", "", None}
THREAD_LINK = re.compile(r"(?:reddit\.com/r/\w+/comments/|redd\.it/)([a-z0-9]{5,9})", re.I)


def _open(path):
    if path.endswith(".zip"):
        import zipfile
        z = zipfile.ZipFile(path)
        name = next(n for n in z.namelist() if not n.endswith("/"))
        return io.TextIOWrapper(z.open(name), encoding="utf-8", errors="replace")
    if path.endswith(".zst"):
        try:
            import zstandard
            return io.TextIOWrapper(zstandard.ZstdDecompressor(max_window_size=2**31).stream_reader(open(path, "rb")),
                                    encoding="utf-8", errors="replace")
        except ImportError:
            p = subprocess.Popen(["zstd", "-dc", "--long=31", path], stdout=subprocess.PIPE)
            return io.TextIOWrapper(p.stdout, encoding="utf-8", errors="replace")
    return open(path, encoding="utf-8", errors="replace")


def iter_records(paths):
    for pattern in paths:
        for path in sorted(glob.glob(pattern)) or [pattern]:
            with _open(path) as fh:
                for line in fh:
                    line = line.strip()
                    if line.startswith("{"):
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            continue


def load_reddit(paths, skip_authors=()):
    """Normalized rows. Mod/admin-distinguished items and skipped authors are dropped."""
    skip = SKIP | set(skip_authors)
    rows = []
    for r in iter_records(paths):
        if r.get("author") in skip or r.get("distinguished") in ("moderator", "admin"):
            continue
        is_post = "title" in r
        body = (r.get("selftext") if is_post else r.get("body")) or ""
        rows.append({
            "id": ("t3_" if is_post else "t1_") + str(r.get("id")),
            "thread": "t3_" + str(r.get("id")) if is_post else r.get("link_id"),
            "parent": r.get("parent_id"),
            "sub": str(r.get("subreddit") or ""),
            "author": r["author"],
            "created": float(r.get("created_utc") or 0),
            "title": r.get("title") or "",
            "body": body,
            "url": r.get("url") or "",
            "score": r.get("score") or 0,
            "removed": body in ("[removed]", "[deleted]") or bool(r.get("removed_by_category")),
            "is_post": is_post,
            "author_id": r.get("author_fullname"),
        })
    return rows
