"""Shared pieces for the Bluesky collectors: paths, config, an HTTP client with backoff and a request log.

Standard library plus PyYAML only. The collectors are run as scripts (`python -I bluesky/collect/x.py`), so each
one puts this folder on sys.path itself; -I leaves the script's folder out.

Privacy: everything these collectors write under the data folder is raw and private (it holds DIDs, which the
API calls and joins need). Status files, the request log and anything printed carry counts only: no DID, no
handle, no post text.
"""
import datetime as dt
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "bluesky" / "config" / "targets.yaml"

B32 = "234567abcdefghijklmnopqrstuvwxyz"


def data_dir():
    """~/socialscope_data/bluesky, or $SOCIALSCOPE_DATA/bluesky (same override as scripts/repull_run/common.py)."""
    base = os.environ.get("SOCIALSCOPE_DATA") or str(Path.home() / "socialscope_data")
    return Path(base) / "bluesky"


def status_dir():
    """Its own folder, next to the data folder and never inside it (CLAUDE.md rule 7)."""
    return data_dir().parent / "bluesky_status"


def load_config(path=None):
    import yaml
    with open(path or CONFIG, encoding="utf-8") as f:
        return yaml.safe_load(f)


def targets(cfg):
    """{did: side} for every target account."""
    return {t["did"]: side for side, rows in cfg["sides"].items() for t in rows}


def now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def atomic_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def did_of(at_uri):
    """at://did:plc:abc/app.bsky.feed.post/3k... -> did:plc:abc. A bare DID is returned as is."""
    if not at_uri:
        return None
    if at_uri.startswith("at://"):
        return at_uri[5:].split("/", 1)[0]
    return at_uri if at_uri.startswith("did:") else None


def tid_from_us(ts_us, clock=0):
    """Record key (TID) for a time in microseconds. Used as a listRecords cursor to start a pull at a date."""
    n = (int(ts_us) << 10) | clock
    return "".join(B32[(n >> (5 * i)) & 31] for i in range(12, -1, -1))


def tid_to_us(tid):
    """Microseconds encoded in a TID record key, or None if the key isn't a TID (keys are chosen by the client)."""
    if len(tid) != 13 or any(c not in B32 for c in tid):
        return None
    n = 0
    for c in tid:
        n = n * 32 + B32.index(c)
    return n >> 10


def iso_to_us(s):
    """'2026-11-19', or a full ISO time, to microseconds since the epoch (UTC)."""
    t = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return int(t.timestamp() * 1_000_000)


class Throttled(Exception):
    """The host kept answering 429 or 5xx after every retry."""


class Http:
    """GET JSON from one host: a fixed gap between requests, backoff on 429 and 5xx, a per-minute request log.

    The log (requests_<name>.jsonl, one line per minute with a count per status code) is what the pilot check
    reads to answer "no sustained 429s". It holds no URLs, because URLs carry DIDs.
    """

    def __init__(self, name, base, rate, user_agent, log_dir=None, retries=6, opener=None, sleep=time.sleep,
                 clock=time.time):
        self.name, self.base = name, base.rstrip("/")
        self.gap = 1.0 / rate if rate else 0.0
        self.ua = user_agent
        self.retries = retries
        self.opener = opener or urllib.request.urlopen
        self.sleep, self.clock = sleep, clock
        self.last = 0.0
        self.log_path = Path(log_dir) / f"requests_{name}.jsonl" if log_dir else None
        self.minute, self.codes = None, {}
        self.total = {}

    def _note(self, code):
        code = str(code)
        self.total[code] = self.total.get(code, 0) + 1
        m = int(self.clock() // 60)
        if self.minute is not None and m != self.minute:
            self.flush()
        self.minute = m
        self.codes[code] = self.codes.get(code, 0) + 1

    def flush(self):
        if self.log_path and self.codes:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"minute": self.minute * 60, "host": self.name, "codes": self.codes}) + "\n")
        self.codes = {}

    def get(self, path, params=None, ok_missing=False):
        """Parsed JSON. With ok_missing, a 400 or 404 returns None (deleted, deactivated or taken-down subject)."""
        url = f"{self.base}/{path.lstrip('/')}"
        if params:
            url += "?" + urllib.parse.urlencode(params, doseq=True)
        delay = 2.0
        for attempt in range(self.retries + 1):
            wait = self.last + self.gap - self.clock()
            if wait > 0:
                self.sleep(wait)
            self.last = self.clock()
            req = urllib.request.Request(url, headers={"User-Agent": self.ua, "Accept": "application/json"})
            try:
                with self.opener(req, timeout=30) as r:
                    body = r.read()
                self._note(200)
                return json.loads(body)
            except urllib.error.HTTPError as e:
                self._note(e.code)
                if e.code in (400, 404) and ok_missing:
                    return None
                if e.code == 429 or e.code >= 500:
                    after = e.headers.get("Retry-After") if e.headers else None
                    pause = float(after) if after and after.isdigit() else delay
                    self.sleep(min(pause, 300))
                    delay = min(delay * 2, 300)
                    continue
                raise
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                self._note("neterr")
                self.sleep(delay)
                delay = min(delay * 2, 300)
        self.flush()
        raise Throttled(f"{self.name}: gave up after {self.retries + 1} tries")


def clients(cfg, log_dir=None):
    """One Http per service, at the rates in targets.yaml."""
    c, r = cfg["collect"], cfg["collect"]["rate"]
    ua = c["user_agent"]
    log_dir = log_dir or data_dir() / "logs"
    return {
        "appview": Http("appview", c["appview"], r["appview"], ua, log_dir),
        "plc": Http("plc", c["plc"], r["plc"], ua, log_dir),
        "constellation": Http("constellation", c["constellation"], r["constellation"], ua, log_dir),
    }
