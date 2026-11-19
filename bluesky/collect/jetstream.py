#!/usr/bin/env python3
"""Bounded Jetstream recorder for the Bluesky politics module (read-only; it never posts, likes or follows).

Connects to Jetstream, receives every event in the six collections from targets.yaml, and keeps only events
that touch the target accounts or the people replying to them:

  kept if   the author is a target or a known replier
       or   the event points at one (reply to, quote of, like or repost of their post; follow, block or
            list entry naming them)
  repliers  an account joins the replier set the first time it replies in a thread a target started, or
            directly to a target. The set only grows, up to limits.max_replier_set.
  deletes   kept for any account that authored a kept record, so the normalize step can drop deleted records.
  identity / account events (handle changes, deactivations, takedowns): kept for the same accounts.

Files under <data>/raw/jetstream/:
  YYYY-MM-DDTHH.jsonl       the open hour, raw Jetstream lines, filed by the event's own time
  YYYY-MM-DDTHH.jsonl.gz    finished hours
  sessions.jsonl            one line per connection: host, start, end, reason, cursor asked for, first and last
                            event time, counts. A gap is a session whose first event is later than its cursor.
Files under <data>/state/:
  cursor.json               time_us of the last event handled, saved every minute
  repliers.txt, seen_authors.txt   one DID per line, append-only
  jetstream.pid
Status (<data>/../bluesky_status/status.json): counts only. No DID, handle or text ever goes there.

Resume: on start, and after every drop, it reconnects with cursor = saved cursor minus 5 seconds, so nothing
is lost and a few seconds are duplicated (normalize dedups on did/collection/rkey/rev). Jetstream replayed
about 37 hours on Nov 19 2026 (both hosts); an outage longer than the buffer is a real gap and shows up in
sessions.jsonl.

Patterned on scripts/dgg_live_logger.py, including its two fixes: a connection that goes silent is dropped
after IDLE_S seconds instead of waited on forever, and every drop is logged with a reason.

Needs: websockets, PyYAML (bluesky/requirements.txt).
"""
import argparse
import asyncio
import collections
import datetime as dt
import gzip
import json
import os
import shutil
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I leaves the script's folder off sys.path
import bsky_common as bc  # noqa: E402

IDLE_S = 60        # the full network is never silent this long
REWIND_US = 5_000_000
BUFFER_HOURS = 36  # measured replay depth was about 37 h on Nov 19 2026


def hour_of(time_us):
    return dt.datetime.fromtimestamp(time_us / 1e6, dt.timezone.utc).strftime("%Y-%m-%dT%H")


def subjects(collection, record):
    """DIDs an event points at, and whether it is a reply (root DID, parent DID)."""
    out, reply = [], None
    if collection == "app.bsky.feed.post":
        r = record.get("reply") or {}
        root = bc.did_of((r.get("root") or {}).get("uri"))
        parent = bc.did_of((r.get("parent") or {}).get("uri"))
        if root or parent:
            reply = (root, parent)
            out += [root, parent]
        emb = record.get("embed") or {}
        rec = emb.get("record") or {}
        # quote post: embed.record.uri; quote with media: embed.record.record.uri
        out.append(bc.did_of(rec.get("uri") or (rec.get("record") or {}).get("uri")))
    elif collection in ("app.bsky.feed.like", "app.bsky.feed.repost"):
        out.append(bc.did_of((record.get("subject") or {}).get("uri")))
    elif collection in ("app.bsky.graph.follow", "app.bsky.graph.block", "app.bsky.graph.listitem"):
        s = record.get("subject")
        out.append(s if isinstance(s, str) and s.startswith("did:") else None)
    return [d for d in out if d], reply


class Recorder:
    def __init__(self, out, state, status, targets, max_repliers=200000, clock=time.time):
        self.out, self.state, self.status_dir = Path(out), Path(state), Path(status)
        for d in (self.out, self.state, self.status_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.targets = set(targets)
        self.max_repliers = max_repliers
        self.clock = clock
        self.repliers = self._load_set("repliers.txt")
        self.seen = self._load_set("seen_authors.txt")
        self._rep_fh = open(self.state / "repliers.txt", "a", buffering=1)
        self._seen_fh = open(self.state / "seen_authors.txt", "a", buffering=1)
        self.hour, self.fh = None, None
        self.cursor = bc.load_json(self.state / "cursor.json", {}).get("time_us")
        self.last_us = None
        self.last_save = 0
        self.last_status = 0
        self.counts = collections.Counter()      # since start: seen:<collection>, kept:<collection>, kept:<why>
        self.per_min = collections.Counter()     # minute -> kept, last 3 hours
        self.bytes_in = 0
        self.session = None
        self.started = bc.now_iso()
        self.host = None
        self._compress_closed()

    def _load_set(self, name):
        try:
            with open(self.state / name, encoding="utf-8") as f:
                return {line.strip() for line in f if line.startswith("did:")}
        except FileNotFoundError:
            return set()

    # ---- files ----
    def _compress_closed(self):
        for p in self.out.glob("*.jsonl"):
            if p.name[:4].isdigit() and p.stem != self.hour:
                with open(p, "rb") as a, gzip.open(str(p) + ".gz", "ab") as b:  # "ab": a replayed hour appends
                    shutil.copyfileobj(a, b)
                p.unlink()

    def _write(self, time_us, raw):
        h = hour_of(time_us)
        if h != self.hour:
            if self.fh:
                self.fh.close()
            self.hour = h
            self.fh = open(self.out / f"{h}.jsonl", "a", buffering=1, encoding="utf-8")
            self._compress_closed()
        self.fh.write(raw.rstrip("\n") + "\n")

    # ---- filter ----
    def decide(self, ev):
        """Why an event is kept (a short word), or None. Grows the replier and seen-author sets."""
        did = ev.get("did")
        kind = ev.get("kind")
        tracked = did in self.targets or did in self.repliers
        if kind in ("identity", "account"):
            return kind if tracked or did in self.seen else None
        if kind != "commit":
            return None
        c = ev.get("commit") or {}
        coll = c.get("collection", "")
        self.counts["seen:" + coll] += 1
        if c.get("operation") == "delete":
            return "delete" if tracked or did in self.seen else None
        subs, reply = subjects(coll, c.get("record") or {})
        why = None
        if reply and did not in self.targets and (reply[0] in self.targets or reply[1] in self.targets):
            why = "reply_to_target"
            if did not in self.repliers:
                if len(self.repliers) < self.max_repliers:
                    self.repliers.add(did)
                    self._rep_fh.write(did + "\n")
                else:
                    self.counts["replier_cap_hits"] += 1
        elif tracked:
            why = "author"
        elif any(s in self.targets for s in subs):
            why = "points_at_target"
        elif any(s in self.repliers for s in subs):
            why = "points_at_replier"
        if why and not tracked and did not in self.seen and did not in self.repliers:
            self.seen.add(did)
            self._seen_fh.write(did + "\n")
        if why:
            self.counts["kept:" + coll] += 1
        return why

    def handle(self, raw):
        self.bytes_in += len(raw)
        try:
            ev = json.loads(raw)
        except json.JSONDecodeError:
            self.counts["bad_json"] += 1
            return
        t = ev.get("time_us")
        if not isinstance(t, int):
            return
        if self.session is not None:
            self.session["events"] += 1
            self.session.setdefault("first_time_us", t)
            self.session["last_time_us"] = t
        why = self.decide(ev)
        if why:
            self._write(t, raw)
            self.counts["kept:" + why] += 1
            self.per_min[int(self.clock() // 60)] += 1
            if self.session is not None:
                self.session["kept"] += 1
        self.last_us = t
        now = self.clock()
        if now - self.last_save >= 60:
            self.save_cursor()
        if now - self.last_status >= 5:
            self.write_status()

    # ---- state ----
    def save_cursor(self):
        if self.last_us:
            self.cursor = self.last_us
            bc.atomic_json(self.state / "cursor.json", {"time_us": self.last_us, "saved": bc.now_iso()})
        self.last_save = self.clock()

    def resume_cursor(self):
        return self.cursor - REWIND_US if self.cursor else None

    def open_session(self, host):
        self.host = host
        self.session = {"host": host, "start": bc.now_iso(), "cursor": self.resume_cursor(), "events": 0, "kept": 0}
        if self.cursor and self.clock() - self.cursor / 1e6 > BUFFER_HOURS * 3600:
            self.session["gap_possible"] = "saved cursor is older than the replay buffer"

    def close_session(self, reason):
        if self.session is None:
            return
        s = self.session
        s["end"], s["reason"] = bc.now_iso(), reason
        if s.get("cursor") and s.get("first_time_us"):
            # seconds between the cursor asked for and the first event received; near 0 means no gap
            s["resume_gap_s"] = round((s["first_time_us"] - s["cursor"]) / 1e6, 1)
        with open(self.out / "sessions.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(s) + "\n")
        self.session = None
        self.save_cursor()
        self.write_status()

    def _recent_sessions(self):
        try:
            with open(self.out / "sessions.jsonl", encoding="utf-8") as f:
                return [json.loads(line) for line in f.readlines()[-8:]]
        except Exception:
            return []

    def write_status(self):
        now = self.clock()
        self.last_status = now
        cutoff = int(now // 60) - 180
        for k in [k for k in self.per_min if k < cutoff]:
            del self.per_min[k]
        bc.atomic_json(self.status_dir / "status.json", {
            "updated": bc.now_iso(),
            "started": self.started,
            "connected": self.session is not None,
            "host": self.host,
            "lag_seconds": round(now - self.last_us / 1e6, 1) if self.last_us else None,
            "last_event": dt.datetime.fromtimestamp(self.last_us / 1e6, dt.timezone.utc).isoformat(
                timespec="seconds") if self.last_us else None,
            "counts_since_start": dict(sorted(self.counts.items())),
            "megabytes_received": round(self.bytes_in / 1e6, 1),
            "targets": len(self.targets),
            "repliers": len(self.repliers),
            "other_authors_seen": len(self.seen),
            "kept_per_minute": [[k * 60, self.per_min.get(k, 0)] for k in range(cutoff, int(now // 60) + 1)],
            "recent_sessions": self._recent_sessions(),
        })

    def close(self):
        for fh in (self.fh, self._rep_fh, self._seen_fh):
            if fh:
                fh.close()
        self.fh = None


def stream_url(host, collections_, cursor):
    q = "&".join("wantedCollections=" + c for c in collections_)
    return f"wss://{host}/subscribe?{q}" + (f"&cursor={cursor}" if cursor else "")


class Stalled(Exception):
    pass


async def run(rec, hosts, collections_, user_agent, deadline=None):
    import websockets
    delay, i = 5, 0
    while deadline is None or time.time() < deadline:
        host = hosts[i % len(hosts)]
        reason = "closed"
        try:
            url = stream_url(host, collections_, rec.resume_cursor())
            async with websockets.connect(url, additional_headers={"User-Agent": user_agent},
                                          max_size=2**22) as ws:
                rec.open_session(host)
                delay = 5
                while True:
                    left = None if deadline is None else deadline - time.time()
                    if left is not None and left <= 0:
                        reason = "time limit"
                        return
                    try:
                        raw = await asyncio.wait_for(ws.recv(), min(IDLE_S, left) if left else IDLE_S)
                    except asyncio.TimeoutError:
                        if left is not None and deadline - time.time() <= 0:
                            reason = "time limit"
                            return
                        raise Stalled(f"no message for {IDLE_S} s") from None
                    rec.handle(raw if isinstance(raw, str) else raw.decode("utf-8", "replace"))
        except asyncio.CancelledError:
            reason = "stopped"
            raise
        except Exception as e:
            reason = type(e).__name__
            i += 1  # try the other host next
        finally:
            rec.close_session(reason)
        await asyncio.sleep(delay)
        delay = min(delay * 2, 300)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(bc.CONFIG))
    ap.add_argument("--hours", type=float, help="stop after this many hours (the pilot uses 24)")
    args = ap.parse_args()
    cfg = bc.load_config(args.config)
    d = bc.data_dir()
    rec = Recorder(d / "raw" / "jetstream", d / "state", bc.status_dir(), bc.targets(cfg),
                   cfg["limits"]["max_replier_set"])
    pid = d / "state" / "jetstream.pid"
    pid.write_text(str(os.getpid()))
    deadline = time.time() + args.hours * 3600 if args.hours else None
    print(f"bsky_recorder start {bc.now_iso()} targets={len(rec.targets)} repliers={len(rec.repliers)} "
          f"resume={'yes' if rec.cursor else 'no'}", flush=True)
    loop = asyncio.new_event_loop()
    task = loop.create_task(run(rec, cfg["collect"]["jetstream_hosts"], cfg["collect"]["wanted_collections"],
                                cfg["collect"]["user_agent"], deadline))
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, task.cancel)
    how = "done: time limit reached"
    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        how = "stopped by signal"
    finally:
        rec.save_cursor()
        rec.write_status()
        rec.close()
        pid.unlink(missing_ok=True)
        print(f"bsky_recorder end {bc.now_iso()} ({how})", flush=True)


if __name__ == "__main__":
    main()
