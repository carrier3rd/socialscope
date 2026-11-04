#!/usr/bin/env python3
"""Context-sub pulls chosen Nov 3, 2026 (docs/context-subs-results.md).
Full posts+comments for small/medium subs; posts only for the huge news subs.
Changed Nov 3, 9:15 PM (Joseph): one continuous window Aug 1 - Nov 2, 2026, pulled month by month so each zip stays
a manageable size; ShitLiberalsSay dropped.
Resumable: finished zips are skipped. Run from ~/socialscope:
  nohup systemd-inhibit --what=sleep:idle --who=socialscope --why="context pulls" \
    python3 -I scripts/pull_context_subs.py > ~/socialscope_data/context_pull.log 2>&1 &
"""
import os, sys
sys.path.insert(0, os.path.expanduser("~/socialscope"))
from socialscope import arctic

WEEKS = [("2026-08-01", "2026-09-01"), ("2026-09-01", "2026-10-01"), ("2026-10-01", "2026-11-01"),
         ("2026-11-01", "2026-11-03")]
FULL = ["youtubedrama", "DecodingTheGurus", "Fauxmoi"]
POSTS_ONLY = ["politics", "worldnews", "news"]
OUT = os.path.expanduser("~/socialscope_data/reddit_pulls/context")

for start, end in WEEKS:
    arctic.pull_subreddits(FULL, start, end, kinds=("posts", "comments"), out_dir=OUT)
    arctic.pull_subreddits(POSTS_ONLY, start, end, kinds=("posts",), out_dir=OUT)
print("context pulls done")
