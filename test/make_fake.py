"""Synthetic Reddit comments: organic users plus a planted 6-account ring."""
import json, random
random.seed(7)
subs = ["streamdrama", "clipsfail", "streamerfans", "news_chat"]
words = ("stream chat clip game take honestly wild funny dumb point context watched yesterday "
         "edit mod ban drama tweet video people think agree disagree opinion good bad weird long "
         "short reaction guest topic segment vod highlight debate argument").split()
T0 = 1_760_000_000
out = []

def comment(author, sub, t, text, parent=None, acct_created=None):
    out.append({"id": f"c{len(out)}", "author": author, "subreddit": sub, "created_utc": int(t),
                "body": text, "parent_id": parent or f"t3_{random.randint(1, 400)}",
                "author_created_utc": acct_created})

# organic: 300 users, random times over 14 days, random text
for u in range(300):
    created = T0 - random.randint(200, 3000) * 86400
    for _ in range(random.randint(1, 25)):
        n = random.randint(6, 30)
        comment(f"user{u}", random.choice(subs), T0 + random.random() * 14 * 86400,
                " ".join(random.choice(words) for _ in range(n)), acct_created=created)

# organic people repeating a popular copypasta, spread over days (should cluster but not flag accounts)
pasta = "i am once again asking the mods to please stop deleting every single clip from the vod"
for u in random.sample(range(300), 12):
    comment(f"user{u}", random.choice(subs), T0 + random.random() * 14 * 86400, pasta)

# the ring: 6 young accounts, 3 talking points, light rewording, posted across subs within minutes,
# on a near-fixed schedule (every ~45 min)
points = [
    "the leaked clip proves he knew about the sponsorship scam for months and lied to chat about it",
    "his own mods confirmed the donations were faked, everyone should unsubscribe before it gets worse",
    "real fans are leaving, viewer numbers dropped forty percent this week and the sponsors are pulling out",
]
swaps = [("everyone", "every viewer"), ("months", "a long time"), ("real fans", "actual fans"), ("", "")]
for b in range(6):
    created = T0 - random.randint(3, 20) * 86400
    t = T0 + 3600 * 24 + b * 40
    for k in range(40):
        p = points[k % 3]
        a, c = random.choice(swaps)
        text = p.replace(a, c) if a else p
        comment(f"ring_bot{b}", subs[(k + b) % len(subs)], t, text, parent=f"t3_ring{k}", acct_created=created)
        t += 2700 + random.randint(-90, 90)

random.shuffle(out)
with open("fake.jsonl", "w") as fh:
    for r in out:
        fh.write(json.dumps(r) + "\n")
print(len(out), "rows")
