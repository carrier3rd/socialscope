"""Shared helpers for the Phase 4 detectors (bluesky/detect/*.py). Written Nov 27 2026.

Every detector reads the Phase 2 tables through DuckDB, takes a time range [start_us, end_us) so the same code runs
on development days now and on the test window later, and returns two things:
  summary   counts only, safe to print and to quote in a results file (no DID, handle or text)
  private   per-account or per-group details, written under processed/detect/private/ and never published
Side is a property of the target's thread, never of an account (predictions file, "Sides").
"""
import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "collect"))
import bsky_common as bc  # noqa: E402

DAY_US = 86_400_000_000
HOUR_US = 3_600_000_000


def connect(data):
    import duckdb
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
    con.execute(f"SET memory_limit = '{os.environ.get('BSKY_DETECT_MEMORY', '2GB')}'")
    tmp = data / "processed" / "duckdb_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    con.execute(f"SET temp_directory = '{tmp.as_posix()}'")
    return con


def table(data, name):
    """The path of a Phase 2 table, for read_parquet('...')."""
    return (data / "processed" / "tables" / f"{name}.parquet").as_posix()


def register_targets(con, cfg):
    import pyarrow as pa
    t = bc.targets(cfg)
    con.register("targets_arrow", pa.Table.from_pylist([{"did": d, "side": s} for d, s in t.items()],
                                                       schema=pa.schema([("did", pa.string()), ("side", pa.string())])))
    con.execute("CREATE OR REPLACE TEMP TABLE targets AS SELECT * FROM targets_arrow")
    return t


def day_us(d):
    d = d if isinstance(d, dt.date) else dt.date.fromisoformat(str(d))
    return int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp() * 1_000_000)


def write_private(data, name, obj):
    bc.atomic_json(data / "processed" / "detect" / "private" / f"{name}.json", obj)


def write_summary(data, name, obj):
    bc.atomic_json(data / "processed" / "detect" / f"{name}.json", {"run": bc.now_iso(), **obj})
