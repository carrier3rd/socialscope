import json, random, sys, os
d = sys.argv[1]
items = [json.loads(l) for l in open(os.path.join(d, "items.jsonl"))]
HEAD = """You are coding Reddit comments for STANCE toward a named subject. Work through each item in two steps before coding.

STEP 1, WHOSE VIEW. {ctx}Decide whether the commenter is stating their own view, or echoing someone else's view to mock it (sarcasm, parody, quoting an opponent's position in exaggerated form, "sure, because X is so great"). Text after ">" is quoted from someone else and is never the commenter's own view. Write VIEW = own, echo, or unclear.
STEP 2, STANCE of the COMMENTER (not of the person they are mocking) toward the subject:
P = pro / supportive / defends it
A = against / critical / attacks it
N = no lean, off-topic, or cannot tell
B = clearly both (praises one part, attacks another)
If VIEW = echo, the stance is the OPPOSITE of the view being echoed.

Glossary notes, when given, explain community slang in that item. Use them.

Output ONLY a CSV with header: item,view,code
One row per item, every item. Do not skip any.
"""
for cond, seeds in (("C0", (11, 12)), ("C1", (21, 22))):
    for run, seed in enumerate(seeds, 1):
        order = items[:]; random.Random(seed).shuffle(order)
        ctx = "Read the parent comment (what this comment replies to) first. " if cond == "C1" else ""
        out = [HEAD.format(ctx=ctx), f"\n{len(order)} items\n"]
        for it in order:
            out.append(f"\n=== ITEM {it['item']} | subject: {it['subject']}")
            if cond == "C1":
                out.append("PARENT: " + (it["parent"] if it["parent"] else "(none: this replies directly to the post)"))
            out.append("COMMENT: " + it["comment"])
            if it["glossary"]: out.append("GLOSSARY: " + it["glossary"])
        open(os.path.join(d, "runs", f"{cond}_r{run}_input.txt"), "w").write("\n".join(out) + "\n")
print("ok")
