#!/usr/bin/env python3
"""Daily, capped history pull for the accounts replying to the targets during the observation window.

    python -I bluesky/collect/history_daily.py              one capped run (the scheduled job)
    python -I bluesky/collect/history_daily.py --plan       queue counts only: no request is made
    python -I bluesky/collect/history_daily.py --accounts 5 a smaller run (e.g. a by-hand check)

Written Nov 27 2026; the owner approved a daily, capped pull of replier histories that day (VERIFIED.md, "Histories
are not being pulled"). Without it prediction 7 and every Tier A recall would count only the pilot accounts.

The queue: every account with at least one reply in the window (targets.yaml window.start to window.end, by the
record's createdAt) in a thread a target started or directly to a target, targets excluded: the frozen in-thread
replier definition, read from the recorder's finished hour files. Hours already read are remembered, so each run
reads only the new ones.

Order: accounts never pulled first (most window replies first, then the earliest first reply), then accounts whose
last pull is oldest. An account pulled in the last `repull_after_days` days is skipped. A pilot history
(appview.py histories, Nov 19-20) counts as a pull at its own fetch time.

The pull itself is appview.history: com.atproto.repo.listRecords on the account's own PDS (found from its PLC log),
newest first from the pull time, until the targets.yaml caps (1,000 top-level posts and 1,000 replies) are full.
That is the same request and file format as the pilot histories, so normalize stages them as source 'history' and
the scorer's "has a history" sees them. (getAuthorFeed is not used, see appview.py's docstring.)

Caps (targets.yaml history_daily): accounts per run, requests per run (every attempt to any host, retries
included), minutes per run (no account is started after it), and a minimum gap between any two requests on top of the per-host rates. An account is started only if
the requests left cover its worst case (max_pages + 1), so the cap never cuts an account in half. 429 and 5xx back
off inside bsky_common.Http; after `stop_after_throttled` accounts in a row that a host kept refusing, the run stops.

Writes only new files; nothing that exists is changed:
  first pull   raw/histories/<aa>/<did>.jsonl.gz and .done.json (the pilot layout); skipped if .done.json exists.
               A .jsonl.gz left without its .done.json by a crash is incomplete and is replaced by the new pull.
  re-pull      raw/histories_daily/<aa>/<did>/<UTC stamp>.jsonl.gz: only records whose URI is not already held for
               the account, from the pull time back to the previous pull's anchor. normalize does not read this
               folder yet (re-pulls start only after every queued account has a first pull).
  ledger       state/history_daily/pulls.jsonl, one line per account attempt (private: it holds DIDs)
  queue state  state/history_daily/window_repliers.json (private)
  status       bluesky_status/histories.json: counts only, no DID, handle or text.
A lock file (state/history_daily.lock) stops a second copy.

Running next to normalize (the nightly run, 01:00-06:50, overlaps the 04:30 bsky normalize; checked Nov 27 2026):
normalize reads raw/histories/*/*.jsonl.gz and raw/plc/*/*.json, which this job writes, and nothing under
histories_daily or state/history_daily. Every file here is written to <name>.tmp and renamed into place
(_write_gz, bc.atomic_json), and the .tmp names match neither glob, so normalize sees a file whole or not at all;
a file that lands after normalize listed its folder is staged the next night. Existing files are never deleted.
"""
import argparse
import datetime as dt
import gzip
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import appview  # noqa: E402
import bsky_common as bc  # noqa: E402
import plc  # noqa: E402

POST = "app.bsky.feed.post"
DAY_US = 86_400_000_000
DEFAULTS = {"accounts_per_run": 1200, "requests_per_run": 50000, "repull_after_days": 14, "min_gap_s": 0.4,
            "stop_after_throttled": 3, "max_pages": 60, "max_minutes": 350}


class BudgetExhausted(Exception):
    """The run's request cap is reached. Not an HTTP error, so bsky_common.Http does not retry it."""


class Budget:
    """Counts every network attempt across all hosts, holds a minimum gap between any two, and stops at the cap.

    It wraps the urlopen each Http uses, so retries after a 429 or 5xx count against the cap too."""

    def __init__(self, cap, min_gap_s=0.0, opener=None, sleep=time.sleep, clock=time.time):
        self.cap, self.gap = int(cap), float(min_gap_s)
        self.used = 0
        self.inner = opener
        self.sleep, self.clock = sleep, clock
        self.last = None

    def left(self):
        return self.cap - self.used

    def opener(self, req, timeout=None):
        if self.used >= self.cap:
            raise BudgetExhausted(f"request cap {self.cap} reached")
        if self.last is not None:
            wait = self.last + self.gap - self.clock()
            if wait > 0:
                self.sleep(wait)
        self.last = self.clock()
        self.used += 1
        return (self.inner or urllib.request.urlopen)(req, timeout=timeout)


def _key(did):
    return did.replace(":", "_")


def _iso(us):
    return dt.datetime.fromtimestamp(us / 1e6, dt.timezone.utc).isoformat(timespec="seconds")


def _hour_us(name):
    """'2026-11-27T05' -> microseconds."""
    return bc.iso_to_us(name + ":00:00+00:00")


# ------------------------------------------------------------------------------------------------ the queue
def reply_in_window(ev, targets, start_us, end_us):
    """The author's DID if this Jetstream line is a reply to a target thread inside the window, else None."""
    if ev.get("kind") != "commit":
        return None, None
    c = ev.get("commit") or {}
    if c.get("collection") != POST or c.get("operation") != "create":
        return None, None
    did = ev.get("did")
    rec = c.get("record") or {}
    reply = rec.get("reply") or {}
    if not did or did in targets or not reply:
        return None, None
    root = bc.did_of((reply.get("root") or {}).get("uri"))
    parent = bc.did_of((reply.get("parent") or {}).get("uri"))
    if root not in targets and parent not in targets:
        return None, None
    try:
        t = bc.iso_to_us(rec.get("createdAt"))
    except Exception:
        t = ev.get("time_us")
    if not isinstance(t, int) or not start_us <= t < end_us:
        return None, None
    return did, t


def scan_window(jet_dir, targets, start_us, end_us, state):
    """Add the replies in finished hour files not read before to state {"hours": [...], "repliers": {did: [n, first_us]}}."""
    jet_dir = Path(jet_dir)
    done = set(state.setdefault("hours", []))
    reps = state.setdefault("repliers", {})
    n = {"hours_read": 0, "replies": 0, "new_accounts": 0}
    files = sorted(jet_dir.glob("20*.jsonl.gz")) if jet_dir.is_dir() else []
    for p in files:
        hour = p.name[:-len(".jsonl.gz")]
        if hour in done or (jet_dir / p.name[:-3]).exists():       # read before, or still being written
            continue
        try:
            h_us = _hour_us(hour)
        except ValueError:
            continue
        if h_us + 3600e6 <= start_us - 3600e6 or h_us >= end_us + 3600e6:   # an hour of slack for clock skew
            continue
        try:
            with gzip.open(p, "rt", encoding="utf-8") as f:
                for line in f:
                    if '"reply"' not in line:
                        continue
                    try:
                        ev = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    did, t = reply_in_window(ev, targets, start_us, end_us)
                    if not did:
                        continue
                    n["replies"] += 1
                    r = reps.get(did)
                    if r is None:
                        reps[did] = [1, t]
                        n["new_accounts"] += 1
                    else:
                        r[0] += 1
                        r[1] = min(r[1], t)
        except (EOFError, OSError):
            continue                                                 # a damaged file is tried again next run
        state["hours"].append(hour)
        done.add(hour)
        n["hours_read"] += 1
    return n


def last_pulls(hist_root, ledger):
    """{did: time_us of the newest completed pull}: pilot .done.json files plus this job's ledger."""
    out = {}
    root = Path(hist_root)
    for p in root.glob("*/*.done.json") if root.is_dir() else []:
        j = bc.load_json(p, {})
        try:
            t = bc.iso_to_us(j["fetched"])
        except Exception:
            t = j.get("anchor_us") if isinstance(j.get("anchor_us"), int) else 0
        out[p.name[:-len(".done.json")].replace("_", ":", 2)] = t
    if Path(ledger).exists():
        with open(ledger, encoding="utf-8") as f:
            for line in f:
                try:
                    j = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if j.get("failed") or not j.get("did"):
                    continue
                t = bc.iso_to_us(j["at"])
                if t > out.get(j["did"], -1):
                    out[j["did"]] = t
    return out


def plan(repliers, last, now_us, repull_after_days, cap):
    """The accounts to pull this run, in order, and the queue counts."""
    min_age = repull_after_days * DAY_US
    never = [d for d in repliers if d not in last]
    due = [d for d in repliers if d in last and now_us - last[d] >= min_age]
    never.sort(key=lambda d: (-repliers[d][0], repliers[d][1], d))
    due.sort(key=lambda d: (last[d], d))
    order = never + due
    counts = {"window_repliers": len(repliers), "never_pulled": len(never), "due_for_repull": len(due),
              "pulled_recently": len(repliers) - len(never) - len(due)}
    return order[:cap] if cap else order, counts


# ------------------------------------------------------------------------------------------------ one account
def held_uris(hist_root, daily_root, did):
    """URIs already on disk for the account and the newest anchor among its pulls."""
    uris, anchor = set(), None
    canon = Path(hist_root) / did[-2:] / (_key(did) + ".jsonl.gz")
    files = [canon] if canon.exists() else []
    d = Path(daily_root) / did[-2:] / _key(did)
    files += sorted(d.glob("*.jsonl.gz")) if d.is_dir() else []
    for p in files:
        try:
            with gzip.open(p, "rt", encoding="utf-8") as f:
                for line in f:
                    try:
                        uris.add(json.loads(line)["uri"])
                    except (json.JSONDecodeError, KeyError):
                        pass
        except (EOFError, OSError):
            pass
    for meta in [Path(hist_root) / did[-2:] / (_key(did) + ".done.json")] + (sorted(d.glob("*.done.json")) if d.is_dir() else []):
        a = bc.load_json(meta, {}).get("anchor_us")
        if isinstance(a, int) and (anchor is None or a > anchor):
            anchor = a
    return uris, anchor


def history_since(pds, did, anchor_us, since_us, max_pages):
    """Records from the anchor back to since_us (exclusive), newest first. Returns (records, summary)."""
    cursor = bc.tid_from_us(anchor_us + 1)
    recs, pages, why = [], 0, "exhausted"
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
        older = False
        for rec in batch:
            t = bc.tid_to_us(rec["uri"].rsplit("/", 1)[1])
            if t is not None and t <= since_us:
                older = True
                continue
            recs.append(rec)
        cursor = r.get("cursor")
        if older:
            why = "reached the previous pull"
            break
        if not cursor or not batch:
            break
    return recs, {"gone": False, "pages": pages, "ended": why, "anchor_us": anchor_us, "since_us": since_us}


def _write_gz(path, recs):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as f:
        for rec in recs:
            f.write(json.dumps(rec) + "\n")
    os.replace(tmp, path)


def pull_one(did, ctx, now_us):
    """Pull one account. Returns the ledger line (with the DID; it goes only to the private ledger)."""
    hist, daily, lim = ctx["hist_root"], ctx["daily_root"], ctx["limits"]
    done = hist / did[-2:] / (_key(did) + ".done.json")
    host = plc.pds_of(plc.audit(ctx["plc"], ctx["plc_root"], did)) if ctx["plc"] else None
    if not host:
        host = ctx["fallback"]
    pds = ctx["pds_client"](host)
    stamp = dt.datetime.fromtimestamp(now_us / 1e6, dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    line = {"did": did, "at": _iso(now_us), "fallback_pds": host == ctx["fallback"]}
    if not done.exists():
        recs, summary = appview.history(pds, did, now_us, lim["history_posts_per_account"],
                                        lim["history_replies_per_account"], max_pages=ctx["max_pages"])
        seen, uniq = set(), []
        for rec in recs:                                   # one copy of each record, whatever the server sent
            if rec.get("uri") not in seen:
                seen.add(rec.get("uri"))
                uniq.append(rec)
        data = done.with_name(_key(did) + ".jsonl.gz")
        line["replaced_incomplete"] = data.exists()
        if uniq:
            _write_gz(data, uniq)
        bc.atomic_json(done, {**summary, "fetched": _iso(now_us), "by": "history_daily"})
        line.update(kind="first", records=len(uniq), new=len(uniq), gone=summary.get("gone", False),
                    ended=summary.get("ended"), pages=summary.get("pages"))
        return line
    held, prev_anchor = held_uris(hist, daily, did)
    if prev_anchor is None:      # the last pull found the account gone: take a capped history like a first pull
        recs, summary = appview.history(pds, did, now_us, lim["history_posts_per_account"],
                                        lim["history_replies_per_account"], max_pages=ctx["max_pages"])
    else:
        recs, summary = history_since(pds, did, now_us, prev_anchor, ctx["max_pages"])
    new, seen = [], set(held)
    for rec in recs:
        if rec.get("uri") not in seen:
            seen.add(rec.get("uri"))
            new.append(rec)
    out_dir = daily / did[-2:] / _key(did)
    if new:
        _write_gz(out_dir / f"{stamp}.jsonl.gz", new)
    if not summary.get("gone"):
        bc.atomic_json(out_dir / f"{stamp}.done.json", {**summary, "fetched": _iso(now_us), "records": len(new)})
    line.update(kind="repull", records=len(recs), new=len(new), gone=summary.get("gone", False),
                ended=summary.get("ended"), pages=summary.get("pages"))
    return line


# ------------------------------------------------------------------------------------------------ one run
def single_instance(state_dir):
    """Hold state/history_daily.lock for the life of the process; None if another copy holds it."""
    state_dir.mkdir(parents=True, exist_ok=True)
    f = open(state_dir / "history_daily.lock", "a+")
    try:
        if os.name == "nt":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        return None
    return f


def settings(cfg):
    s = dict(DEFAULTS)
    s.update(cfg.get("history_daily") or {})
    return s


def run(cfg, data, status_dir, accounts=None, plan_only=False, opener=None, sleep=time.sleep, clock=time.time,
        log=print):
    """One run. Returns the status dict (counts only)."""
    s = settings(cfg)
    cap_accounts = s["accounts_per_run"] if accounts is None else accounts
    w = cfg["window"]
    start_us, end_us = bc.iso_to_us(str(w["start"])), bc.iso_to_us(str(w["end"]))
    sdir = data / "state" / "history_daily"
    qpath, ledger = sdir / "window_repliers.json", sdir / "pulls.jsonl"
    hist_root, daily_root = data / "raw" / "histories", data / "raw" / "histories_daily"
    t0 = clock()
    started = _iso(int(t0 * 1e6))

    qstate = bc.load_json(qpath, {})
    scanned = scan_window(data / "raw" / "jetstream", set(bc.targets(cfg)), start_us, end_us, qstate)
    if not plan_only:
        bc.atomic_json(qpath, qstate)
    repliers = qstate.get("repliers", {})
    now_us = int(clock() * 1e6)
    last = last_pulls(hist_root, ledger)
    todo, queue = plan(repliers, last, now_us, s["repull_after_days"], cap_accounts)

    status = {"run_started": started, "plan_only": plan_only, "caps": {k: s[k] for k in DEFAULTS},
              "accounts_this_run": cap_accounts, "scan": scanned, "queue_before": queue,
              "result": {"pulled_first": 0, "repulled": 0, "gone": 0, "failed": 0, "throttled": 0,
                         "records_written": 0, "fallback_pds": 0, "replaced_incomplete": 0},
              "ended": "plan only" if plan_only else None}
    if plan_only:
        status["would_pull"] = len(todo)
        return status

    budget = Budget(s["requests_per_run"], s["min_gap_s"], opener, sleep, clock)
    c = cfg["collect"]
    log_dir = data / "logs"
    clients = {}

    def client(name, host, rate):
        if host not in clients:
            clients[host] = bc.Http(name, host, rate, c["user_agent"], log_dir, opener=budget.opener, sleep=sleep,
                                    clock=clock)
        return clients[host]

    plc_http = client("plc", c["plc"], c["rate"]["plc"])
    ctx = {"hist_root": hist_root, "daily_root": daily_root, "limits": cfg["limits"], "plc": plc_http,
           "plc_root": data / "raw" / "plc", "fallback": c["pds_fallback"], "max_pages": s["max_pages"],
           "pds_client": lambda host: client("pds", host, c["rate"]["pds"])}
    res = status["result"]
    worst = s["max_pages"] + 1
    in_a_row = 0
    sdir.mkdir(parents=True, exist_ok=True)
    ended = "queue empty"
    with open(ledger, "a", encoding="utf-8", newline="\n") as led:
        for did in todo:
            if budget.left() < worst:
                ended = "request cap"
                break
            if clock() - t0 >= s["max_minutes"] * 60:
                ended = "time cap"
                break
            try:
                line = pull_one(did, ctx, int(clock() * 1e6))
                in_a_row = 0
            except BudgetExhausted:
                ended = "request cap"
                break
            except bc.Throttled:
                res["throttled"] += 1
                in_a_row += 1
                line = {"did": did, "at": _iso(int(clock() * 1e6)), "failed": "throttled"}
            except Exception as e:      # an unreachable self-hosted PDS must not stop the run; retried next run
                res["failed"] += 1
                line = {"did": did, "at": _iso(int(clock() * 1e6)), "failed": type(e).__name__}
            led.write(json.dumps(line) + "\n")
            led.flush()
            if not line.get("failed"):
                if line.get("gone"):
                    res["gone"] += 1
                else:
                    res["pulled_first" if line["kind"] == "first" else "repulled"] += 1
                res["records_written"] += line.get("new", 0)
                res["fallback_pds"] += bool(line.get("fallback_pds"))
                res["replaced_incomplete"] += bool(line.get("replaced_incomplete"))
            if in_a_row >= s["stop_after_throttled"]:
                ended = f"stopped: {in_a_row} accounts in a row refused (429/5xx)"
                break
            done_n = res["pulled_first"] + res["repulled"] + res["gone"] + res["failed"] + res["throttled"]
            if done_n % 25 == 0:
                status.update(ended="running", requests_used=budget.used)
                write_status(status_dir, status)
        else:
            ended = "account cap" if queue["never_pulled"] + queue["due_for_repull"] > len(todo) else "queue empty"
    for h in clients.values():
        h.flush()
    codes = {}
    for h in clients.values():
        for k, v in h.total.items():
            codes[k] = codes.get(k, 0) + v
    last = last_pulls(hist_root, ledger)
    _, after = plan(repliers, last, int(clock() * 1e6), s["repull_after_days"], 0)
    per_run = max(1, res["pulled_first"] + res["gone"])
    status.update(ended=ended, run_finished=_iso(int(clock() * 1e6)), seconds=round(clock() - t0, 1), requests_used=budget.used,
                  requests_by_status=codes, queue_after=after,
                  days_to_first_pull_all_at_this_rate=round(after["never_pulled"] / per_run, 1)
                  if res["pulled_first"] + res["gone"] else None)
    return status


def write_status(status_dir, status):
    """bluesky_status/histories.json: this run, plus the last 30 runs' outcomes. Counts only."""
    p = Path(status_dir) / "histories.json"
    old = bc.load_json(p, {})
    runs = [r for r in old.get("runs", []) if r.get("run_started") != status.get("run_started")]
    if not status.get("plan_only") and status.get("ended") != "running":
        runs.append({k: status.get(k) for k in ("run_started", "run_finished", "ended", "requests_used", "result")})
    bc.atomic_json(p, {**status, "runs": runs[-30:]})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true", help="read the queue and print counts; no request is made")
    ap.add_argument("--accounts", type=int, help="account cap for this run (default: history_daily.accounts_per_run)")
    args = ap.parse_args()
    cfg = bc.load_config()
    data = bc.data_dir()
    lock = single_instance(data / "state")
    if lock is None:
        print(f"history_daily {bc.now_iso()}: another copy is running (state/history_daily.lock); exiting", flush=True)
        sys.exit(3)
    status = run(cfg, data, bc.status_dir(), accounts=args.accounts, plan_only=args.plan)
    if not args.plan:
        write_status(bc.status_dir(), status)
    print("history_daily", json.dumps({k: v for k, v in status.items() if k != "caps"}), flush=True)


if __name__ == "__main__":
    main()
