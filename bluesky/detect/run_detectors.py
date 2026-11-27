#!/usr/bin/env python3
"""Run the five Phase 4 detectors over a time range and write counts-only summaries.

    python bluesky/detect/run_detectors.py --dev       development days only: everything before the window start
    python bluesky/detect/run_detectors.py --window    the test window (refuses to run before the window has ended)

Outputs: <data>/processed/detect/<name>.json (counts only) and processed/detect/private/<name>.json (details, never
published). In --dev mode block_surge uses the first half of the development days as its baseline and alarms in the
second half: a plumbing check only; the scored run uses week 1 of the window as the baseline and weeks 2-3 for alarms.
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import block_surge  # noqa: E402
import common as cm  # noqa: E402
import dormant_hijack  # noqa: E402
import follow_burst  # noqa: E402
import like_farm  # noqa: E402
import reply_bot  # noqa: E402

DEV_START = "2026-11-19"   # the first day the recorder ran (pilot)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dev", action="store_true")
    g.add_argument("--window", action="store_true")
    ap.add_argument("--config", default=str(cm.bc.CONFIG))
    a = ap.parse_args()
    cfg = cm.bc.load_config(a.config)
    data = cm.bc.data_dir()
    w = cfg["window"]
    ws, we = cm.day_us(w["start"]), cm.day_us(w["end"])
    if a.window:
        if time.time() * 1e6 < we:
            sys.exit("the test window has not ended yet; scoring it now would read part of it early")
        start, end = ws, we
        base = (ws, ws + 7 * cm.DAY_US)
        alarm = (ws + 7 * cm.DAY_US, we)
        tag = "window"
    else:
        start, end = cm.day_us(DEV_START), ws
        mid = start + (end - start) // 2 // cm.HOUR_US * cm.HOUR_US
        base, alarm = (start, mid), (mid, end)
        tag = "dev"
    out = {}
    for name, fn in (("like_farm", lambda: like_farm.run(data, cfg, start, end)),
                     ("follow_burst", lambda: follow_burst.run(data, cfg, start, end)),
                     ("dormant_hijack", lambda: dormant_hijack.run(data, cfg, start, end)),
                     ("reply_bot", lambda: reply_bot.run(data, cfg, start, end)),
                     ("block_surge", lambda: block_surge.run(data, cfg, alarm[0], alarm[1], base[0], base[1]))):
        t0 = time.time()
        summary, private = fn()
        summary["seconds"] = round(time.time() - t0, 1)
        cm.write_summary(data, f"{name}_{tag}", summary)
        cm.write_private(data, f"{name}_{tag}", private)
        out[name] = summary
        print(name, json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
