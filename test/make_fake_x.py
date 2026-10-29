"""Synthetic X data as API v2 pages: organic users plus an 8-account amplification ring."""
import json, random
from datetime import datetime, timezone
random.seed(11)
iso = lambda t: datetime.fromtimestamp(t, timezone.utc).isoformat().replace("+00:00", "Z")
words = ("stream clip take wild funny dumb context watched edit ban drama video people think agree "
         "opinion weird reaction guest segment highlight debate argument chat vod").split()
tags = ["streamdrama", "twitch", "clips", "news"]
T0 = 1_760_000_000
users, tweets = {}, []

def user(uid, handle, age_days):
    users[uid] = {"id": uid, "username": handle, "created_at": iso(T0 - age_days * 86400)}

def tweet(uid, t, text="", tag=None, rt=None, reply=None):
    tw = {"id": str(len(tweets) + 10_000), "author_id": uid, "created_at": iso(t), "text": text,
          "conversation_id": str(random.randint(1, 300)), "entities": {}}
    if tag:
        tw["text"] += f" #{tag}"
        tw["entities"]["hashtags"] = [{"tag": tag}]
    refs = []
    if rt: refs.append({"type": "retweeted", "id": rt}); tw["text"] = "RT @someone: ..."
    if reply: refs.append({"type": "replied_to", "id": reply})
    if refs: tw["referenced_tweets"] = refs
    tweets.append(tw)
    return tw["id"]

# organic: 250 users tweeting and occasionally retweeting popular posts at random times
popular = []
for u in range(250):
    user(f"u{u}", f"person{u}", random.randint(200, 4000))
for u in range(250):
    for _ in range(random.randint(1, 20)):
        t = T0 + random.random() * 10 * 86400
        if popular and random.random() < 0.25:
            tweet(f"u{u}", t, rt=random.choice(popular))
        else:
            tid = tweet(f"u{u}", t, " ".join(random.choice(words) for _ in range(random.randint(6, 25))),
                        tag=random.choice(tags) if random.random() < 0.6 else None)
            if random.random() < 0.05: popular.append(tid)

# ring: 8 new accounts; seed account posts talking points, others retweet within seconds,
# and they post reworded versions under different hashtags
points = ["the sponsor contract leak proves the whole charity stream was a scam from day one",
          "mods are mass banning anyone who asks where the donation money went, screenshot everything"]
for b in range(8):
    user(f"bot{b}", f"truthwatch{b}{random.randint(100, 999)}", random.randint(2, 25))
t = T0 + 2 * 86400
for k in range(30):
    seed = tweet("bot0", t, points[k % 2], tag=tags[k % 4])
    for b in range(1, 8):
        tweet(f"bot{b}", t + random.randint(3, 40), rt=seed)
        if k % 3 == b % 3:
            tweet(f"bot{b}", t + random.randint(300, 1500), points[k % 2].replace("whole", "entire"),
                  tag=tags[(k + b) % 4])
    t += 3600 + random.randint(-60, 60)

random.shuffle(tweets)
with open("fake_x.jsonl", "w") as fh:
    for i in range(0, len(tweets), 100):   # one v2 page per line
        page = tweets[i:i + 100]
        fh.write(json.dumps({"data": page, "includes": {"users": [users[x["author_id"]] for x in page]}}) + "\n")
print(len(tweets), "tweets")
