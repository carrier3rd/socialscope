#!/usr/bin/env python3
"""
Training-sample builder (scripts/build_training_sample.py).

From the Bot Bouncer inventory CSV (username, flair, listed_utc) plus a set of weekly
subreddit zips/jsonl dumps:
- Draws up to N banned accounts, N organic-flair accounts, and N random active accounts
  from the weekly subreddit dumps (excluding any account in the inventory or --exclude list).
- Splits strictly by listing date (train = listed_utc < cutoff_utc, test = listed_utc >= cutoff_utc),
  never randomly. For random active accounts (which have no Bot Bouncer listing date), uses
  their earliest activity timestamp in the weekly dumps (`first_seen_utc`) or assigns them
  relative to the temporal cutoff based on activity timestamp.
- Takes an `--exclude` file of usernames to drop (e.g., an earlier test set).
- Uses a fixed random seed (`--seed`, default 42) after deterministic sorting.
- Writes `users_to_pull.txt` and `groups.csv` with columns:
  `username,group,split,listed_utc`
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import glob
import io
import json
from pathlib import Path
import random
import zipfile
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple


IGNORED_AUTHORS = {"[deleted]", "[removed]", "automoderator", ""}


def parse_cutoff(cutoff_str: str) -> int:
    """Parse a cutoff date (YYYY-MM-DD or ISO-8601) or integer epoch timestamp into UTC seconds."""
    s = cutoff_str.strip()
    if s.isdigit():
        return int(s)
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        dt = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def load_exclude_usernames(path: Optional[str | Path]) -> Set[str]:
    """Load lowercase usernames to exclude from a text or CSV file."""
    if not path:
        return set()
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Exclude file not found: {p}")

    excluded: Set[str] = set()
    with p.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue
            first_col = raw.split(",")[0].strip().strip('"').strip("'")
            if first_col.lower() in {"username", "author", "user"}:
                continue
            if first_col.startswith("u/"):
                first_col = first_col[2:]
            elif first_col.startswith("/u/"):
                first_col = first_col[3:]
            if first_col:
                excluded.add(first_col.lower())
    return excluded


def load_inventory(
    inventory_path: str | Path,
    excluded_lower: Set[str],
) -> List[Tuple[str, str, int]]:
    """
    Load private inventory CSV (username, flair, listed_utc).
    Deduplicates by keeping latest listed_utc if needed, and filters out excluded usernames.
    """
    p = Path(inventory_path)
    if not p.exists():
        raise FileNotFoundError(f"Inventory file not found: {p}")

    latest: Dict[str, Tuple[str, str, int]] = {}
    with p.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            username = (row.get("username") or "").strip()
            flair = (row.get("flair") or "").strip().lower()
            raw_utc = (row.get("listed_utc") or "").strip()
            if not username or not raw_utc:
                continue
            key = username.lower()
            if key in excluded_lower or key in IGNORED_AUTHORS:
                continue
            try:
                listed_utc = int(float(raw_utc))
            except ValueError:
                continue
            prev = latest.get(key)
            if prev is None or listed_utc >= prev[2]:
                latest[key] = (username, flair, listed_utc)

    return sorted(latest.values(), key=lambda x: (x[2], x[0].lower()))


def iter_weekly_records(paths: Iterable[str | Path]) -> Iterator[dict]:
    """Iterate over Reddit post/comment records in weekly subreddit zips or jsonl files."""
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
            raise FileNotFoundError(f"Weekly input file not found: {path}")
        if path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path, "r") as zf:
                for name in sorted(zf.namelist()):
                    if name.endswith("/") or not name.lower().endswith((".jsonl", ".json", ".ndjson")):
                        continue
                    with zf.open(name, "r") as raw:
                        text_stream = io.TextIOWrapper(raw, encoding="utf-8", errors="replace")
                        for line in text_stream:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                obj = json.loads(line)
                                if isinstance(obj, dict):
                                    yield obj
                            except json.JSONDecodeError:
                                continue
        else:
            with path.open("r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if isinstance(obj, dict):
                            yield obj
                    except json.JSONDecodeError:
                        continue


def collect_active_accounts(
    weekly_paths: Iterable[str | Path],
    excluded_lower: Set[str],
) -> List[Tuple[str, int]]:
    """
    Scan weekly subreddit dumps for active accounts not in `excluded_lower`.
    Returns a deterministically sorted list of (canonical_username, latest_activity_utc).
    """
    active: Dict[str, Tuple[str, int]] = {}
    for rec in iter_weekly_records(weekly_paths):
        author = (rec.get("author") or "").strip()
        if not author:
            continue
        key = author.lower()
        if key in IGNORED_AUTHORS or key in excluded_lower:
            continue
        raw_ts = rec.get("created_utc")
        try:
            ts = int(float(raw_ts)) if raw_ts is not None else 0
        except (ValueError, TypeError):
            ts = 0

        prev = active.get(key)
        if prev is None or ts > prev[1]:
            active[key] = (author, ts)

    return sorted(active.values(), key=lambda x: (x[0].lower(), x[1]))


def sample_pool(
    candidates: List[Tuple[str, int]],
    n: int,
    rng: random.Random,
) -> List[Tuple[str, int]]:
    """Draw up to n items from candidates using rng without replacement, preserving deterministic order."""
    if n <= 0 or not candidates:
        return []
    if len(candidates) <= n:
        return list(candidates)
    chosen = rng.sample(candidates, n)
    return sorted(chosen, key=lambda x: (x[1], x[0].lower()))


def build_training_sample(
    inventory_path: str | Path,
    weekly_paths: Iterable[str | Path],
    n_per_group: int,
    cutoff_utc: int,
    exclude_path: Optional[str | Path] = None,
    seed: int = 42,
) -> List[Dict[str, str | int]]:
    """
    Build training and test sample across three groups: `banned`, `organic`, and `random` (active control).
    Splits strictly by timestamp vs `cutoff_utc` (`train` if listed_utc < cutoff_utc else `test`).
    """
    rng = random.Random(seed)
    excluded_lower = load_exclude_usernames(exclude_path)

    inv_rows = load_inventory(inventory_path, excluded_lower)
    inv_usernames_lower = {u.lower() for u, _fl, _ts in inv_rows}

    banned_pool = [(u, ts) for u, fl, ts in inv_rows if fl == "banned"]
    organic_pool = [(u, ts) for u, fl, ts in inv_rows if fl == "organic"]

    active_exclusions = excluded_lower | inv_usernames_lower
    active_pool = collect_active_accounts(weekly_paths, active_exclusions)

    sampled_banned = sample_pool(banned_pool, n_per_group, rng)
    sampled_organic = sample_pool(organic_pool, n_per_group, rng)
    sampled_active = sample_pool(active_pool, n_per_group, rng)

    records: List[Dict[str, str | int]] = []
    for group_name, pool in (
        ("banned", sampled_banned),
        ("organic", sampled_organic),
        ("random", sampled_active),
    ):
        for username, listed_utc in pool:
            split = "train" if listed_utc < cutoff_utc else "test"
            records.append(
                {
                    "username": username,
                    "group": group_name,
                    "split": split,
                    "listed_utc": listed_utc,
                }
            )

    return records


def write_sample_outputs(
    records: List[Dict[str, str | int]],
    out_dir: str | Path,
) -> Tuple[Path, Path]:
    """Write `users_to_pull.txt` and `groups.csv` to `out_dir`."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    users_file = out_path / "users_to_pull.txt"
    groups_file = out_path / "groups.csv"

    with users_file.open("w", encoding="utf-8") as uf:
        for r in records:
            uf.write(f"{r['username']}\n")

    with groups_file.open("w", newline="", encoding="utf-8") as gf:
        writer = csv.DictWriter(gf, fieldnames=["username", "group", "split", "listed_utc"])
        writer.writeheader()
        for r in records:
            writer.writerow(r)

    return users_file, groups_file


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Draw N banned, N organic-flair, and N random active accounts with date-based train/test split."
    )
    parser.add_argument(
        "--inventory",
        required=True,
        help="Path to private Bot Bouncer inventory CSV (username, flair, listed_utc).",
    )
    parser.add_argument(
        "--weekly",
        nargs="+",
        required=True,
        help="Weekly subreddit dump files (.zip or .jsonl) to sample random active accounts from.",
    )
    parser.add_argument(
        "-n",
        "--n-per-group",
        type=int,
        default=300,
        help="Number of accounts to draw per group (banned, organic, random). Default: 300.",
    )
    parser.add_argument(
        "--cutoff",
        required=True,
        help="Temporal split cutoff date (YYYY-MM-DD, ISO-8601, or UTC epoch seconds). Train < cutoff, Test >= cutoff.",
    )
    parser.add_argument(
        "--exclude",
        default=None,
        help="Optional file of usernames to drop (e.g. an earlier test set).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Fixed random seed for reproducible sampling (default: 42).",
    )
    parser.add_argument(
        "-o",
        "--out-dir",
        default="out/training_sample",
        help="Directory to write users_to_pull.txt and groups.csv (default: out/training_sample).",
    )
    args = parser.parse_args(argv)

    cutoff_utc = parse_cutoff(args.cutoff)
    records = build_training_sample(
        inventory_path=args.inventory,
        weekly_paths=args.weekly,
        n_per_group=args.n_per_group,
        cutoff_utc=cutoff_utc,
        exclude_path=args.exclude,
        seed=args.seed,
    )
    write_sample_outputs(records, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
