#!/usr/bin/env python3
"""PLC audit logs: one file per DID from https://plc.directory/<did>/log/audit, cached forever.

The log is append-only, so a cached copy is only ever out of date by newer operations; pass --refresh to
fetch again. did:web accounts have no PLC log and are counted and skipped.

Cache: <data>/raw/plc/<last two characters of the DID>/<did>.json   (private: file names are DIDs)
Prints counts only.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bsky_common as bc  # noqa: E402


def cache_path(root, did):
    return Path(root) / did[-2:] / (did.replace(":", "_") + ".json")


def audit(http, root, did, refresh=False):
    """The audit log (a list of operations), from the cache or the directory. None for non-PLC or unknown DIDs."""
    if not did.startswith("did:plc:"):
        return None
    p = cache_path(root, did)
    if p.exists() and not refresh:
        return bc.load_json(p, None)
    log = http.get(f"{did}/log/audit", ok_missing=True)
    if log is not None:
        bc.atomic_json(p, log)
    return log


def pds_of(log):
    """Current PDS endpoint from the newest operation that still stands, or None."""
    for op in reversed(log or []):
        if op.get("nullified"):
            continue
        o = op.get("operation") or {}
        ep = ((o.get("services") or {}).get("atproto_pds") or {}).get("endpoint") or o.get("service")
        if ep:
            return ep.rstrip("/")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dids", help="file with one DID per line (default: <data>/state/repliers.txt)")
    ap.add_argument("--limit", type=int, default=0, help="stop after this many new fetches")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    cfg = bc.load_config()
    d = bc.data_dir()
    http = bc.clients(cfg)["plc"]
    root = d / "raw" / "plc"
    src = Path(args.dids) if args.dids else d / "state" / "repliers.txt"
    dids = list(bc.targets(cfg))
    if src.exists():
        dids += [x.strip() for x in open(src, encoding="utf-8") if x.startswith("did:")]
    n = {"cached": 0, "fetched": 0, "missing": 0, "not_plc": 0}
    for did in dict.fromkeys(dids):
        if not did.startswith("did:plc:"):
            n["not_plc"] += 1
        elif cache_path(root, did).exists() and not args.refresh:
            n["cached"] += 1
        else:
            n["fetched" if audit(http, root, did, args.refresh) is not None else "missing"] += 1
            if args.limit and n["fetched"] + n["missing"] >= args.limit:
                break
    http.flush()
    print("plc", json.dumps(n), "requests", json.dumps(http.total))


if __name__ == "__main__":
    main()
