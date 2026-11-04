#!/usr/bin/env python3
"""Language features for Reddit comments and the live 2026 DGG log, comparable with orl_deep.py's ling_year.tsv.

Same feature code (scripts/ling.py) and the same effort cutoff (25+ words, emotes and links not counted).
Reddit: every r_<sub>_comments_*.jsonl under --reddit (each comment counted once, removed and deleted ones and
AutoModerator skipped). Live DGG: every YYYY-MM-DD.jsonl[.gz] under --live (bots skipped).

Output: <out>/ling_compare.tsv  source, community, scope (all | effort | directed), then ling.Acc summary columns.
'directed' only exists for chat (messages that name the streamer or say "you" without addressing a chatter).
"""
import argparse
import glob
import gzip
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ling  # noqa: E402

try:
    from vader.vaderSentiment import SentimentIntensityAnalyzer
    VADER = SentimentIntensityAnalyzer()
except Exception:
    VADER = None

EFFORT_WORDS = 25
DAYFILE = re.compile(r"^\d{4}-\d{2}-\d{2}\.jsonl(\.gz)?$")
SKIP_AUTHORS = {"AutoModerator", "[deleted]", ""}


def add(accs, key, text, emotes, directed=None):
    f = ling.features(text, emotes)
    if not f["words"] and not f["emotes"]:
        return
    accs.setdefault(key + ("all",), ling.Acc()).add(f)
    if f["words"] >= EFFORT_WORDS:
        v = VADER.polarity_scores(text)["compound"] if VADER else None
        accs.setdefault(key + ("effort",), ling.Acc()).add(f, v)
    if directed:
        accs.setdefault(key + ("directed",), ling.Acc()).add(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reddit", default=os.path.expanduser("~/socialscope_data/reddit_pulls"))
    ap.add_argument("--live", default=os.path.expanduser("~/socialscope_data/dgg_live"))
    ap.add_argument("--emotes", default=os.path.expanduser("~/socialscope_data/dgg_chat/emotes.json"))
    ap.add_argument("--out", default=os.path.expanduser("~/socialscope_data/orl_deep/_cross"))
    a = ap.parse_args()
    emotes = {e["prefix"] for e in json.load(open(a.emotes))}
    accs = {}

    seen = set()
    for path in sorted(glob.glob(os.path.join(a.reddit, "**", "r_*_comments_*.jsonl"), recursive=True)):
        sub = os.path.basename(path)[2:].split("_comments_")[0]
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cid = r.get("id")
                body = r.get("body") or ""
                if cid in seen or r.get("author") in SKIP_AUTHORS or body in ("[removed]", "[deleted]"):
                    continue
                seen.add(cid)
                add(accs, ("reddit", "r/" + sub), body, emotes)
        print("reddit", sub, len(seen), file=sys.stderr)

    aliases = {"destiny", "steven", "tiny", "stevie"}
    for fn in sorted(os.listdir(a.live)):
        if not DAYFILE.match(fn):
            continue
        op = gzip.open if fn.endswith(".gz") else open
        with op(os.path.join(a.live, fn), "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "bot" in (r.get("flags") or []):
                    continue
                text = r.get("text") or ""
                low = set(ling.WORD.findall(text.lower()))
                directed = bool(low & aliases) or (bool(low & ling.SECOND) and not text.startswith("@"))
                add(accs, ("live", "DGG 2026"), text, emotes, directed)

    os.makedirs(a.out, exist_ok=True)
    keys = None
    with open(os.path.join(a.out, "ling_compare.tsv"), "w") as fo:
        for (src, com, scope), acc in sorted(accs.items()):
            s = acc.summary()
            if keys is None:
                keys = list(s)
                fo.write("source\tcommunity\tscope\t" + "\t".join(keys) + "\n")
            fo.write(f"{src}\t{com}\t{scope}\t" + "\t".join("" if s[k] is None else str(s[k]) for k in keys) + "\n")
    print("wrote", os.path.join(a.out, "ling_compare.tsv"))


if __name__ == "__main__":
    main()
