import json, os, random, subprocess, sys, time, math
d = sys.argv[1]; MODEL = "gemini-4-hydrogen"
items = [json.loads(l) for l in open(os.path.join(d, "items.jsonl"))]
out = os.path.join(d, "runs", "gemini_raw.jsonl")
done = set()
if os.path.exists(out):
    for l in open(out):
        r = json.loads(l); done.add((r["cond"], r["run"], r["item"]))
HEAD = ("You are coding a Reddit comment for STANCE of the commenter toward a named subject.\n"
        "{ctx}Decide whether the commenter states their own view or echoes someone else's view to mock it; "
        "text after \">\" is quoted from someone else and is never the commenter's view. If echoing, the stance is the "
        "opposite of the echoed view. Glossary notes explain community slang.\n"
        "P = pro / supportive / defends it; A = against / critical / attacks it; "
        "B = clearly both; N = no lean, off-topic, or cannot tell.\n"
        "Answer with ONE letter only: P, A, B or N.\n\n")
def prompt(it, cond):
    ctx = "Read the parent comment (what this comment replies to) first. " if cond == "C1" else ""
    s = HEAD.format(ctx=ctx) + f"SUBJECT: {it['subject']}\n"
    if cond == "C1":
        s += "PARENT: " + (it["parent"] or "(none: this replies directly to the post)") + "\n"
    s += "COMMENT: " + it["comment"] + "\n"
    if it["glossary"]: s += "GLOSSARY: " + it["glossary"] + "\n"
    return s
def call(text):
    body = json.dumps({"contents": [{"parts": [{"text": text}]}],
                       "generationConfig": {"responseMimeType": "text/x.enum", "responseSchema": {"type": "STRING", "enum": ["P", "A", "B", "N"]}, "thinkingConfig": {"thinkingLevel": "low"}, "responseLogprobs": True, "logprobs": 5, "maxOutputTokens": 4096}})
    for attempt in range(8):
        p = subprocess.run(["curl", "-sS", "--max-time", "120", "-H", "Content-Type: application/json",
                            f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
                            "--data-binary", "@-"], input=body, capture_output=True, text=True)
        try: r = json.loads(p.stdout)
        except Exception: time.sleep(10); continue
        if "error" in r:
            code = r["error"].get("code")
            if code in (429, 500, 503):
                delay = 30
                for det in r["error"].get("details", []):
                    if "retryDelay" in det:
                        try: delay = max(delay, float(det["retryDelay"].rstrip("s")) + 2)
                        except ValueError: pass
                print("retry", code, delay, flush=True); time.sleep(min(delay, 300)); continue
            return {"error": r["error"]}
        return r
    return {"error": "gave up"}
def parse(r):
    if "error" in r: return {"error": str(r["error"])[:200]}
    c = r["candidates"][0]
    text = "".join(p.get("text", "") for p in c.get("content", {}).get("parts", []) if not p.get("thought")).strip()
    lr = c.get("logprobsResult", {})
    dist = None
    for chosen, top in zip(lr.get("chosenCandidates", []), lr.get("topCandidates", [])):
        if chosen["token"].strip():
            dist = {}
            for t in top["candidates"]:
                k = t["token"].strip().upper()
                if k in ("P", "A", "B", "N"): dist[k] = dist.get(k, 0) + math.exp(t["logProbability"])
            break
    return {"text": text, "label": (text[:1].upper() if text else ""), "dist": dist}
jobs = [(c, r, s) for c, r, s in (("C0", 1, 31), ("C0", 2, 32), ("C1", 1, 41), ("C1", 2, 42))]
with open(out, "a") as f:
    for cond, run, seed in jobs:
        order = items[:]; random.Random(seed).shuffle(order)
        for it in order:
            if (cond, run, it["item"]) in done: continue
            res = parse(call(prompt(it, cond)))
            res.update(cond=cond, run=run, item=it["item"])
            f.write(json.dumps(res) + "\n"); f.flush()
        print("finished", cond, run, flush=True)
print("ALL DONE", flush=True)
