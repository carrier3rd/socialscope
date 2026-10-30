#!/usr/bin/env python3
"""
Bot Bouncer listing inventory (scripts/bb_inventory.py).

Parses Bot Bouncer post dumps (.zip, .jsonl, .json, .ndjson) in Arctic Shift format.
Extracts the target username from `url` (/user/<NAME> or /u/<NAME>) or `title` ("Overview for <NAME>"),
and the verdict from `link_flair_text` (normalized to lowercase).

Deduplicates accounts listed multiple times by retaining the latest verdict per account
(highest `created_utc`). Outputs:
1. A CSV of counts by month x flair (using the latest verdict per account, or all listings).
2. A private CSV of (username, flair, listed_utc) with the latest verdict per account.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime, timezone
import glob
import io
import json
from pathlib import Path
import re
import zipfile
from typing import Dict, Iterable, Iterator, List, Optional, Tuple


URL_USER_RE = re.compile(r"/(?:user|u)/([A-Za-z0-9_-]+)", re.IGNORECASE)
TITLE_USER_RE = re.compile(r"overview\s+for\s+/?(?:u/|user/)?([A-Za-z0-9_-]+)", re.IGNORECASE)


def extract_username(post: dict) -> Optional[str]:
    """Extract target username from a Bot Bouncer submission record."""
    for field in ("url", "permalink"):
        val = post.get(field) or ""
        if isinstance(val, str) and val:
            # Skip r/BotBouncer self-links unless they contain /user/ or /u/
            m = URL_USER_RE.search(val)
            if m:
                return m.group(1)

    title = post.get("title") or ""
    if isinstance(title, str) and title:
        m = TITLE_USER_RE.search(title)
        if m:
            return m.group(1)

    return None


def normalize_flair(flair: Optional[str]) -> str:
    """Normalize link_flair_text into a clean lowercase verdict token."""
    if not flair or not isinstance(flair, str):
        return "unflaired"
    cleaned = flair.strip().lower()
    if not cleaned:
        return "unflaired"
    # Handle composite flairs like "Banned | Bot" or emoji prefixes if present
    for known in ("banned", "organic", "pending", "purged", "declined", "retired", "service"):
        if known in cleaned:
            return known
    return cleaned


def iter_jsonl_stream(stream: Iterable[str]) -> Iterator[dict]:
    """Yield parsed JSON objects from a text line stream."""
    for line in stream:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                yield obj
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict):
                        yield item
        except json.JSONDecodeError:
            continue


def iter_records(paths: Iterable[str | Path]) -> Iterator[dict]:
    """Iterate over records from .zip, .jsonl, .ndjson, or .json files."""
    expanded: List[Path] = []
    for p in paths:
        p_str = str(p)
        matches = glob.glob(p_str)
        if matches:
            expanded.extend(Path(m) for m in sorted(matches))
        else:
            expanded.append(Path(p_str))

    for path in expanded:
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")
        if path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path, "r") as zf:
                for name in sorted(zf.namelist()):
                    if name.endswith("/") or not name.lower().endswith((".jsonl", ".json", ".ndjson")):
                        continue
                    with zf.open(name, "r") as raw:
                        text_stream = io.TextIOWrapper(raw, encoding="utf-8", errors="replace")
                        yield from iter_jsonl_stream(text_stream)
        else:
            with path.open("r", encoding="utf-8", errors="replace") as f:
                first_char = f.read(1)
                f.seek(0)
                if first_char == "[":
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                yield item
                else:
                    yield from iter_jsonl_stream(f)


def build_inventory(
    records: Iterable[dict],
) -> Tuple[Dict[str, Tuple[str, str, int]], Dict[str, Dict[str, int]]]:
    """
    Process Bot Bouncer post records and deduplicate by account (latest created_utc wins).

    Returns:
        latest_by_user: dict mapping lowercase_username -> (canonical_username, flair, listed_utc)
        month_flair_counts: dict mapping YYYY-MM -> {flair -> count} (computed on deduplicated accounts)
    """
    latest_by_user: Dict[str, Tuple[str, str, int]] = {}

    for post in records:
        username = extract_username(post)
        if not username:
            continue
        raw_ts = post.get("created_utc")
        if raw_ts is None:
            continue
        try:
            listed_utc = int(float(raw_ts))
        except (ValueError, TypeError):
            continue

        flair = normalize_flair(post.get("link_flair_text"))
        key = username.lower()

        prev = latest_by_user.get(key)
        if prev is None or listed_utc >= prev[2]:
            latest_by_user[key] = (username, flair, listed_utc)

    month_flair_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for _key, (_user, flair, listed_utc) in latest_by_user.items():
        month_str = datetime.fromtimestamp(listed_utc, tz=timezone.utc).strftime("%Y-%m")
        month_flair_counts[month_str][flair] += 1

    return latest_by_user, month_flair_counts


def write_counts_csv(
    month_flair_counts: Dict[str, Dict[str, int]],
    out_path: str | Path,
) -> List[str]:
    """Write month x flair pivot table to CSV. Returns ordered flair columns."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_flairs_set = {flair for flairs in month_flair_counts.values() for flair in flairs}
    preferred_order = ["banned", "organic", "pending", "purged", "declined", "retired", "service", "unflaired"]
    ordered_flairs = [f for f in preferred_order if f in all_flairs_set]
    ordered_flairs.extend(sorted(all_flairs_set - set(ordered_flairs)))

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["month", *ordered_flairs, "total"])
        for month in sorted(month_flair_counts.keys()):
            row_counts = [month_flair_counts[month].get(fl, 0) for fl in ordered_flairs]
            writer.writerow([month, *row_counts, sum(row_counts)])

    return ordered_flairs


def write_private_inventory_csv(
    latest_by_user: Dict[str, Tuple[str, str, int]],
    out_path: str | Path,
) -> None:
    """Write private (username, flair, listed_utc) file sorted by listed_utc then username."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = sorted(latest_by_user.values(), key=lambda x: (x[2], x[0].lower()))
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "flair", "listed_utc"])
        for username, flair, listed_utc in rows:
            writer.writerow([username, flair, listed_utc])


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build Bot Bouncer month x flair inventory and deduplicated account verdict list."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Bot Bouncer post dump files (.zip, .jsonl, .json)",
    )
    parser.add_argument(
        "-o",
        "--out-counts",
        default="out/bb_counts_by_month.csv",
        help="Output CSV path for counts by month x flair (default: out/bb_counts_by_month.csv)",
    )
    parser.add_argument(
        "-p",
        "--out-private",
        default="out/bb_inventory_private.csv",
        help="Private output CSV path for (username, flair, listed_utc) (default: out/bb_inventory_private.csv)",
    )
    args = parser.parse_args(argv)

    records = iter_records(args.inputs)
    latest_by_user, month_flair_counts = build_inventory(records)
    write_counts_csv(month_flair_counts, args.out_counts)
    write_private_inventory_csv(latest_by_user, args.out_private)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
