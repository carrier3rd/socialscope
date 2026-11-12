#!/usr/bin/env python3
"""Weak-model-first cascade: label everything cheaply, flag what the weak model is measurably unsure of, and send
only those items (plus a random audit sample) to a stronger model after the user approves.

Steps (each reads/writes files in --out, so a run can stop and resume between them):

  weak    Label every item K times with a cheap model.
          python3 cascade.py weak --items items.jsonl --prompt prompt.txt --out run/ \
              --provider anthropic --model claude-haiku-5-5 --runs 3
          python3 cascade.py weak ... --provider gemini --model gemini-4-hydrogen --labels P,A,B,N   # adds logprobs

  flag    Decide what to escalate, from measured signals only (never the weak model's own say-so alone):
            unstable      the K runs disagree
            low_margin    Gemini only: top-label prob minus runner-up < --margin
            insufficient  Anthropic prompts only: the coder wrote "SUFFICIENT: no"
            label         the majority label is in --escalate-labels (e.g. positives you never want final from a
                          weak model)
          plus a random --audit share of the UNFLAGGED items, to estimate what the cascade misses.
          Writes escalate.jsonl and summary.md (counts, reasons, rough cost per strong model). Then STOP and ask the
          user whether to run the strong pass and on which model.
          python3 cascade.py flag --out run/ [--margin 0.8] [--audit 0.1] [--escalate-labels A,ENDORSE]

  strong  Only with --yes (the user's go-ahead). Labels escalate.jsonl with the strong model.
          python3 cascade.py strong --out run/ --model claude-opus-5-5 --effort high --yes

  report  Weak-vs-strong agreement on flagged items, the audit miss rate with a 95% CI, and final labels
          (strong label where it ran, weak majority elsewhere) in final.csv.
          python3 cascade.py report --out run/

Items: JSONL with "id", "target", optional "context", "subject", "glossary".
Prompt (Anthropic): instructions that end the reply with "LABEL: <code>" and, if you want the sufficiency signal,
"SUFFICIENT: yes|no". For --provider gemini the answer is constrained to --labels (one token), so VIEW/SUFFICIENT
lines are not available; the prompt should just say what the labels mean.

Credentials: Anthropic via the SDK's usual sources (ANTHROPIC_API_KEY, an `ant auth login` profile, ...);
Gemini via an x-goog-api-key header (environment network secret, or GEMINI_API_KEY in the environment).
"""
import argparse
import concurrent.futures as cf
import csv
import json
import math
import os
import random
import re
import subprocess
import sys
import time
from collections import Counter

# Rough list prices per million tokens (input, output), Nov 2026. Check current pricing before relying on totals.
PRICES = {"claude-haiku-5-5": (0.10, 0.50), "claude-sonnet-5-5": (2.0, 10.0), "claude-opus-5-5": (4.0, 20.0),
          "claude-fable-5-2": (8.0, 40.0)}
LABEL = re.compile(r"^\s*\**LABEL\**\s*:\s*\**\s*([A-Za-z_]+)", re.M)
SUFF = re.compile(r"^\s*\**SUFFICIENT\**\s*:\s*\**\s*(yes|no)", re.M | re.I)


def load_jsonl(p):
    return [json.loads(x) for x in open(p) if x.strip()]


def render(prompt, it, with_context=True):
    parts = [prompt.rstrip(), "", "=== ITEM"]
    if it.get("subject"):
        parts.append(f"SUBJECT: {it['subject']}")
    if with_context:
        parts.append("CONTEXT: " + (it["context"] if it.get("context") else "(none available)"))
    if it.get("glossary"):
        parts.append("GLOSSARY: " + it["glossary"])
    parts.append("TARGET: " + it["target"])
    return "\n".join(parts)


# ---------------------------------------------------------------- providers
def call_anthropic(client, model, effort, text):
    import anthropic
    for attempt in range(6):
        try:
            msg = client.messages.create(model=model, max_tokens=4000, output_config={"effort": effort},
                                         messages=[{"role": "user", "content": text}])
            break
        except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.InternalServerError):
            time.sleep(2 ** attempt * 5)
    else:
        return {"error": "gave up after retries"}
    if msg.stop_reason == "refusal":
        return {"error": "refusal"}
    out = "".join(b.text for b in msg.content if b.type == "text")
    lab, suff = LABEL.findall(out), SUFF.findall(out)
    return {"label": lab[-1].upper() if lab else "", "sufficient": suff[-1].lower() if suff else "",
            "in_tok": msg.usage.input_tokens, "out_tok": msg.usage.output_tokens}


def call_gemini(model, labels, text):
    body = json.dumps({"contents": [{"parts": [{"text": text}]}], "generationConfig": {
        "responseMimeType": "text/x.enum", "responseSchema": {"type": "STRING", "enum": labels},
        "thinkingConfig": {"thinkingLevel": "low"}, "responseLogprobs": True, "logprobs": 5,
        "maxOutputTokens": 4096}})
    hdr = ["-H", "Content-Type: application/json"]
    if os.environ.get("GEMINI_API_KEY"):
        hdr += ["-H", "x-goog-api-key: " + os.environ["GEMINI_API_KEY"]]
    for attempt in range(8):
        p = subprocess.run(["curl", "-sS", "--max-time", "120", *hdr, "--data-binary", "@-",
                            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"],
                           input=body, capture_output=True, text=True)
        try:
            r = json.loads(p.stdout)
        except ValueError:
            time.sleep(10)
            continue
        if "error" in r:
            if r["error"].get("code") in (429, 500, 503):
                time.sleep(min(30 * (attempt + 1), 300))
                continue
            return {"error": str(r["error"].get("message", r["error"]))[:200]}
        c = r["candidates"][0]
        txt = "".join(x.get("text", "") for x in c.get("content", {}).get("parts", []) if not x.get("thought"))
        lr = c.get("logprobsResult", {})
        dist = {}
        for ch, top in zip(lr.get("chosenCandidates", []), lr.get("topCandidates", [])):
            if ch["token"].strip():
                for t in top["candidates"]:
                    k = t["token"].strip().upper()
                    if k in labels:
                        dist[k] = dist.get(k, 0) + math.exp(t["logProbability"])
                break
        s = sum(dist.values()) or 1
        um = r.get("usageMetadata", {})
        return {"label": txt.strip().upper(), "dist": {k: v / s for k, v in dist.items()},
                "in_tok": um.get("promptTokenCount", 0), "out_tok": um.get("candidatesTokenCount", 0)}
    return {"error": "gave up after retries"}


def run_calls(jobs, provider, model, effort, labels, workers):
    """jobs: list of (key, text). Returns {key: result}."""
    client = None
    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
    fn = (lambda t: call_anthropic(client, model, effort, t)) if provider == "anthropic" \
        else (lambda t: call_gemini(model, labels, t))
    out = {}
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fn, t): k for k, t in jobs}
        for n, f in enumerate(cf.as_completed(futs), 1):
            out[futs[f]] = f.result()
            if n % 25 == 0:
                print(f"  {n}/{len(jobs)}", flush=True)
    return out


# ---------------------------------------------------------------- steps
def weak(a):
    os.makedirs(a.out, exist_ok=True)
    items = load_jsonl(a.items)
    prompt = open(a.prompt).read()
    labels = [x.strip().upper() for x in a.labels.split(",")] if a.labels else None
    if a.provider == "gemini" and not labels:
        sys.exit("--labels is required for --provider gemini")
    json.dump({"items": a.items, "prompt": a.prompt, "provider": a.provider, "model": a.model, "effort": a.effort,
               "labels": labels, "runs": a.runs, "with_context": not a.no_context},
              open(os.path.join(a.out, "weak_config.json"), "w"), indent=1)
    path = os.path.join(a.out, "weak.jsonl")
    done = {(r["id"], r["run"]) for r in load_jsonl(path)} if os.path.exists(path) else set()
    jobs = []
    for run in range(1, a.runs + 1):
        order = items[:]
        random.Random(100 + run).shuffle(order)
        jobs += [((str(it["id"]), run), render(prompt, it, not a.no_context)) for it in order
                 if (str(it["id"]), run) not in done]
    print(f"weak pass: {len(items)} items x {a.runs} runs = {len(jobs)} calls on {a.model}")
    res = run_calls(jobs, a.provider, a.model, a.effort, labels, a.workers)
    with open(path, "a") as f:
        for (iid, run), r in res.items():
            f.write(json.dumps({"id": iid, "run": run, **r}) + "\n")
    print("errors:", sum("error" in r for r in res.values()))


def flag(a):
    cfg = json.load(open(os.path.join(a.out, "weak_config.json")))
    items = {str(it["id"]): it for it in load_jsonl(cfg["items"])}
    rows = [r for r in load_jsonl(os.path.join(a.out, "weak.jsonl")) if r.get("label")]
    by = {}
    for r in rows:
        by.setdefault(r["id"], []).append(r)
    esc_labels = {x.strip().upper() for x in a.escalate_labels.split(",")} if a.escalate_labels else set()
    flagged, unflagged, reasons = [], [], Counter()
    for iid in items:
        rs = by.get(iid, [])
        why = []
        if not rs:
            why.append("no_weak_label")
        else:
            labs = Counter(r["label"] for r in rs)
            maj = labs.most_common(1)[0][0]
            if len(labs) > 1:
                why.append("unstable")
            margins = []
            for r in rs:
                d = sorted((r.get("dist") or {}).values(), reverse=True)
                if d:
                    margins.append(d[0] - (d[1] if len(d) > 1 else 0))
            if margins and min(margins) < a.margin:
                why.append("low_margin")
            if any(r.get("sufficient") == "no" for r in rs):
                why.append("insufficient")
            if maj in esc_labels:
                why.append("label")
        (flagged if why else unflagged).append(iid)
        for w in why:
            reasons[w] += 1
        items[iid]["_why"] = why
    rnd = random.Random(a.seed)
    audit = sorted(rnd.sample(unflagged, min(len(unflagged), math.ceil(a.audit * len(unflagged))))) if a.audit else []
    with open(os.path.join(a.out, "escalate.jsonl"), "w") as f:
        for iid in flagged:
            f.write(json.dumps({"id": iid, "why": items[iid]["_why"], "audit": False}) + "\n")
        for iid in audit:
            f.write(json.dumps({"id": iid, "why": [], "audit": True}) + "\n")
    # rough cost: weak-pass input tokens per item as the size guide, ~600 output tokens per strong call
    in_tok = [r.get("in_tok", 0) for r in rows if r.get("in_tok")]
    avg_in = (sum(in_tok) / len(in_tok)) if in_tok else 600
    n = len(flagged) + len(audit)
    lines = [f"# Cascade summary ({cfg['model']}, {cfg['runs']} runs per item)", "",
             f"- Items: {len(items)}; flagged: **{len(flagged)}** ({len(flagged) / max(1, len(items)):.0%}); "
             f"audit sample of unflagged: {len(audit)}; to send to a strong model: **{n}**",
             f"- Flag reasons (an item can have several): {dict(reasons)}",
             f"- Thresholds: margin < {a.margin}; audit share {a.audit}; escalate labels {sorted(esc_labels) or '-'}",
             "", "Rough strong-pass cost (list price, ~{:.0f} input + ~600 output tokens per call; "
             "check current pricing):".format(avg_in)]
    for m, (pi, po) in PRICES.items():
        lines.append(f"- {m}: ${n * (avg_in * pi + 600 * po) / 1e6:.2f}")
    lines += ["", "Next: ask the user whether to run the strong pass, and on which model:",
              f"`python3 cascade.py strong --out {a.out} --model claude-opus-5-5 --effort high --yes`"]
    open(os.path.join(a.out, "summary.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


def strong(a):
    cfg = json.load(open(os.path.join(a.out, "weak_config.json")))
    esc = load_jsonl(os.path.join(a.out, "escalate.jsonl"))
    if not a.yes:
        sys.exit(f"{len(esc)} items are queued. The strong pass costs money: rerun with --yes once the user has "
                 f"approved it (see {os.path.join(a.out, 'summary.md')}).")
    items = {str(it["id"]): it for it in load_jsonl(cfg["items"])}
    prompt = open(a.prompt or cfg["prompt"]).read()
    labels = cfg["labels"]
    path = os.path.join(a.out, "strong.jsonl")
    done = {r["id"] for r in load_jsonl(path)} if os.path.exists(path) else set()
    jobs = [(e["id"], render(prompt, items[e["id"]], cfg["with_context"])) for e in esc if e["id"] not in done]
    print(f"strong pass: {len(jobs)} calls on {a.model}")
    res = run_calls(jobs, a.provider, a.model, a.effort, labels, a.workers)
    with open(path, "a") as f:
        for iid, r in res.items():
            f.write(json.dumps({"id": iid, "model": a.model, **r}) + "\n")
    print("errors:", sum("error" in r for r in res.values()))


def wilson(k, n, z=1.96):
    if not n:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / den, (c + h) / den)


def report(a):
    cfg = json.load(open(os.path.join(a.out, "weak_config.json")))
    items = [str(it["id"]) for it in load_jsonl(cfg["items"])]
    weak_rows = [r for r in load_jsonl(os.path.join(a.out, "weak.jsonl")) if r.get("label")]
    wmaj = {}
    for iid in items:
        c = Counter(r["label"] for r in weak_rows if r["id"] == iid)
        wmaj[iid] = c.most_common(1)[0][0] if c else ""
    esc = {e["id"]: e for e in load_jsonl(os.path.join(a.out, "escalate.jsonl"))}
    spath = os.path.join(a.out, "strong.jsonl")
    st = {r["id"]: r for r in load_jsonl(spath) if r.get("label")} if os.path.exists(spath) else {}
    L = [f"# Cascade report: weak {cfg['model']} -> strong {next(iter(st.values()))['model'] if st else '(not run)'}",
         ""]
    for name, audit in (("Flagged items", False), ("Audit sample (unflagged)", True)):
        ids = [i for i, e in esc.items() if e["audit"] == audit and i in st]
        k = sum(st[i]["label"] != wmaj[i] for i in ids)
        lo, hi = wilson(k, len(ids))
        L.append(f"- {name}: strong model changed {k}/{len(ids)} weak labels "
                 f"({k / max(1, len(ids)):.0%}, 95% CI {lo:.0%}-{hi:.0%})")
        if audit and ids:
            L.append(f"  - Estimated share of UNFLAGGED items the weak model gets 'wrong' by the strong model's "
                     f"reading: {lo:.0%}-{hi:.0%}. Strong-model agreement is not ground truth: models share biases.")
        trans = Counter(f"{wmaj[i]}->{st[i]['label']}" for i in ids if st[i]["label"] != wmaj[i])
        if trans:
            L.append(f"  - Changes: {dict(trans.most_common())}")
    why = Counter()
    for i, e in esc.items():
        if not e["audit"] and i in st and st[i]["label"] != wmaj[i]:
            why.update(e["why"])
    L.append(f"- Flag reasons on items the strong model changed: {dict(why)}")
    with open(os.path.join(a.out, "final.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "label", "source", "weak_majority", "flagged_because"])
        for iid in items:
            src = "strong" if iid in st else "weak"
            w.writerow([iid, st[iid]["label"] if iid in st else wmaj[iid], src, wmaj[iid],
                        "|".join(esc.get(iid, {}).get("why", []))])
    open(os.path.join(a.out, "report.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))
    print("final labels:", os.path.join(a.out, "final.csv"))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    w = sp.add_parser("weak")
    w.add_argument("--items", required=True)
    w.add_argument("--prompt", required=True)
    w.add_argument("--out", required=True)
    w.add_argument("--provider", choices=["anthropic", "gemini"], default="anthropic")
    w.add_argument("--model", default="claude-haiku-5-5")
    w.add_argument("--effort", default="low")
    w.add_argument("--labels", help="comma list; required for gemini")
    w.add_argument("--runs", type=int, default=3)
    w.add_argument("--workers", type=int, default=4)
    w.add_argument("--no-context", action="store_true", help="code the target alone")
    f = sp.add_parser("flag")
    f.add_argument("--out", required=True)
    f.add_argument("--margin", type=float, default=0.8)
    f.add_argument("--audit", type=float, default=0.1)
    f.add_argument("--escalate-labels", default="")
    f.add_argument("--seed", type=int, default=7)
    s = sp.add_parser("strong")
    s.add_argument("--out", required=True)
    s.add_argument("--provider", choices=["anthropic", "gemini"], default="anthropic")
    s.add_argument("--model", default="claude-opus-5-5")
    s.add_argument("--effort", default="high")
    s.add_argument("--prompt", help="defaults to the weak pass prompt")
    s.add_argument("--workers", type=int, default=4)
    s.add_argument("--yes", action="store_true", help="the user approved the strong pass")
    r = sp.add_parser("report")
    r.add_argument("--out", required=True)
    a = p.parse_args()
    {"weak": weak, "flag": flag, "strong": strong, "report": report}[a.cmd](a)


if __name__ == "__main__":
    main()
