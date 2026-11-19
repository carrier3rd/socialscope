#!/usr/bin/env python3
"""Constellation client (constellation.microcosm.blue): who liked, reposted, followed or blocked a subject.

The public instance is best-effort, so every response is cached on disk and never asked for twice, requests
are spaced out (collect.rate.constellation in targets.yaml), and a failure returns None so callers can fall
back to counts from the Jetstream recording.

Endpoints, checked Nov 19 2026 with a made-up subject:
  /xrpc/blue.microcosm.links.getBacklinks?subject=&source=&limit=(max 100)&cursor=
        -> {"total": n, "records": [...], "cursor": null or a string}
  /xrpc/blue.microcosm.links.getBacklinksCount?subject=&source=   -> {"total": n}
The shape of one entry in "records" has not been seen yet (no real subject was queried before the pilot);
responses are stored whole, so nothing here depends on it.

Cache: <data>/raw/constellation/<aa>/<sha256 of the request>.json   (private)
Blocks and list memberships read through here are reported in aggregate only (spec section 3).
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bsky_common as bc  # noqa: E402

SOURCES = {
    "likes": "app.bsky.feed.like:subject.uri",
    "reposts": "app.bsky.feed.repost:subject.uri",
    "replies": "app.bsky.feed.post:reply.parent.uri",
    "followers": "app.bsky.graph.follow:subject",
    "blockers": "app.bsky.graph.block:subject",
}
NS = "xrpc/blue.microcosm.links."


class Constellation:
    def __init__(self, http, root):
        self.http, self.root = http, Path(root)
        self.hits = self.misses = self.failures = 0

    def _get(self, method, params, cache=True):
        key = hashlib.sha256(json.dumps([method, sorted(params.items())]).encode()).hexdigest()
        p = self.root / key[:2] / (key + ".json")
        if cache and p.exists():
            self.hits += 1
            return bc.load_json(p, {}).get("body")
        try:
            body = self.http.get(NS + method, params)
        except Exception:
            self.failures += 1
            return None
        self.misses += 1
        bc.atomic_json(p, {"method": method, "params": params, "fetched": bc.now_iso(), "body": body})
        return body

    def count(self, subject, kind):
        """Total links of one kind to a subject, or None if Constellation is down. Not cached: counts move."""
        body = self._get("getBacklinksCount", {"subject": subject, "source": SOURCES[kind]}, cache=False)
        return None if body is None else body.get("total")

    def records(self, subject, kind, max_pages=20):
        """Every record linking to the subject, up to max_pages of 100. None if the first page fails."""
        out, cursor = [], None
        for _ in range(max_pages):
            params = {"subject": subject, "source": SOURCES[kind], "limit": 100}
            if cursor:
                params["cursor"] = cursor
            body = self._get("getBacklinks", params)
            if body is None:
                return out or None
            out += body.get("records") or []
            cursor = body.get("cursor")
            if not cursor:
                break
        return out


def main():
    """Pilot use: likers and reposters of the target posts found by `appview.py threads`."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50, help="most posts to query in this pass")
    ap.add_argument("--max-pages", type=int, default=20)
    args = ap.parse_args()
    cfg = bc.load_config()
    d = bc.data_dir()
    con = Constellation(bc.clients(cfg)["constellation"], d / "raw" / "constellation")
    index = d / "raw" / "threads" / "index.jsonl"
    uris = []
    if index.exists():
        uris = list(dict.fromkeys(json.loads(line)["uri"] for line in open(index, encoding="utf-8")))
    done = 0
    for uri in uris[-args.limit:]:
        for kind in ("likes", "reposts"):
            con.records(uri, kind, args.max_pages)
        done += 1
    con.http.flush()
    print("constellation", json.dumps({"posts": done, "cache_hits": con.hits, "fetched": con.misses,
                                       "failures": con.failures}), "requests", json.dumps(con.http.total))


if __name__ == "__main__":
    main()
