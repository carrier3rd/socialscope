#!/usr/bin/env python3
"""With/without-context flip calibration on the Anthropic Message Batches API.

Measures how often a coder's label changes when context is added, and which way, against a rerun noise floor.
Design (see SKILL.md "Calibrate before you trust a coder that sees context"):
  C0 = target only, C1 = target + context; two independent runs each; one item per request; shuffled submission.
  Items with no context are a placebo (identical input in both conditions).

Input: a JSONL file, one item per line:
  {"id": "...", "target": "text to code", "context": "parent / preceding lines / transcript or null",
   "subject": "optional", "glossary": "optional"}
Prompt: a text file with the coding instructions. It must tell the coder to end its reply with one line
  "LABEL: <code>" and may ask for "VIEW: <own|echo|quote|report|unclear>". The script appends the item.

Usage (pre-register predictions first, then):
  python3 flip_calibration.py submit  --items items.jsonl --prompt prompt.txt --out calib/ [--model claude-opus-5-5]
  python3 flip_calibration.py collect --out calib/            # waits for the batch, writes runs/*_codes.csv
  python3 analyze.py calib/ calib/                           # flip rates, noise floor, transitions

Cost: 4 requests per item, at Batch API prices (50% off). Check with --dry-run first.
"""
import argparse
import csv
import json
import os
import random
import re
import sys
import time

CONDS = (("C0", 1, 11), ("C0", 2, 12), ("C1", 1, 21), ("C1", 2, 22))


def load_items(path):
    items = [json.loads(line) for line in open(path) if line.strip()]
    for i, it in enumerate(items):
        it["_idx"] = i
    return items


def render(prompt, it, cond):
    parts = [prompt.rstrip(), "", "=== ITEM"]
    if it.get("subject"):
        parts.append(f"SUBJECT: {it['subject']}")
    if cond == "C1":
        parts.append("CONTEXT: " + (it["context"] if it.get("context") else "(none available)"))
    if it.get("glossary"):
        parts.append("GLOSSARY: " + it["glossary"])
    parts.append("TARGET: " + it["target"])
    return "\n".join(parts)


def submit(a):
    import anthropic
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    items = load_items(a.items)
    prompt = open(a.prompt).read()
    os.makedirs(os.path.join(a.out, "runs"), exist_ok=True)
    # items.jsonl in the schema analyze.py reads
    with open(os.path.join(a.out, "items.jsonl"), "w") as f:
        for it in items:
            f.write(json.dumps({
                "item": str(it["id"]), "subject": it.get("subject") or "", "parent": it.get("context"),
                "comment": it["target"], "glossary": it.get("glossary"),
                "comment_has_quote": bool(re.search(r"(^|\n)\s*>", it["target"])),
                "parent_truncated": bool(it.get("context")) and it["context"].rstrip().endswith("[...]"),
            }) + "\n")
    reqs = []
    for cond, run, seed in CONDS:
        order = items[:]
        random.Random(seed).shuffle(order)
        for it in order:
            reqs.append(Request(
                custom_id=f"{cond}_r{run}_{it['_idx']}",
                params=MessageCreateParamsNonStreaming(
                    model=a.model, max_tokens=4000, output_config={"effort": a.effort},
                    messages=[{"role": "user", "content": render(prompt, it, cond)}],
                ),
            ))
    print(f"{len(items)} items -> {len(reqs)} requests ({a.model}, effort {a.effort})")
    if a.dry_run:
        print(reqs[0]["params"]["messages"][0]["content"][:1500])
        return
    batch = anthropic.Anthropic().messages.batches.create(requests=reqs)
    json.dump({"batch_id": batch.id, "ids": {str(it["_idx"]): str(it["id"]) for it in items}},
              open(os.path.join(a.out, "batch.json"), "w"))
    print("batch", batch.id, batch.processing_status)


LABEL = re.compile(r"^\s*LABEL\s*:\s*([A-Za-z_]+)", re.M)
VIEW = re.compile(r"^\s*VIEW\s*:\s*([A-Za-z_]+)", re.M)


def collect(a):
    import anthropic
    client = anthropic.Anthropic()
    meta = json.load(open(os.path.join(a.out, "batch.json")))
    while True:
        b = client.messages.batches.retrieve(meta["batch_id"])
        if b.processing_status == "ended":
            break
        print("status", b.processing_status, "processing", b.request_counts.processing, flush=True)
        time.sleep(60)
    rows = {f"{c}_r{r}": [] for c, r, _ in CONDS}
    bad = 0
    for res in client.messages.batches.results(meta["batch_id"]):
        cond_run, idx = res.custom_id.rsplit("_", 1)
        item = meta["ids"][idx]
        if res.result.type != "succeeded":
            bad += 1
            continue
        msg = res.result.message
        if msg.stop_reason == "refusal":
            bad += 1
            continue
        text = "".join(blk.text for blk in msg.content if blk.type == "text")
        lab, view = LABEL.findall(text), VIEW.findall(text)
        if not lab:
            bad += 1
            continue
        rows[cond_run].append((item, view[-1].lower() if view else "", lab[-1].upper()))
    for name, rs in rows.items():
        with open(os.path.join(a.out, "runs", f"{name}_codes.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["item", "view", "code"])
            w.writerows(rs)
        print(name, len(rs), "rows")
    print("unparsed / errored / refused:", bad)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("submit")
    s.add_argument("--items", required=True)
    s.add_argument("--prompt", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--model", default="claude-opus-5-5")
    s.add_argument("--effort", default="low", choices=["low", "medium", "high", "xhigh", "max"])
    s.add_argument("--dry-run", action="store_true")
    c = sp.add_parser("collect")
    c.add_argument("--out", required=True)
    a = p.parse_args()
    {"submit": submit, "collect": collect}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
