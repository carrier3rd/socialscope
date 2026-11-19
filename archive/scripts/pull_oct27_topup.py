#!/usr/bin/env python3
"""Top up the Oct 27 - Nov 2, 2026 panel week (cloud session, Nov 5).
The week was first pulled on Nov 1 around midday, so it is missing the rest of Nov 1, all of Nov 2, and
r/thebulwark comments. Rerunning pull_subreddits with the same dates resumes each .jsonl from its last
timestamp (arctic._resume) and rewrites the zip, so this only fetches the missing tail. Run from ~/socialscope:
  nohup systemd-inhibit --what=sleep:idle --who=socialscope --why="oct27 topup" \
    python3 -I scripts/pull_oct27_topup.py > ~/socialscope_data/reddit_pulls/oct27/topup_log.txt 2>&1 &
"""
import os, sys
sys.path.insert(0, os.path.expanduser("~/socialscope"))
from socialscope import arctic

SUBS = ["Asmongold", "Conservative", "Destiny", "Hasan_Piker", "IsraelPalestine", "LeftoversH3", "LivestreamFail",
        "Palestine", "PoliticalCompassMemes", "TankieTheDeprogram", "atrioc", "dsa", "h3h3productions", "neoliberal",
        "samharris", "thebulwark", "thedavidpakmanshow", "ukraine"]
arctic.pull_subreddits(SUBS, "2026-10-27", "2026-11-03",
                       out_dir=os.path.expanduser("~/socialscope_data/reddit_pulls/oct27"))
print("oct27 topup done")
