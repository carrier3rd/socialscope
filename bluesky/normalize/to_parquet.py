#!/usr/bin/env python3
"""Phase 2 normalize: raw Bluesky files -> the five parquet tables of the spec (section 8), deletes applied.

    python bluesky/normalize/to_parquet.py            stage new or changed raw files, then rebuild the tables
    python bluesky/normalize/to_parquet.py --full     stage every raw file again first

Written Nov 27 2026 (owner: "start phase 2"). Prints and writes counts only: no DID, handle or text leaves the
private data folder.

Inputs, under <data> = ~/socialscope_data/bluesky (bsky_common.data_dir):
  raw/jetstream/<hour>.jsonl.gz      the recorder's kept events (the hour still being written is skipped)
  raw/histories/<aa>/<did>.jsonl.gz  listRecords post records per replier (appview.py histories)
  raw/threads/<target>/<rkey>.json.gz  getPostThread responses (appview.py threads)
  raw/profiles/part-NNNN.jsonl.gz    getProfiles results
  raw/labels/<labeler>/labels.jsonl.gz  whitelisted labels (labels.py)
  raw/plc/<aa>/<did>.json            PLC audit logs (plc.py)

Outputs, under <data>/processed/:
  staging/...                        one parquet set per raw jetstream hour, history bucket and thread folder, so
                                     a run only parses what is new (state: staging/state.json)
  tables/posts.parquet               uri, did, rkey, created_at, indexed_at, text, langs, reply_parent, reply_root,
                                     quote_uri, embed_type, facet_links, facet_mentions, sources
  tables/interactions.parquet        type, uri, actor_did, subject, list_uri, created_at, rkey_time, time_us
  tables/accounts.parquet            did, handle, display_name, created_at, pds_host, domain_handle, self_labels,
                                     verified, status, side_seen
  tables/labels.parquet              src, uri_or_did, val, neg, cts, exp (the newest event per src/uri/val)
  tables/plc_ops.parquet             did, op_type, handle, pds, rotation_keys_changed, created_at, nullified
  normalize_report.json              row counts in and out, duplicates dropped, deletes applied

Rules:
  - Duplicates: a record is one (did, collection, rkey); the same record from several sources or replays is kept
    once. Jetstream copies of one event from two hosts differ only in time_us, so they collapse here too.
  - Deletes (spec section 3): a Jetstream delete of (did, collection, rkey) drops that record from every source,
    unless the record was created again after the delete. A snapshot record (history, thread) has no event
    time, so any delete seen for it drops it.
  - An account whose newest account event says status "deleted" loses all its records. Deactivated and
    taken-down accounts keep theirs (deactivation can be undone); their status is in accounts.status.
  - side_seen: the sides of the target threads an account replied in. It is a grouping variable for aggregates
    (spec section 3, "Faction"); it is never published per account.
"""
import argparse
import datetime as dt
import gzip
import hashlib
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "collect"))
import bsky_common as bc  # noqa: E402

POST = "app.bsky.feed.post"
INTERACTIONS = {"app.bsky.feed.like": "like", "app.bsky.feed.repost": "repost", "app.bsky.graph.follow": "follow",
                "app.bsky.graph.block": "block", "app.bsky.graph.listitem": "listitem"}
STAGE_VERSION = 1   # bump when a staged row's shape or meaning changes: everything is staged again


# ---------------------------------------------------------------- parsing one record
def _ts(iso):
    """An ISO time as written by a client -> microseconds since 1970, or None. Clients write many formats."""
    if not isinstance(iso, str) or len(iso) < 10:
        return None
    s = iso.strip().replace("Z", "+00:00")
    if "." in s:                                      # Python takes at most 6 fractional digits
        head, frac = s.split(".", 1)
        digits = "".join(c for c in frac if c.isdigit())
        rest = frac[len(digits):]
        s = f"{head}.{(digits + '000000')[:6]}{rest}"
    try:
        t = dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    try:
        return int(t.timestamp() * 1_000_000)
    except (OverflowError, OSError, ValueError):
        return None


def did_of(uri):
    """at://did:plc:x/coll/rkey -> did:plc:x (None for anything else)."""
    if isinstance(uri, str) and uri.startswith("at://"):
        return uri[5:].split("/", 1)[0] or None
    return None


def _uri(rec, *path):
    for p in path:
        rec = rec.get(p) if isinstance(rec, dict) else None
    return rec if isinstance(rec, str) else None


def post_row(did, rkey, rec, source, time_us=None, indexed_us=None):
    """One app.bsky.feed.post record -> one posts row."""
    rec = rec if isinstance(rec, dict) else {}
    embed = rec.get("embed") if isinstance(rec.get("embed"), dict) else {}
    etype = embed.get("$type")
    quote = None
    if etype == "app.bsky.embed.record":
        quote = _uri(embed, "record", "uri")
    elif etype == "app.bsky.embed.recordWithMedia":
        quote = _uri(embed, "record", "record", "uri")
    links, mentions = [], []
    for f in rec.get("facets") or []:
        for feat in (f.get("features") or []) if isinstance(f, dict) else []:
            if not isinstance(feat, dict):
                continue
            if feat.get("$type") == "app.bsky.richtext.facet#link" and isinstance(feat.get("uri"), str):
                links.append(feat["uri"])
            elif feat.get("$type") == "app.bsky.richtext.facet#mention" and isinstance(feat.get("did"), str):
                mentions.append(feat["did"])
    if etype == "app.bsky.embed.external" and _uri(embed, "external", "uri"):
        links.append(embed["external"]["uri"])          # link cards count as links too
    langs = rec.get("langs")
    return {"uri": f"at://{did}/{POST}/{rkey}", "did": did, "rkey": rkey, "created_us": _ts(rec.get("createdAt")),
            "indexed_us": indexed_us, "time_us": time_us,
            "text": rec.get("text") if isinstance(rec.get("text"), str) else None,
            "langs": [x for x in langs if isinstance(x, str)] if isinstance(langs, list) else [],
            "reply_parent": _uri(rec, "reply", "parent", "uri"), "reply_root": _uri(rec, "reply", "root", "uri"),
            "quote_uri": quote, "embed_type": etype, "facet_links": links, "facet_mentions": mentions,
            "source": source}


def interaction_row(did, coll, rkey, rec, time_us):
    rec = rec if isinstance(rec, dict) else {}
    subj = rec.get("subject")
    subject = subj.get("uri") if isinstance(subj, dict) else subj if isinstance(subj, str) else None
    return {"type": INTERACTIONS[coll], "uri": f"at://{did}/{coll}/{rkey}", "actor_did": did, "subject": subject,
            "list_uri": rec.get("list") if isinstance(rec.get("list"), str) else None,
            "created_us": _ts(rec.get("createdAt")), "rkey_time_us": bc.tid_to_us(rkey), "time_us": time_us,
            "source": "jetstream"}


# ---------------------------------------------------------------- staging
def _arrow():
    import pyarrow as pa
    L = pa.list_(pa.string())
    return pa, {
        "posts": pa.schema([("uri", pa.string()), ("did", pa.string()), ("rkey", pa.string()),
                            ("created_us", pa.int64()), ("indexed_us", pa.int64()), ("time_us", pa.int64()),
                            ("text", pa.string()), ("langs", L), ("reply_parent", pa.string()),
                            ("reply_root", pa.string()), ("quote_uri", pa.string()), ("embed_type", pa.string()),
                            ("facet_links", L), ("facet_mentions", L), ("source", pa.string())]),
        "interactions": pa.schema([("type", pa.string()), ("uri", pa.string()), ("actor_did", pa.string()),
                                   ("subject", pa.string()), ("list_uri", pa.string()), ("created_us", pa.int64()),
                                   ("rkey_time_us", pa.int64()), ("time_us", pa.int64()), ("source", pa.string())]),
        "deletes": pa.schema([("did", pa.string()), ("collection", pa.string()), ("rkey", pa.string()),
                              ("time_us", pa.int64())]),
        "account_events": pa.schema([("did", pa.string()), ("active", pa.bool_()), ("status", pa.string()),
                                     ("time_us", pa.int64())]),
    }


def _write(folder, rows_by_table, counts):
    pa, schemas = _arrow()
    import pyarrow.parquet as pq
    folder.mkdir(parents=True, exist_ok=True)
    for name, schema in schemas.items():
        rows = rows_by_table.get(name, [])
        tmp = folder / f"{name}.parquet.tmp"
        pq.write_table(pa.Table.from_pylist(rows, schema=schema), tmp, compression="zstd")
        os.replace(tmp, folder / f"{name}.parquet")
        counts[name] = counts.get(name, 0) + len(rows)


def stage_jetstream(path, dest):
    """One closed hour file -> staged rows. Counts lines, bad lines and exact duplicate lines."""
    rows = {"posts": [], "interactions": [], "deletes": [], "account_events": []}
    c = {"lines": 0, "bad_lines": 0, "duplicate_lines": 0}
    seen = set()
    with gzip.open(path, "rt", encoding="utf-8") as f:
        try:
            for line in f:
                c["lines"] += 1
                k = hashlib.blake2b(line.rstrip("\r\n").encode("utf-8"), digest_size=16).digest()
                if k in seen:
                    c["duplicate_lines"] += 1
                    continue
                seen.add(k)
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    c["bad_lines"] += 1
                    continue
                did, t, kind = ev.get("did"), ev.get("time_us"), ev.get("kind")
                if not isinstance(did, str) or not isinstance(t, int):
                    c["bad_lines"] += 1
                    continue
                if kind == "account":
                    a = ev.get("account") or {}
                    rows["account_events"].append({"did": did, "active": a.get("active"),
                                                   "status": a.get("status"), "time_us": t})
                    continue
                if kind != "commit":
                    continue                              # identity events: handles come from PLC and profiles
                cm = ev.get("commit") or {}
                coll, rkey, op = cm.get("collection"), cm.get("rkey"), cm.get("operation")
                if not isinstance(rkey, str):
                    c["bad_lines"] += 1
                    continue
                if op == "delete":
                    rows["deletes"].append({"did": did, "collection": coll, "rkey": rkey, "time_us": t})
                elif op in ("create", "update") and coll == POST:
                    rows["posts"].append(post_row(did, rkey, cm.get("record"), "jetstream", time_us=t, indexed_us=t))
                elif op in ("create", "update") and coll in INTERACTIONS:
                    rows["interactions"].append(interaction_row(did, coll, rkey, cm.get("record"), t))
        except (EOFError, OSError):                       # a file cut off by a crash: what was read still counts
            c["truncated_files"] = 1
    _write(dest, rows, c)
    return c


def stage_histories(files, dest):
    rows, c = {"posts": []}, {"files": 0, "bad_lines": 0}
    for p in files:
        c["files"] += 1
        try:
            with gzip.open(p, "rt", encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except json.JSONDecodeError:
                        c["bad_lines"] += 1
                        continue
                    uri = r.get("uri")
                    did = did_of(uri)
                    if not did:
                        c["bad_lines"] += 1
                        continue
                    rows["posts"].append(post_row(did, uri.rsplit("/", 1)[1], r.get("value"), "history"))
        except (EOFError, OSError):
            c["truncated_files"] = c.get("truncated_files", 0) + 1
    _write(dest, rows, c)
    return c


def _thread_posts(node, out):
    if not isinstance(node, dict):
        return out
    p = node.get("post")
    if isinstance(p, dict) and isinstance(p.get("uri"), str):
        did = (p.get("author") or {}).get("did") or did_of(p["uri"])
        if did:
            out.append(post_row(did, p["uri"].rsplit("/", 1)[1], p.get("record"), "thread",
                                indexed_us=_ts(p.get("indexedAt"))))
    for r in node.get("replies") or []:
        _thread_posts(r, out)
    return out


def stage_threads(files, dest):
    rows, c = {"posts": []}, {"files": 0}
    for p in files:
        c["files"] += 1
        try:
            with gzip.open(p, "rt", encoding="utf-8") as f:
                _thread_posts(json.load(f).get("thread"), rows["posts"])
        except (EOFError, OSError, ValueError):
            c["bad_files"] = c.get("bad_files", 0) + 1
    _write(dest, rows, c)
    return c


def _stamp(files):
    h = hashlib.sha1(str(STAGE_VERSION).encode())
    for p in sorted(files):
        st = p.stat()
        h.update(f"{p.name}:{st.st_size}:{int(st.st_mtime)}\n".encode())
    return h.hexdigest()


def stage_all(data, full=False, log=print):
    """Stage every raw unit whose files changed since it was last staged. Returns counts per kind."""
    raw, staging = data / "raw", data / "processed" / "staging"
    state_path = staging / "state.json"
    state = {} if full else bc.load_json(state_path, {})
    units = []
    jet = raw / "jetstream"
    for p in sorted(jet.glob("20*.jsonl.gz")) if jet.is_dir() else []:
        if (jet / p.name[:-3]).exists():                 # the hour still being written: next run
            continue
        units.append(("jetstream", p.name[:-len(".jsonl.gz")], [p], staging / "jetstream" / p.name[:-9]))
    for kind, root, pattern in (("histories", raw / "histories", "*.jsonl.gz"), ("threads", raw / "threads", "*.json.gz")):
        for d in sorted(x for x in root.iterdir() if x.is_dir()) if root.is_dir() else []:
            files = sorted(d.glob(pattern))
            if files:
                units.append((kind, d.name, files, staging / kind / d.name))
    out = {}
    keep = set()
    for kind, name, files, dest in units:
        key = f"{kind}/{name}"
        keep.add(key)
        stamp = _stamp(files)
        if state.get(key) == stamp and (dest / "posts.parquet").exists():
            continue
        fn = {"jetstream": lambda: stage_jetstream(files[0], dest), "histories": lambda: stage_histories(files, dest),
              "threads": lambda: stage_threads(files, dest)}[kind]
        c = fn()
        for k, v in c.items():
            out.setdefault(kind, {})[k] = out.setdefault(kind, {}).get(k, 0) + v
        state[key] = stamp
        bc.atomic_json(state_path, state)                  # saved per unit: an interrupted run resumes
    for key in [k for k in state if k not in keep]:        # a raw unit that went away
        state.pop(key)
    staging.mkdir(parents=True, exist_ok=True)
    bc.atomic_json(state_path, state)
    log(f"staged: {json.dumps({k: v.get('lines', v.get('files')) for k, v in out.items()})}")
    return out


# ---------------------------------------------------------------- small inputs, read whole each run
def profiles_rows(raw):
    newest = {}
    for p in sorted((raw / "profiles").glob("part-*.jsonl.gz")) if (raw / "profiles").is_dir() else []:
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                pr = r.get("profile") or {}
                did = pr.get("did")
                if not isinstance(did, str):
                    continue
                if did not in newest or (r.get("fetched") or "") >= (newest[did][0] or ""):
                    newest[did] = (r.get("fetched"), pr)
    out = []
    for did, (_, pr) in newest.items():
        labels = [x.get("val") for x in pr.get("labels") or [] if isinstance(x, dict) and x.get("src") == did]
        ver = pr.get("verification") or {}
        out.append({"did": did, "handle": pr.get("handle"), "display_name": pr.get("displayName"),
                    "created_us": _ts(pr.get("createdAt")), "self_labels": [x for x in labels if isinstance(x, str)],
                    "verified": ver.get("verifiedStatus") == "valid" or ver.get("trustedVerifierStatus") == "valid"})
    return out


def plc_rows(raw):
    out = []
    root = raw / "plc"
    for p in sorted(root.glob("*/*.json")) if root.is_dir() else []:
        try:
            log = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        prev_keys = None
        for e in log if isinstance(log, list) else []:
            op = e.get("operation") or {}
            typ = op.get("type")
            if typ == "create":                           # the legacy first-operation format
                keys = [op.get("recoveryKey"), op.get("signingKey")]
                handle, pds = op.get("handle"), op.get("service")
            else:
                keys = op.get("rotationKeys")
                aka = [x for x in op.get("alsoKnownAs") or [] if isinstance(x, str) and x.startswith("at://")]
                handle = aka[0][5:] if aka else None
                pds = ((op.get("services") or {}).get("atproto_pds") or {}).get("endpoint")
            keys = sorted(k for k in keys or [] if isinstance(k, str))
            out.append({"did": e.get("did"), "op_type": typ, "handle": handle, "pds": pds,
                        "rotation_keys_changed": prev_keys is not None and keys != prev_keys and typ != "plc_tombstone",
                        "created_us": _ts(e.get("createdAt")), "nullified": bool(e.get("nullified"))})
            if not e.get("nullified"):
                prev_keys = keys
    return out


def label_rows(raw):
    out = []
    root = raw / "labels"
    for p in sorted(root.glob("*/labels.jsonl.gz")) if root.is_dir() else []:
        try:
            with gzip.open(p, "rt", encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    out.append({"seq": r.get("seq"), "src": r.get("src"), "uri_or_did": r.get("uri"),
                                "val": r.get("val"), "neg": bool(r.get("neg")), "cts_us": _ts(r.get("cts")),
                                "exp_us": _ts(r.get("exp")), "labeler": p.parent.name})
        except (EOFError, OSError):
            pass
    return out


# ---------------------------------------------------------------- the tables
SQL = r"""
CREATE TEMP TABLE dels AS
  SELECT did, collection, rkey, max(time_us) AS del_us FROM read_parquet(?) GROUP BY ALL;
CREATE TEMP TABLE gone_accounts AS
  SELECT did FROM (SELECT did, arg_max(status, time_us) AS status FROM read_parquet(?) GROUP BY did)
  WHERE status = 'deleted';
CREATE TEMP TABLE p_all AS SELECT * FROM read_parquet(?, union_by_name = true);
CREATE TEMP TABLE i_all AS SELECT * FROM read_parquet(?, union_by_name = true);

-- the newest copy of each record. A delete removes it unless it was written again after the delete
CREATE TEMP TABLE posts_kept AS
WITH last_write AS (
  SELECT uri, max(time_us) AS write_us FROM p_all GROUP BY uri
)
SELECT p.uri,
       any_value(p.did) AS did, any_value(p.rkey) AS rkey,
       arg_max(p.created_us, coalesce(p.time_us, 0)) AS created_us,
       coalesce(min(p.indexed_us) FILTER (WHERE p.source = 'thread'), min(p.indexed_us)) AS indexed_us,
       arg_max(p.text, coalesce(p.time_us, 0)) AS text, arg_max(p.langs, coalesce(p.time_us, 0)) AS langs,
       arg_max(p.reply_parent, coalesce(p.time_us, 0)) AS reply_parent,
       arg_max(p.reply_root, coalesce(p.time_us, 0)) AS reply_root,
       arg_max(p.quote_uri, coalesce(p.time_us, 0)) AS quote_uri,
       arg_max(p.embed_type, coalesce(p.time_us, 0)) AS embed_type,
       arg_max(p.facet_links, coalesce(p.time_us, 0)) AS facet_links,
       arg_max(p.facet_mentions, coalesce(p.time_us, 0)) AS facet_mentions,
       list_sort(list_distinct(list(p.source))) AS sources
FROM p_all p
JOIN last_write w USING (uri)
LEFT JOIN dels d ON d.did = p.did AND d.collection = 'app.bsky.feed.post' AND d.rkey = p.rkey
WHERE (d.del_us IS NULL OR (w.write_us IS NOT NULL AND w.write_us > d.del_us))
  AND p.did NOT IN (SELECT did FROM gone_accounts)
GROUP BY p.uri;

CREATE TEMP TABLE inter_kept AS
SELECT i.uri, any_value(i.type) AS type, any_value(i.actor_did) AS actor_did,
       arg_max(i.subject, i.time_us) AS subject, arg_max(i.list_uri, i.time_us) AS list_uri,
       arg_max(i.created_us, i.time_us) AS created_us, any_value(i.rkey_time_us) AS rkey_time_us,
       min(i.time_us) AS time_us
FROM i_all i
LEFT JOIN dels d ON d.did = i.actor_did AND d.rkey = split_part(i.uri, '/', 5)
  AND d.collection = split_part(i.uri, '/', 4)
WHERE (d.del_us IS NULL OR i.time_us > d.del_us)
  AND i.actor_did NOT IN (SELECT did FROM gone_accounts)
GROUP BY i.uri;
"""


TS_NAMES = {"created_us": "created_at", "indexed_us": "indexed_at", "rkey_time_us": "rkey_time", "cts_us": "cts",
            "exp_us": "exp"}    # the spec's column names (section 8)


def _ts_cols(cols):
    """Microsecond columns -> UTC timestamps under the spec's names."""
    return ", ".join(f"make_timestamp({c}) AS {TS_NAMES[c]}" for c in cols)


def build_tables(data, cfg, log=print):
    import duckdb
    import pyarrow as pa
    raw, proc = data / "raw", data / "processed"
    staging, tables = proc / "staging", proc / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    globs = {n: sorted(str(p) for p in staging.glob(f"*/*/{n}.parquet")) for n in
             ("posts", "interactions", "deletes", "account_events")}
    _, schemas = _arrow()
    empty = staging / "_empty"
    for n, files in globs.items():                       # read_parquet needs at least one file of each kind
        if not files:
            empty.mkdir(parents=True, exist_ok=True)
            import pyarrow.parquet as pq
            pq.write_table(pa.Table.from_pylist([], schema=schemas[n]), empty / f"{n}.parquet")
            globs[n] = [str(empty / f"{n}.parquet")]
    con = duckdb.connect()
    # the server laptop has 7.8 GB and runs the site and recorders too: cap DuckDB and let it spill to disk
    (proc / "duckdb_tmp").mkdir(parents=True, exist_ok=True)
    con.execute(f"SET memory_limit = '{os.environ.get('BSKY_NORMALIZE_MEMORY', '2GB')}'")
    con.execute(f"SET temp_directory = '{(proc / 'duckdb_tmp').as_posix()}'")
    con.execute("SET threads = 2")
    con.execute("SET TimeZone = 'UTC'")
    con.execute("SET preserve_insertion_order = false")
    for stmt, arg in zip([s for s in SQL.split(";") if s.strip()][:4],
                         [globs["deletes"], globs["account_events"], globs["posts"], globs["interactions"]]):
        con.execute(stmt, [arg])
    for stmt in [s for s in SQL.split(";") if s.strip()][4:]:
        con.execute(stmt)

    targets = bc.targets(cfg)
    con.register("targets", pa.Table.from_pylist([{"did": d, "side": s} for d, s in targets.items()],
                                                 schema=pa.schema([("did", pa.string()), ("side", pa.string())])))
    con.register("profiles", pa.Table.from_pylist(profiles_rows(raw), schema=pa.schema(
        [("did", pa.string()), ("handle", pa.string()), ("display_name", pa.string()), ("created_us", pa.int64()),
         ("self_labels", pa.list_(pa.string())), ("verified", pa.bool_())])))
    plc = plc_rows(raw)
    con.register("plc", pa.Table.from_pylist(plc, schema=pa.schema(
        [("did", pa.string()), ("op_type", pa.string()), ("handle", pa.string()), ("pds", pa.string()),
         ("rotation_keys_changed", pa.bool_()), ("created_us", pa.int64()), ("nullified", pa.bool_())])))
    labs = label_rows(raw)
    con.register("labels_raw", pa.Table.from_pylist(labs, schema=pa.schema(
        [("seq", pa.int64()), ("src", pa.string()), ("uri_or_did", pa.string()), ("val", pa.string()),
         ("neg", pa.bool_()), ("cts_us", pa.int64()), ("exp_us", pa.int64()), ("labeler", pa.string())])))

    def copy(name, select):
        tmp = tables / f"{name}.parquet.tmp"
        con.execute(f"COPY ({select}) TO '{tmp.as_posix()}' (FORMAT parquet, COMPRESSION zstd)")
        os.replace(tmp, tables / f"{name}.parquet")
        return con.execute(f"SELECT count(*) FROM read_parquet('{(tables / (name + '.parquet')).as_posix()}')").fetchone()[0]

    out = {}
    out["posts"] = copy("posts", f"SELECT uri, did, rkey, {_ts_cols(['created_us', 'indexed_us'])}, text, langs, "
                                 "reply_parent, reply_root, quote_uri, embed_type, facet_links, facet_mentions, sources "
                                 "FROM posts_kept ORDER BY did, rkey")
    out["interactions"] = copy("interactions", f"SELECT type, uri, actor_did, subject, list_uri, "
                                               f"{_ts_cols(['created_us', 'rkey_time_us'])}, time_us "
                                               "FROM inter_kept ORDER BY type, actor_did, uri")
    out["plc_ops"] = copy("plc_ops", f"SELECT did, op_type, handle, pds, rotation_keys_changed, "
                                     f"{_ts_cols(['created_us'])}, nullified FROM plc ORDER BY did, created_us")
    # labels: the newest event per (src, uri, val) wins; neg = true means the label was taken off
    out["labels"] = copy("labels", f"SELECT src, uri_or_did, val, neg, {_ts_cols(['cts_us', 'exp_us'])} FROM "
                                   "(SELECT *, row_number() OVER (PARTITION BY src, uri_or_did, val "
                                   "ORDER BY cts_us DESC NULLS LAST, seq DESC NULLS LAST) AS rn FROM labels_raw) "
                                   "WHERE rn = 1 ORDER BY src, uri_or_did, val")
    out["accounts"] = copy("accounts", f"""
        WITH everyone AS (
          SELECT did FROM profiles UNION SELECT did FROM plc WHERE did IS NOT NULL
          UNION SELECT did FROM posts_kept UNION SELECT actor_did FROM inter_kept),
        plc_now AS (
          SELECT did, arg_max(pds, created_us) FILTER (WHERE NOT nullified) AS pds,
                 arg_max(handle, created_us) FILTER (WHERE NOT nullified AND handle IS NOT NULL) AS handle
          FROM plc GROUP BY did),
        status AS (
          SELECT did, arg_max(coalesce(status, CASE WHEN active THEN 'active' END), time_us) AS status
          FROM read_parquet(?) GROUP BY did),
        sides AS (
          SELECT p.did, list_sort(list_distinct(list(t.side))) AS side_seen
          FROM posts_kept p JOIN targets t ON t.did = split_part(p.reply_root, '/', 3)
          WHERE p.did <> t.did GROUP BY p.did)
        SELECT e.did, coalesce(pr.handle, pl.handle) AS handle, pr.display_name,
               make_timestamp(pr.created_us) AS created_at,
               regexp_replace(pl.pds, '^https?://', '') AS pds_host,
               CASE WHEN coalesce(pr.handle, pl.handle) IS NULL THEN NULL
                    ELSE NOT ends_with(coalesce(pr.handle, pl.handle), '.bsky.social') END AS domain_handle,
               coalesce(pr.self_labels, []::VARCHAR[]) AS self_labels, pr.verified,
               coalesce(s.status, 'active') AS status,
               coalesce(sd.side_seen, []::VARCHAR[]) AS side_seen
        FROM everyone e
        LEFT JOIN profiles pr USING (did) LEFT JOIN plc_now pl USING (did)
        LEFT JOIN status s USING (did) LEFT JOIN sides sd USING (did)
        WHERE e.did IS NOT NULL ORDER BY e.did""".replace("read_parquet(?)", "read_parquet(" + repr(globs["account_events"]) + ")"))

    counts = con.execute("""
        SELECT (SELECT count(*) FROM p_all), (SELECT count(DISTINCT uri) FROM p_all),
               (SELECT count(*) FROM i_all), (SELECT count(DISTINCT uri) FROM i_all),
               (SELECT count(*) FROM dels), (SELECT count(*) FROM gone_accounts),
               (SELECT count(*) FROM (SELECT DISTINCT p.uri FROM p_all p JOIN dels d ON d.did = p.did
                  AND d.collection = 'app.bsky.feed.post' AND d.rkey = p.rkey)),
               (SELECT count(*) FROM (SELECT DISTINCT i.uri FROM i_all i JOIN dels d ON d.did = i.actor_did
                  AND d.rkey = split_part(i.uri, '/', 5) AND d.collection = split_part(i.uri, '/', 4)))
    """).fetchone()
    out["in"] = {"post_rows": counts[0], "distinct_posts": counts[1], "interaction_rows": counts[2],
                 "distinct_interactions": counts[3], "deleted_records": counts[4], "deleted_accounts": counts[5],
                 "posts_with_a_delete": counts[6], "interactions_with_a_delete": counts[7],
                 "label_events": len(labs), "plc_operations": len(plc)}
    con.close()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(bc.CONFIG))
    ap.add_argument("--full", action="store_true", help="stage every raw file again")
    a = ap.parse_args()
    cfg = bc.load_config(a.config)
    data = bc.data_dir()
    t0 = time.time()
    staged = stage_all(data, full=a.full)
    tables = build_tables(data, cfg)
    report = {"run": bc.now_iso(), "seconds": round(time.time() - t0, 1), "staged_this_run": staged, "tables": tables}
    bc.atomic_json(data / "processed" / "normalize_report.json", report)
    print("normalize", json.dumps(tables))


if __name__ == "__main__":
    main()
