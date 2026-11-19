#!/usr/bin/env python3
"""AppView and PDS collector: target handles, target threads, replier profiles, replier histories.

Subcommands (each resumes where it stopped; each prints counts only):

  resolve     Re-resolve every handle in targets.yaml and compare with the DID written there. Exit 1 on any
              mismatch. Run this first on the laptop.
  threads     For each target: page getAuthorFeed back to --since, then getPostThread for each of the
              target's own posts. A thread is fetched again while its post is under 48 hours old and the
              last fetch is over 6 hours old; after that it is final.
  profiles    getProfiles in batches of 25 for the replier set.
  histories   For each replier: com.atproto.repo.listRecords on the account's own PDS, starting AT THE ANCHOR
              and paging backwards, until 1,000 top-level posts and 1,000 replies are held (limits in
              targets.yaml). This replaces getAuthorFeed for histories: getAuthorFeed pages newest-first from
              now, which is the pull that produced the Reddit cap artifact (RECON 3.5). Checked Nov 19 2026:
              a record key built from the anchor time works as the listRecords cursor.

Known limits, to be measured in the pilot:
  - getPostThread does not return every reply of a very large thread. The Jetstream recording is the complete
    source for replies made while it runs; threads fill in what came before.
  - listRecords returns the record as written. It has no indexedAt and no like counts, and record keys are
    chosen by the client, so a key that isn't a time-ordered TID is counted in `non_tid_keys`.
  - listRecords needs the account's PDS host (from its PLC log, see plc.py). Accounts whose PDS can't be
    found fall back to collect.pds_fallback.
  - A deactivated or taken-down account returns 400 and is recorded as `gone`, with no history. Report that
    count next to every Tier A result (RECON 3.10).

Files under <data>/raw/ (private):
  threads/<target key>/<rkey>.json.gz, threads/index.jsonl
  profiles/part-NNNN.jsonl.gz, profiles/done.txt
  histories/<aa>/<did>.jsonl.gz, histories/<aa>/<did>.done.json
"""
import argparse
import datetime as dt
import gzip
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bsky_common as bc  # noqa: E402
import plc  # noqa: E402

POST = "app.bsky.feed.post"
REFETCH_AGE_H, REFETCH_EVERY_H = 48, 6


def _key(did):
    return did.replace(":", "_")


def _read_dids(path):
    try:
        with open(path, encoding="utf-8") as f:
            return list(dict.fromkeys(x.strip() for x in f if x.startswith("did:")))
    except FileNotFoundError:
        return []


# ---------------------------------------------------------------- resolve
def resolve(cfg, http):
    bad, n = [], 0
    for side, rows in cfg["sides"].items():
        for i, t in enumerate(rows):
            for h in filter(None, (t["handle"], t.get("alias"))):
                n += 1
                r = http.get("xrpc/com.atproto.identity.resolveHandle", {"handle": h}, ok_missing=True)
                if not r or r.get("did") != t["did"]:
                    bad.append(f"{side} #{i + 1} ({'alias' if h != t['handle'] else 'handle'})")
    return n, bad


# ---------------------------------------------------------------- threads
def target_posts(http, did, since_us, max_pages=50):
    """URIs and creation times of a target's own posts since a time, newest first. Reposts are skipped."""
    out, cursor = [], None
    for _ in range(max_pages):
        p = {"actor": did, "limit": 100, "filter": "posts_and_author_threads"}
        if cursor:
            p["cursor"] = cursor
        r = http.get("xrpc/app.bsky.feed.getAuthorFeed", p, ok_missing=True)
        if not r:
            break
        older = False
        for item in r.get("feed") or []:
            post = item.get("post") or {}
            if item.get("reason") or (post.get("author") or {}).get("did") != did:
                continue
            created = (post.get("record") or {}).get("createdAt")
            try:
                us = bc.iso_to_us(created)
            except Exception:
                continue
            if us < since_us:
                older = True
                continue
            out.append({"uri": post["uri"], "created_us": us, "reply_count": post.get("replyCount")})
        cursor = r.get("cursor")
        if older or not cursor:
            break
    return out


def thread_repliers(node, out=None):
    """Author DIDs of every reply in a getPostThread tree."""
    out = set() if out is None else out
    for rep in (node or {}).get("replies") or []:
        did = ((rep.get("post") or {}).get("author") or {}).get("did")
        if did:
            out.add(did)
        thread_repliers(rep, out)
    return out


def should_fetch(last, created_us, now_us):
    """last: the newest index line for this post, or None."""
    if last is None:
        return True
    if last.get("final"):
        return False
    return now_us - bc.iso_to_us(last["fetched"]) >= REFETCH_EVERY_H * 3600e6


def threads(cfg, http, root, since_us, state, clock=time.time):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    index = root / "index.jsonl"
    last = {}
    if index.exists():
        for line in open(index, encoding="utf-8"):
            j = json.loads(line)
            last[j["uri"]] = j
    n = {"targets": 0, "posts": 0, "fetched": 0, "skipped": 0, "missing": 0, "replies_returned": 0}
    repliers = set()
    for did in bc.targets(cfg):
        n["targets"] += 1
        for post in target_posts(http, did, since_us):
            n["posts"] += 1
            now_us = int(clock() * 1e6)
            if not should_fetch(last.get(post["uri"]), post["created_us"], now_us):
                n["skipped"] += 1
                continue
            r = http.get("xrpc/app.bsky.feed.getPostThread",
                         {"uri": post["uri"], "depth": 1000, "parentHeight": 0}, ok_missing=True)
            if not r:
                n["missing"] += 1
                continue
            rkey = post["uri"].rsplit("/", 1)[1]
            dest = root / _key(did) / f"{rkey}.json.gz"
            dest.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(dest, "wt", encoding="utf-8") as f:
                json.dump(r, f)
            got = thread_repliers(r.get("thread"))
            repliers |= got - set(bc.targets(cfg))
            line = {"uri": post["uri"], "fetched": bc.now_iso(), "reply_count": post["reply_count"],
                    "repliers_returned": len(got),
                    "final": now_us - post["created_us"] >= REFETCH_AGE_H * 3600e6}
            with open(index, "a", encoding="utf-8") as f:
                f.write(json.dumps(line) + "\n")
            n["fetched"] += 1
            n["replies_returned"] += len(got)
    known = set(_read_dids(Path(state) / "thread_repliers.txt"))
    Path(state).mkdir(parents=True, exist_ok=True)
    with open(Path(state) / "thread_repliers.txt", "a", encoding="utf-8") as f:
        for did in sorted(repliers - known):
            f.write(did + "\n")
    n["new_repliers"] = len(repliers - known)
    return n


# ---------------------------------------------------------------- profiles
def profiles(http, root, dids, limit=0):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    done = set(_read_dids(root / "done.txt"))
    todo = [d for d in dids if d not in done]
    if limit:
        todo = todo[:limit]
    n = {"already": len(done), "asked": 0, "returned": 0}
    part = len(list(root.glob("part-*.jsonl.gz")))
    if not todo:
        return n
    with gzip.open(root / f"part-{part:04d}.jsonl.gz", "wt", encoding="utf-8") as out, \
            open(root / "done.txt", "a", encoding="utf-8") as mark:
        for i in range(0, len(todo), 25):
            batch = todo[i:i + 25]
            r = http.get("xrpc/app.bsky.actor.getProfiles", {"actors": batch}, ok_missing=True) or {}
            fetched = bc.now_iso()
            for p in r.get("profiles") or []:
                out.write(json.dumps({"fetched": fetched, "profile": p}) + "\n")
                n["returned"] += 1
            n["asked"] += len(batch)
            mark.write("\n".join(batch) + "\n")   # accounts not returned are deactivated, taken down or gone
            mark.flush()
    return n


# ---------------------------------------------------------------- histories
def history(pds, did, anchor_us, cap_posts, cap_replies, max_pages=60):
    """Records at or before the anchor, newest first, until both caps are full. Returns (records, summary)."""
    cursor = bc.tid_from_us(anchor_us + 1)
    recs, n_post, n_reply, non_tid, pages, why = [], 0, 0, 0, 0, "exhausted"
    while True:
        if pages >= max_pages:
            why = "page limit"
            break
        r = pds.get("xrpc/com.atproto.repo.listRecords",
                    {"repo": did, "collection": POST, "limit": 100, "cursor": cursor}, ok_missing=True)
        pages += 1
        if r is None:
            return [], {"gone": True, "pages": pages}
        batch = r.get("records") or []
        for rec in batch:
            rkey = rec["uri"].rsplit("/", 1)[1]
            if bc.tid_to_us(rkey) is None:
                non_tid += 1
            is_reply = bool((rec.get("value") or {}).get("reply"))
            if is_reply and n_reply < cap_replies:
                n_reply += 1
                recs.append(rec)
            elif not is_reply and n_post < cap_posts:
                n_post += 1
                recs.append(rec)
        cursor = r.get("cursor")
        if n_post >= cap_posts and n_reply >= cap_replies:
            why = "both caps full"
            break
        if not cursor or not batch:
            break
    return recs, {"gone": False, "pages": pages, "posts": n_post, "replies": n_reply, "non_tid_keys": non_tid,
                  "ended": why, "anchor_us": anchor_us}


def histories(cfg, root, dids, anchors, default_anchor_us, limit=0, plc_http=None, log_dir=None):
    root = Path(root)
    c = cfg["collect"]
    lim = cfg["limits"]
    pds_clients = {}
    n = {"already": 0, "pulled": 0, "gone": 0, "records": 0, "fallback_pds": 0}
    for did in dids:
        done = root / did[-2:] / (_key(did) + ".done.json")
        if done.exists():
            n["already"] += 1
            continue
        host = plc.pds_of(plc.audit(plc_http, bc.data_dir() / "raw" / "plc", did)) if plc_http else None
        if not host:
            host = c["pds_fallback"]
            n["fallback_pds"] += 1
        if host not in pds_clients:
            pds_clients[host] = bc.Http("pds", host, c["rate"]["pds"], c["user_agent"], log_dir)
        try:
            recs, summary = history(pds_clients[host], did, anchors.get(did, default_anchor_us),
                                    lim["history_posts_per_account"], lim["history_replies_per_account"])
        except Exception as e:      # an unreachable self-hosted PDS must not stop the pass
            recs, summary = [], {"gone": False, "failed": type(e).__name__}
        done.parent.mkdir(parents=True, exist_ok=True)
        if recs:
            with gzip.open(done.with_name(_key(did) + ".jsonl.gz"), "wt", encoding="utf-8") as f:
                for rec in recs:
                    f.write(json.dumps(rec) + "\n")
        if "failed" not in summary:  # failures are retried on the next pass
            bc.atomic_json(done, {**summary, "fetched": bc.now_iso()})
        n["gone" if summary.get("gone") else "pulled"] += 1
        n["records"] += len(recs)
        if limit and n["pulled"] + n["gone"] >= limit:
            break
    for h in pds_clients.values():
        h.flush()
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["resolve", "threads", "profiles", "histories"])
    ap.add_argument("--since", help="threads: ISO date or time; default 48 hours ago")
    ap.add_argument("--dids", help="profiles/histories: file with one DID per line (default: the replier set)")
    ap.add_argument("--anchor", help="histories: ISO time every history ends at; default now")
    ap.add_argument("--limit", type=int, default=0, help="profiles/histories: stop after this many accounts")
    args = ap.parse_args()
    cfg = bc.load_config()
    d = bc.data_dir()
    cl = bc.clients(cfg)
    http = cl["appview"]
    if args.cmd == "resolve":
        n, bad = resolve(cfg, http)
        print("resolve", json.dumps({"handles_checked": n, "mismatches": bad}))
        http.flush()
        sys.exit(1 if bad else 0)
    dids = _read_dids(args.dids) if args.dids else list(dict.fromkeys(
        _read_dids(d / "state" / "repliers.txt") + _read_dids(d / "state" / "thread_repliers.txt")))
    if args.cmd == "threads":
        since = bc.iso_to_us(args.since) if args.since else int((time.time() - 48 * 3600) * 1e6)
        out = threads(cfg, http, d / "raw" / "threads", since, d / "state")
    elif args.cmd == "profiles":
        out = profiles(http, d / "raw" / "profiles", dids, args.limit)
    else:
        anchor = bc.iso_to_us(args.anchor) if args.anchor else int(time.time() * 1e6)
        out = histories(cfg, d / "raw" / "histories", dids, {}, anchor, args.limit, cl["plc"], d / "logs")
        cl["plc"].flush()
    http.flush()
    print(args.cmd, json.dumps(out), "requests", json.dumps(http.total),
          dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))


if __name__ == "__main__":
    main()
