"""Phase 6 scorer (bluesky/evaluate/score_window.py) on synthetic tables: planted repliers, labels and alarms are
recovered exactly. No network, no real accounts."""
import datetime as dt
import os
import random
import sys
import tempfile
import unittest
from pathlib import Path

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "bluesky", "evaluate"))
try:
    import duckdb  # noqa: F401
    import pyarrow as pa
    import pyarrow.parquet as pq
    import score_window as sw
except ImportError:
    pa = None

DAY, HOUR, MIN = 86_400_000_000, 3_600_000_000, 60_000_000
T0 = 1_790_000_000_000_000 // DAY * DAY
TGT = [f"did:plc:faketarget{i:015d}" for i in range(4)]
MOD, SKY = "did:plc:fakemodlabeler0000000", "did:plc:fakeskywatch00000000"
CFG = {"sides": {"progressive": [{"did": TGT[0]}, {"did": TGT[1]}], "government_right": [{"did": TGT[2]}, {"did": TGT[3]}]},
       "calibration": {"labelers": {"bluesky_mod": {"did": MOD, "keep_vals": ["spam", "impersonation", "!takedown"]},
                                    "skywatch": {"did": SKY, "keep_vals": ["suspect-inauthentic"],
                                                 "keep_prefixes": ["repetitive-domain-spam-"]}},
                       "extra_known_bad": "known_bad/test.csv"}}
TS = pa.timestamp("us", tz="UTC") if pa else None
L = pa.list_(pa.string()) if pa else None


def ts(us):
    return None if us is None else dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(microseconds=us)


def user(n):
    return f"did:plc:fakeuser{n:016d}"


def post(did, rkey, t, parent=None, root=None, sources=("jetstream",)):
    return {"uri": f"at://{did}/app.bsky.feed.post/{rkey}", "did": did, "rkey": rkey, "created_at": ts(t),
            "indexed_at": ts(t), "text": "x", "langs": ["en"], "reply_parent": parent, "reply_root": root or parent,
            "quote_uri": None, "embed_type": None, "facet_links": [], "facet_mentions": [], "sources": list(sources)}


def block(actor, target, t, n):
    return {"type": "block", "uri": f"at://{actor}/app.bsky.graph.block/b{n}", "actor_did": actor, "subject": target,
            "list_uri": None, "created_at": ts(t), "rkey_time": ts(t), "time_us": t}


def label(src, subj, val, cts, neg=False, exp=None):
    return {"src": src, "uri_or_did": subj, "val": val, "neg": neg, "cts": ts(cts), "exp": ts(exp)}


@unittest.skipIf(pa is None, "pyarrow/duckdb not installed")
class TestScoreWindow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / "bluesky"
        (self.data / "processed" / "tables").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, posts, inters, labels, accounts):
        d = self.data / "processed" / "tables"
        pq.write_table(pa.Table.from_pylist(posts, schema=pa.schema([
            ("uri", pa.string()), ("did", pa.string()), ("rkey", pa.string()), ("created_at", TS), ("indexed_at", TS),
            ("text", pa.string()), ("langs", L), ("reply_parent", pa.string()), ("reply_root", pa.string()),
            ("quote_uri", pa.string()), ("embed_type", pa.string()), ("facet_links", L), ("facet_mentions", L),
            ("sources", L)])), d / "posts.parquet")
        pq.write_table(pa.Table.from_pylist(inters, schema=pa.schema([
            ("type", pa.string()), ("uri", pa.string()), ("actor_did", pa.string()), ("subject", pa.string()),
            ("list_uri", pa.string()), ("created_at", TS), ("rkey_time", TS), ("time_us", pa.int64())])),
            d / "interactions.parquet")
        pq.write_table(pa.Table.from_pylist(labels, schema=pa.schema([
            ("src", pa.string()), ("uri_or_did", pa.string()), ("val", pa.string()), ("neg", pa.bool_()),
            ("cts", TS), ("exp", TS)])), d / "labels.parquet")
        pq.write_table(pa.Table.from_pylist(accounts, schema=pa.schema([("did", pa.string()), ("status", pa.string())])),
                       d / "accounts.parquet")

    def test_planted_world(self):
        end = T0 + 21 * DAY
        cut = end + 7 * DAY
        tp = {i: f"at://{TGT[i]}/app.bsky.feed.post/3kfaketgt{i:05d}" for i in range(4)}
        posts = [post(TGT[i], f"3kfaketgt{i:05d}", T0 + HOUR) for i in range(4)]
        # progressive: users 0-199 reply to TGT[0]; government_right: users 200-299 reply to TGT[2];
        # users 0-9 also reply on the right (both sides); user 900 replies deep in a TGT[1] thread (root only)
        for u in range(200):
            posts.append(post(user(u), f"3kfr{u:06d}", T0 + 2 * HOUR, parent=tp[0],
                              sources=("jetstream", "history") if u < 3 else ("jetstream",)))
        for u in list(range(200, 300)) + list(range(10)):
            posts.append(post(user(u), f"3kfg{u:06d}", T0 + 3 * HOUR, parent=tp[2]))
        posts.append(post(user(900), "3kfdeep00001", T0 + 4 * HOUR, parent=f"at://{user(5)}/app.bsky.feed.post/3kfr000005",
                          root=tp[1]))
        posts.append(post(user(901), "3kflate00001", end + HOUR, parent=tp[0]))           # after the window: out
        posts.append(post(TGT[1], "3kftgtrep001", T0 + 5 * HOUR, parent=tp[0]))           # a target: excluded
        labels = [label(MOD, user(0), "spam", T0), label(MOD, user(1), "impersonation", end),
                  label(MOD, user(2), "!takedown", T0),
                  label(MOD, f"at://{user(3)}/app.bsky.feed.post/3kfr000003", "spam", T0),  # post label: no
                  label(MOD, user(4), "spam", T0, neg=True),                                # removed: no
                  label(MOD, user(6), "spam", T0, exp=T0 + DAY),                            # expired: no
                  label(MOD, user(7), "spam", cut + HOUR),                                  # after cutoff: no
                  label(MOD, user(8), "porn", T0),                                          # not kept: no
                  label(SKY, user(250), "repetitive-domain-spam-x", T0),                    # Tier B
                  label(SKY, user(251), "suspect-inauthentic", T0)]
        (self.data / "known_bad").mkdir()
        (self.data / "known_bad" / "test.csv").write_text("did,source\n" + user(260) + ",report\n", encoding="utf-8")
        accounts = [{"did": user(u), "status": "active"} for u in range(300)] + [{"did": user(299), "status": "deactivated"}]
        # blocks: TGT[2] has two alarm hours in week 2, one 3 h after its only (hence top 10%) post, one far away
        h_post = (T0 + 8 * DAY) // HOUR
        posts.append(post(TGT[2], "3kfbig000001", h_post * HOUR + 10 * MIN))
        for k in range(150):                                    # more replies than tp[2]'s 110: its top post
            posts.append(post(user(1000 + k), f"3kfbr{k:05d}", h_post * HOUR + 20 * MIN, parent=f"at://{TGT[2]}/app.bsky.feed.post/3kfbig000001"))
        h1, h2 = h_post + 3, h_post + 100
        inters, n = [], 0
        for k in range(10):                                     # alarm hour 1: 10 blockers, 2 labeled
            inters.append(block(user([0, 250][k] if k < 2 else 500 + k), TGT[2], h1 * HOUR + k * MIN, n)); n += 1
        for k in range(10):                                     # alarm hour 2: 10 blockers, none labeled
            inters.append(block(user(600 + k), TGT[2], h2 * HOUR + k * MIN, n)); n += 1
        for k in range(40):                                     # other hours: 40 blockers, 2 labeled
            who = user(2) if k == 0 else user(251) if k == 1 else user(700 + k)
            inters.append(block(who, TGT[2], (h_post + 20 + k) * HOUR, n)); n += 1
        self.write(posts, inters, labels, accounts)

        surge = [{"target": TGT[2], "hour": h1, "blockers": 10, "expected": 1.0},
                 {"target": TGT[2], "hour": h2, "blockers": 10, "expected": 1.0}]
        like = {"groups": 1, "largest_group": 64}
        dormant = [{"did": user(205), "resume_us": T0, "target_replies": 12}, {"did": user(99999), "resume_us": T0,
                                                                                "target_replies": 12}]
        out = sw.score(self.data, CFG, T0, end, cut, T0 + 7 * DAY, end, like, surge, dormant)

        self.assertEqual(out["in_thread_repliers"], {"progressive": 201, "government_right": 260})
        self.assertEqual(out["in_thread_any_side"], 451)
        # Tier A: users 0, 1, 2 (labels), 260 (known-bad file); Tier B: 250, 251
        self.assertEqual(out["tier_a_in_thread"], 4)
        self.assertEqual(out["tier_a_in_thread_with_history"], 3)
        self.assertEqual(out["tier_b_in_thread"], 2)
        self.assertEqual(out["inactive_unlabeled_in_thread"], 1)
        self.assertFalse(out["tier_a_testable"])
        p1 = out["p1"]
        self.assertEqual(p1["labeled"], {"progressive": 3, "government_right": 6})   # 0,1,2 | 0,1,2,250,251,260
        self.assertAlmostEqual(p1["share"]["progressive"], 3 / 201)                   # 0-9 are on both sides
        lo, hi = p1["share_ci95"]["progressive"]
        self.assertTrue(lo <= 3 / 201 <= hi)
        self.assertFalse(p1["direction_hit"])
        p2 = out["p2"]
        self.assertEqual(p2["2a"]["alarms"], 2)
        self.assertEqual(p2["2b"]["organic"], 1)
        self.assertAlmostEqual(p2["2c"]["labeled_share_alarm_hours"], 2 / 20)
        self.assertAlmostEqual(p2["2c"]["labeled_share_other_hours"], 2 / 40)
        self.assertFalse(p2["2c"]["hit"])
        self.assertTrue(out["p3"]["3a"]["hit"] and out["p3"]["3b"]["hit"])
        # thread size 20-500: tp[0] (200 replies) and tp[2] (110) and the big post (150) stay; user 900's reply is in
        # TGT[1]'s thread, which has 1 reply, so it drops
        self.assertEqual(out["p1_threads_20_to_500"]["repliers"], {"progressive": 200, "government_right": 260})
        self.assertEqual(out["p7"], {"tier_a_with_history": 3, "range_hit": False, "under_30": True})
        self.assertEqual(out["p5"]["matched"], 1)

    def test_window_refuses_early(self):
        old = sys.argv
        sys.argv = ["score_window.py", "--window"]
        try:
            with self.assertRaises(SystemExit) as e:
                sw.main()
            self.assertIn("7 days after", str(e.exception))
        finally:
            sys.argv = old


if __name__ == "__main__":
    unittest.main()
