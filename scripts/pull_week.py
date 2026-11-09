#!/usr/bin/env python3
"""Pull (or top up) one panel week for all 18 subs. Cloud session, Nov 9 2026.
Usage, from ~/socialscope:  python3 -I scripts/pull_week.py 2026-11-03 [2026-10-27 ...]
Each start date pulls start .. start+7 days (end exclusive) into ~/socialscope_data/reddit_pulls/<monDD>/.
Rerunning a week resumes every unfinished .jsonl from its last timestamp and rezips it, so the same command
also finishes a pull that stopped on "server too busy". Run it again until the log shows no "stopped:" lines.
"""
import os, sys
from datetime import date, timedelta
sys.path.insert(0, os.path.expanduser("~/socialscope"))
from socialscope import arctic

SUBS = ["Asmongold", "Conservative", "Destiny", "Hasan_Piker", "IsraelPalestine", "LeftoversH3", "LivestreamFail",
        "Palestine", "PoliticalCompassMemes", "TankieTheDeprogram", "atrioc", "dsa", "h3h3productions", "neoliberal",
        "samharris", "thebulwark", "thedavidpakmanshow", "ukraine"]
for start in sys.argv[1:]:
    d = date.fromisoformat(start)
    folder = d.strftime("%b%d").lower()
    arctic.pull_subreddits(SUBS, start, (d + timedelta(days=7)).isoformat(),
                           out_dir=os.path.expanduser(f"~/socialscope_data/reddit_pulls/{folder}"))
    print(f"week {start} pass done")
