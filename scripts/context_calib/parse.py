import json, re, sys
from collections import Counter
S = sys.argv[1]
def unesc(s):
    s = re.sub(r'\\+([>\[\]=*_#`~\-\\()!|.+])', r'\1', s)
    return s
items = []
for p in (1, 2, 3):
    cur = None; key = None
    for line in open(f"{S}/raw/part{p}.txt", encoding="utf-8"):
        line = line.rstrip("\n")
        m = re.match(r'^\\*=== ITEM (\d+) \| subject: (.*)$', line)
        if m:
            cur = dict(item=int(m[1]), subject=m[2].strip(), parent=None, comment=None, glossary=None, part=p)
            items.append(cur); key = None; continue
        if cur is None: continue
        m = re.match(r'^(PARENT|COMMENT|GLOSSARY):\s?(.*)$', line)
        if m:
            key = m[1].lower(); cur[key] = (cur[key] + "\n" if cur[key] and key == "glossary" else "") + m[2]; continue
        if line.strip() == "": key = None if key != "comment" else key; continue
        if line.startswith(("item,literal", "PART ")): key = None; continue
        if key: cur[key] += "\n" + line
for it in items:
    for k in ("parent", "comment", "glossary"):
        if it[k] is not None:
            it[k] = unesc(it[k]).strip() or None
    if it["parent"] and it["parent"].startswith("(none"): it["parent"] = None
    c = it["comment"] or ""
    it["comment_has_quote"] = bool(re.search(r'(^|\n|\s)>', c))
    it["parent_truncated"] = bool(it["parent"] and it["parent"].rstrip().endswith("[...]"))
with open(f"{S}/items.jsonl", "w", encoding="utf-8") as f:
    for it in items: f.write(json.dumps(it, ensure_ascii=False) + "\n")
print("total", len(items), "per part", Counter(i["part"] for i in items))
print("non-null parent", sum(i["parent"] is not None for i in items))
print("parent_truncated", sum(i["parent_truncated"] for i in items))
print("comment_has_quote", sum(i["comment_has_quote"] for i in items))
print("glossary non-null", sum(i["glossary"] is not None for i in items))
print("missing comment", [i["item"] for i in items if not i["comment"]])
L = [len(i["comment"] or "") for i in items]
print("comment len max", max(L), "min", min(L), "top5", sorted(L)[-5:])
PL = [len(i["parent"]) for i in items if i["parent"]]
print("parent len max", max(PL), "top5", sorted(PL)[-5:])
near = [(i["item"], len(i["comment"])) for i in items if len(i["comment"]) >= max(L) - 15]
print("comments within 15 of max", near)
noend = [(i["item"], len(i["comment"])) for i in items if len(i["comment"]) >= 0.9*max(L) and not re.search(r'[.!?)"\'”’…]\s*$', i["comment"])]
print("near-cap w/o ending punct", noend)
print("dup ids", [k for k, v in Counter(i["item"] for i in items).items() if v > 1])
print("dup comments", [k[:60] for k, v in Counter(i["comment"] for i in items).items() if v > 1])
print("leftover backslashes", [i["item"] for i in items if any("\\" in (i[k] or "") for k in ("parent", "comment", "glossary"))])
for i in items[:2]:
    print({k: (v[:70] + "...") if isinstance(v, str) and len(v) > 70 else v for k, v in i.items()})
