"""Phase 4 detectors (bluesky/detect/*.py): each plants a known pattern in synthetic tables and recovers it (spec,
Phase 4 acceptance). No network, no real accounts."""
import datetime as dt
import os
import random
import sys
import tempfile
import unittest
from pathlib import Path

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "bluesky", "detect"))
try:
    import duckdb  # noqa: F401
    import pyarrow as pa
    import pyarrow.parquet as pq
    import block_surge
    import dormant_hijack
    import follow_burst
    import like_farm
    import reply_bot
except ImportError:
    pa = None

DAY, HOUR, MIN = 86_400_000_000, 3_600_000_000, 60_000_000
T0 = 1_790_000_000_000_000 // DAY * DAY          # a UTC midnight
TGT = [f"did:plc:faketarget{i:015d}" for i in range(4)]
CFG = {"sides": {"progressive": [{"did": TGT[0]}, {"did": TGT[1]}], "government_right": [{"did": TGT[2]}, {"did": TGT[3]}]}}
TS = pa.timestamp("us", tz="UTC") if pa else None


def ts(us):
    return dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(microseconds=us)


def user(n):
    return f"did:plc:fakeuser{n:016d}"


def post(did, rkey, t, parent=None, root=None, text="x", embed=None):
    return {"uri": f"at://{did}/app.bsky.feed.post/{rkey}", "did": did, "rkey": rkey, "created_at": ts(t),
            "indexed_at": ts(t), "text": text, "langs": ["en"], "reply_parent": parent, "reply_root": root or parent,
            "quote_uri": None, "embed_type": embed, "facet_links": [], "facet_mentions": [], "sources": ["jetstream"]}


def inter(kind, actor, subject, t, n):
    return {"type": kind, "uri": f"at://{actor}/x/{kind}{n}", "actor_did": actor, "subject": subject, "list_uri": None,
            "created_at": ts(t), "rkey_time": ts(t), "time_us": t}


@unittest.skipIf(pa is None, "pyarrow/duckdb not installed")
class TestDetectors(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / "bluesky"
        (self.data / "processed" / "tables").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, posts=(), inters=(), plc=()):
        d = self.data / "processed" / "tables"
        L = pa.list_(pa.string())
        pq.write_table(pa.Table.from_pylist(list(posts), schema=pa.schema([
            ("uri", pa.string()), ("did", pa.string()), ("rkey", pa.string()), ("created_at", TS), ("indexed_at", TS),
            ("text", pa.string()), ("langs", L), ("reply_parent", pa.string()), ("reply_root", pa.string()),
            ("quote_uri", pa.string()), ("embed_type", pa.string()), ("facet_links", L), ("facet_mentions", L),
            ("sources", L)])), d / "posts.parquet")
        pq.write_table(pa.Table.from_pylist(list(inters), schema=pa.schema([
            ("type", pa.string()), ("uri", pa.string()), ("actor_did", pa.string()), ("subject", pa.string()),
            ("list_uri", pa.string()), ("created_at", TS), ("rkey_time", TS), ("time_us", pa.int64())])),
            d / "interactions.parquet")
        pq.write_table(pa.Table.from_pylist(list(plc), schema=pa.schema([
            ("did", pa.string()), ("op_type", pa.string()), ("handle", pa.string()), ("pds", pa.string()),
            ("rotation_keys_changed", pa.bool_()), ("created_at", TS), ("nullified", pa.bool_())])), d / "plc_ops.parquet")

    def test_like_farm_finds_the_planted_group_and_nothing_else(self):
        rnd = random.Random(1)
        tposts = [f"at://{TGT[i % 4]}/app.bsky.feed.post/3kfakep{i:06d}" for i in range(40)]
        farm = tposts[:8]                                  # 8 posts by 4 targets (i % 4)
        inters, n = [], 0
        for a in range(60):                                # 60 farm accounts: the same 8 posts (one skips one)
            for p in farm[: 8 if a % 2 else 7]:
                inters.append(inter("like", user(a), p, T0 + n, n)); n += 1
        for a in range(60, 400):                           # 340 organic likers: random posts
            for p in rnd.sample(tposts, rnd.randint(5, 12)):
                inters.append(inter("like", user(a), p, T0 + n, n)); n += 1
        self.write(inters=inters)
        summary, private = like_farm.run(self.data, CFG, T0, T0 + DAY)
        self.assertEqual(summary["groups"], 1)
        self.assertGreaterEqual(summary["largest_group"], 55)        # 7/8 = 0.875 overlap still joins
        self.assertTrue(set(private[0]["accounts"]) <= {user(a) for a in range(60)})
        self.assertGreaterEqual(private[0]["targets"], 3)

    def test_follow_burst_finds_bulk_followers_and_a_creation_streak(self):
        inters, plc, n = [], [], 0
        for k in range(60):                                # one account follows 60 accounts in 30 minutes
            inters.append(inter("follow", user(1), user(1000 + k), T0 + k * 30_000_000, n)); n += 1
        for a in range(12):                                # 12 new accounts made in one hour, all follow TGT[2]
            inters.append(inter("follow", user(100 + a), TGT[2], T0 + DAY, n)); n += 1
            plc.append({"did": user(100 + a), "op_type": "plc_operation", "handle": f"u{a}.bsky.social",
                        "pds": "https://x", "rotation_keys_changed": False, "created_at": ts(T0 + 10 * MIN + a),
                        "nullified": False})
        for a in range(12):                                # 12 old accounts follow TGT[3]: created over 12 days
            inters.append(inter("follow", user(200 + a), TGT[3], T0 + DAY, n)); n += 1
            plc.append({"did": user(200 + a), "op_type": "plc_operation", "handle": f"o{a}.bsky.social",
                        "pds": "https://x", "rotation_keys_changed": False, "created_at": ts(T0 - (a + 1) * DAY),
                        "nullified": False})
        self.write(inters=inters, plc=plc)
        summary, private = follow_burst.run(self.data, CFG, T0, T0 + 2 * DAY)
        self.assertEqual(summary["bulk_follow_accounts"], 1)
        self.assertEqual(summary["creation_streak_hours"], 1)
        self.assertEqual(private["streaks"][0]["target"], TGT[2])

    def test_dormant_hijack_needs_silence_change_and_ten_target_replies(self):
        tpost = f"at://{TGT[0]}/app.bsky.feed.post/3kfaketgt0001"
        posts = [post(TGT[0], "3kfaketgt0001", T0)]
        plc = []
        for who, change_days_before, replies in ((1, 10, 12), (2, 60, 12), (3, 10, 5)):
            d = user(who)
            posts.append(post(d, "3kfakeold0001", T0 - 400 * DAY))           # last post 400 days ago
            posts += [post(d, f"3kfakere{i:05d}", T0 + i * MIN, parent=tpost) for i in range(replies)]
            plc += [{"did": d, "op_type": "plc_operation", "handle": "old.bsky.social", "pds": "https://p",
                     "rotation_keys_changed": False, "created_at": ts(T0 - 900 * DAY), "nullified": False},
                    {"did": d, "op_type": "plc_operation", "handle": "new.example", "pds": "https://p",
                     "rotation_keys_changed": False, "created_at": ts(T0 - change_days_before * DAY), "nullified": False}]
        self.write(posts=posts, plc=plc)
        summary, private = dormant_hijack.run(self.data, CFG, T0, T0 + DAY)
        self.assertEqual(summary["matching_rule"], 1)                        # 2: change too early; 3: too few
        self.assertEqual(private[0]["did"], user(1))

    def test_reply_bot_flags_fast_reply_only_accounts(self):
        posts = []
        for i in range(12):
            tp = f"at://{TGT[i % 4]}/app.bsky.feed.post/3kfaketp{i:05d}"
            posts.append(post(TGT[i % 4], f"3kfaketp{i:05d}", T0 + i * HOUR))
            posts.append(post(user(1), f"3kfakebot{i:04d}", T0 + i * HOUR + 20_000_000, parent=tp, text="Thoughts?"))
            posts.append(post(user(2), f"3kfakehum{i:04d}", T0 + i * HOUR + 40 * MIN, parent=tp, text="a longer reply"))
            posts.append(post(user(3), f"3kfakepic{i:04d}", T0 + i * HOUR + 10_000_000, parent=tp,
                              embed="app.bsky.embed.images"))
        posts.append(post(user(2), "3kfakehumtop1", T0))                       # the human also posts originals
        self.write(posts=posts)
        summary, private = reply_bot.run(self.data, CFG, T0, T0 + DAY)
        self.assertEqual(summary["accounts_with_10_target_replies"], 3)
        self.assertEqual([p["did"] for p in private], [user(1)])                # 3 posts images, 2 is slow
        self.assertAlmostEqual(private[0]["bait_share"], 1.0)

    def test_block_surge_alarms_on_the_planted_hour_only(self):
        rnd = random.Random(2)
        inters, n = [], 0
        base_end = T0 + 7 * DAY
        for h in range(14 * 24):                               # two weeks: ~2 blockers per target-hour
            for t in TGT:
                for _ in range(rnd.choice([1, 2, 2, 3])):
                    inters.append(inter("block", user(n), t, T0 + h * HOUR + rnd.randrange(HOUR), n)); n += 1
        surge_h = 10 * 24 + 15
        for k in range(40):                                    # 40 extra distinct blockers of TGT[1] in one hour
            inters.append(inter("block", user(10**6 + k), TGT[1], T0 + surge_h * HOUR + k * MIN, n)); n += 1
        self.write(inters=inters)
        summary, private = block_surge.run(self.data, CFG, base_end, T0 + 14 * DAY, T0, base_end)
        self.assertEqual(summary["alarms"], 1)
        self.assertEqual((private[0]["target"], private[0]["hour"]), (TGT[1], (T0 + surge_h * HOUR) // HOUR))

    def test_nb_quantile(self):
        self.assertEqual(block_surge.nb_quantile(0.5, 0, 0.3), 0)
        self.assertGreaterEqual(block_surge.nb_quantile(0.999, 2.0, 0.0), 7)   # Poisson(2) 99.9% is 8
        self.assertGreater(block_surge.nb_quantile(0.999, 2.0, 1.0), block_surge.nb_quantile(0.999, 2.0, 0.0))


if __name__ == "__main__":
    unittest.main()
