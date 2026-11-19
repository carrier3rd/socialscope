#!/usr/bin/env python3
"""Did the 24-hour pilot pass? Reads the recorder's session log, hour files and the request logs.

Phase 1 is done when (spec section 10): the 24-hour run completed, it resumed after a killed process, and the
request log shows no sustained 429s. This prints each check with its numbers and PASS or FAIL. Counts only.

It refuses to run until docs/bluesky-politics-predictions.md is committed, because it reads pilot data
(CLAUDE.md rule 3). Pilot days are development data either way.
"""
import collections
import gzip
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bsky_common as bc  # noqa: E402

PREDICTIONS = "docs/bluesky-politics-predictions.md"
SUSTAINED_MIN = 5      # this many minutes in a row with a 429 counts as sustained
MAX_RESUME_GAP_S = 60


def predictions_committed(repo=bc.REPO):
    r = subprocess.run(["git", "-C", str(repo), "log", "--oneline", "-1", "--", PREDICTIONS],
                       capture_output=True, text=True)
    return r.returncode == 0 and bool(r.stdout.strip())


def read_jsonl(path):
    try:
        with open(path, encoding="utf-8") as f:
            out = []
            for line in f:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass      # a killed process can leave one cut-off last line
            return out
    except FileNotFoundError:
        return []


def session_checks(sessions):
    resumed = [s for s in sessions if s.get("cursor")]
    gaps = [s["resume_gap_s"] for s in resumed if "resume_gap_s" in s]
    return {
        "sessions": len(sessions),
        "reasons": dict(collections.Counter(s.get("reason") for s in sessions)),
        "resumed_sessions": len(resumed),
        "largest_resume_gap_s": max(gaps) if gaps else None,
        "gap_possible": sum(1 for s in sessions if s.get("gap_possible")),
        "events": sum(s.get("events", 0) for s in sessions),
        "kept": sum(s.get("kept", 0) for s in sessions),
    }


def longest_429_run(rows):
    """Longest run of consecutive minutes with at least one 429, and the totals per status code."""
    total = collections.Counter()
    minutes = set()
    for r in rows:
        for code, k in r["codes"].items():
            total[code] += k
        if r["codes"].get("429"):
            minutes.add(r["minute"] // 60)
    best = run = 0
    prev = None
    for m in sorted(minutes):
        run = run + 1 if prev is not None and m == prev + 1 else 1
        best, prev = max(best, run), m
    return best, dict(total)


def hours_covered(folder):
    return sorted({p.name[:13] for p in Path(folder).glob("20*.jsonl*")})


def kept_by_kind(folder):
    n = collections.Counter()
    for p in sorted(Path(folder).glob("20*.jsonl*")):
        op = gzip.open if p.suffix == ".gz" else open
        with op(p, "rt", encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    j = json.loads(line)
                except json.JSONDecodeError:
                    n["cut_off_lines"] += 1
                    continue
                c = j.get("commit") or {}
                n[(c.get("collection", "") + ":" + c.get("operation", "")) if c else j.get("kind", "?")] += 1
    return dict(sorted(n.items()))


def main():
    if not predictions_committed():
        sys.exit(f"{PREDICTIONS} is not committed yet. Commit it before reading pilot data (CLAUDE.md rule 3).")
    d = bc.data_dir()
    js = d / "raw" / "jetstream"
    ok = True

    def check(name, passed, detail):
        nonlocal ok
        ok = ok and passed
        print(f"{'PASS' if passed else 'FAIL'}  {name}: {detail}")

    hours = hours_covered(js)
    check("24 hours recorded", len(hours) >= 24, f"{len(hours)} hour files, {hours[0] if hours else '-'} to "
                                                 f"{hours[-1] if hours else '-'}")
    s = session_checks(read_jsonl(js / "sessions.jsonl"))
    print("      sessions:", json.dumps(s))
    check("resumed after a kill", s["resumed_sessions"] >= 1, f"{s['resumed_sessions']} sessions started from a "
          "saved cursor (a session killed with -9 leaves no line of its own)")
    gap = s["largest_resume_gap_s"]
    check("no gap on resume", gap is not None and gap <= MAX_RESUME_GAP_S and not s["gap_possible"],
          f"largest distance from cursor to first event: {gap} s (limit {MAX_RESUME_GAP_S})")
    for log in sorted((d / "logs").glob("requests_*.jsonl")):
        run, total = longest_429_run(read_jsonl(log))
        check(f"no sustained 429s ({log.stem[9:]})", run < SUSTAINED_MIN,
              f"longest run {run} min; requests by status {json.dumps(total)}")
    print("      kept events by kind:", json.dumps(kept_by_kind(js)))
    print("PILOT PASSED" if ok else "PILOT NOT PASSED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
