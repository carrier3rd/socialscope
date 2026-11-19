#!/usr/bin/env python3
"""Label replay: com.atproto.label.subscribeLabels from cursor 0 for each labeler in targets.yaml.

NOT YET RUN AGAINST A LIVE LABELER (Nov 19 2026): the cloud session only checked that both hosts answer
/xrpc/_health. The frame format below follows the AT Protocol event-stream spec and is tested on synthetic
frames. The first laptop run should be `--max-frames 200` and a look at the printed counts.

Each frame is two DAG-CBOR objects: a header {op: 1, t: "#labels"} and a body {seq, labels: [...]}.
A label is {src, uri, val, cts} plus optional cid, neg, exp, ver, sig. `uri` is a DID for an account label or
an at:// URI for a label on one record.

What is written, per labeler, under <data>/raw/labels/<name>/:
  labels.jsonl.gz    one line per kept label: seq, src, uri, val, neg, cts, exp   (private; sig is dropped)
  counts.json        every value seen, kept or not: {val: {"YYYY-MM": n}}, plus negations. This is how label
                     volume over time is checked for outages (Skywatch, June 2026) without storing subjects.
  cursor.json        last seq handled; the next run resumes after it.
Only values on the labeler's whitelist in targets.yaml are written. Skywatch's political and identity values
are counted and dropped here, at collection, so no per-account faction label ever reaches disk.
Negations (neg: true) are kept for whitelisted values; the newest event per (src, uri, val) wins downstream.

Stops when the stream has been quiet for --quiet seconds (caught up), or at --max-frames.
Needs: websockets, cbor2, PyYAML.
"""
import argparse
import asyncio
import collections
import gzip
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bsky_common as bc  # noqa: E402


def decode_frame(raw):
    """(header, body) from one binary frame."""
    import cbor2
    buf = io.BytesIO(raw)
    return cbor2.load(buf), cbor2.load(buf)


def keep(val, vals, prefixes=()):
    return val in vals or any(val.startswith(p) for p in prefixes)


class LabelSink:
    def __init__(self, root, vals, prefixes=()):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.vals, self.prefixes = set(vals), tuple(prefixes)
        self.counts = bc.load_json(self.root / "counts.json", {})
        self.seq = bc.load_json(self.root / "cursor.json", {}).get("seq", 0)
        self.fh = gzip.open(self.root / "labels.jsonl.gz", "at", encoding="utf-8")
        self.n = collections.Counter()

    def frame(self, raw):
        """Handle one frame. Returns False on an error frame, True otherwise."""
        hdr, body = decode_frame(raw)
        if hdr.get("op") != 1:
            self.n["error_frames"] += 1
            self.error = body
            return False
        self.n["frames"] += 1
        if hdr.get("t") != "#labels":
            self.n["other_frames"] += 1   # "#info", e.g. OutdatedCursor
            return True
        seq = body.get("seq", 0)
        for lab in body.get("labels") or []:
            val, neg = lab.get("val", ""), bool(lab.get("neg"))
            month = str(lab.get("cts", ""))[:7]
            by = self.counts.setdefault(("neg:" if neg else "") + val, {})
            by[month] = by.get(month, 0) + 1
            if keep(val, self.vals, self.prefixes):
                self.fh.write(json.dumps({"seq": seq, "src": lab.get("src"), "uri": lab.get("uri"), "val": val,
                                          "neg": neg, "cts": lab.get("cts"), "exp": lab.get("exp")}) + "\n")
                self.n["kept"] += 1
            else:
                self.n["dropped"] += 1
        self.seq = max(self.seq, seq)
        return True

    def save(self):
        self.fh.flush()
        bc.atomic_json(self.root / "counts.json", self.counts)
        bc.atomic_json(self.root / "cursor.json", {"seq": self.seq, "saved": bc.now_iso()})

    def close(self):
        self.save()
        self.fh.close()


async def replay(host, sink, user_agent, quiet=30, max_frames=0):
    import websockets
    url = f"wss://{host}/xrpc/com.atproto.label.subscribeLabels?cursor={sink.seq}"
    async with websockets.connect(url, additional_headers={"User-Agent": user_agent}, max_size=2**24) as ws:
        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), quiet)
            except asyncio.TimeoutError:
                return "caught up"
            if isinstance(raw, str) or not sink.frame(raw):
                return "error frame"
            if sink.n["frames"] % 1000 == 0:
                sink.save()
            if max_frames and sink.n["frames"] >= max_frames:
                return "frame limit"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labeler", action="append", help="name from targets.yaml (default: all)")
    ap.add_argument("--quiet", type=int, default=30)
    ap.add_argument("--max-frames", type=int, default=0)
    args = ap.parse_args()
    cfg = bc.load_config()
    for name, lab in cfg["calibration"]["labelers"].items():
        if args.labeler and name not in args.labeler:
            continue
        sink = LabelSink(bc.data_dir() / "raw" / "labels" / name, lab["keep_vals"], lab.get("keep_prefixes", ()))
        start = sink.seq
        try:
            how = asyncio.run(replay(lab["host"], sink, cfg["collect"]["user_agent"], args.quiet, args.max_frames))
        except Exception as e:
            how = "failed: " + type(e).__name__
        finally:
            sink.close()
        print("labels", name, json.dumps({"ended": how, "from_seq": start, "to_seq": sink.seq, **sink.n,
                                          "distinct_values_seen": len(sink.counts)}))


if __name__ == "__main__":
    main()
