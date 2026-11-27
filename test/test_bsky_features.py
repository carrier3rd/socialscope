"""Phase 3 features (bluesky/features/bsky_only.py) on synthetic tables. No network, no real accounts.
The leakage test is the spec's Phase 3 acceptance check: no feature uses activity after the anchor."""
import datetime as dt
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "bluesky", "features"))
import bsky_only as bo  # noqa: E402

try:
    import duckdb  # noqa: F401
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:
    pa = None

DAY = 86_400_000_000
MIN = 60_000_000
T0 = 1_790_000_000_000_000          # 2026-09-21
TGT, A, B, C = ("did:plc:faketarget0000000000000a", "did:plc:fakeuser000000000000000a",
                "did:plc:fakeuser000000000000000b", "did:plc:fakeuser000000000000000c")
ANCHOR = T0 + 300 * DAY


def ts(us):
    # a plain datetime in UTC: pyarrow's own tz-aware scalars need the tzdata package on Windows
    return dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(microseconds=us)


def post(did, rkey, t, parent=None, links=(), indexed=None, src="jetstream"):
    return {"uri": f"at://{did}/app.bsky.feed.post/{rkey}", "did": did, "rkey": rkey, "created_at": ts(t),
            "indexed_at": ts(indexed) if indexed else None, "text": "x", "langs": ["en"], "reply_parent": parent,
            "reply_root": parent, "quote_uri": None, "embed_type": None, "facet_links": list(links),
            "facet_mentions": [], "sources": [src]}


def inter(kind, actor, subject, t, rkey):
    return {"type": kind, "uri": f"at://{actor}/x/{rkey}", "actor_did": actor, "subject": subject,
            "list_uri": None, "created_at": ts(t), "rkey_time": ts(t), "time_us": t}


@unittest.skipIf(pa is None, "pyarrow/duckdb not installed")
class TestFeatures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / "bluesky"
        (self.data / "processed" / "tables").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, posts, inters):
        tdir = self.data / "processed" / "tables"
        L = pa.list_(pa.string())
        TS = pa.timestamp("us", tz="UTC")
        pq.write_table(pa.Table.from_pylist(posts, schema=pa.schema([
            ("uri", pa.string()), ("did", pa.string()), ("rkey", pa.string()), ("created_at", TS),
            ("indexed_at", TS), ("text", pa.string()), ("langs", L), ("reply_parent", pa.string()),
            ("reply_root", pa.string()), ("quote_uri", pa.string()), ("embed_type", pa.string()),
            ("facet_links", L), ("facet_mentions", L), ("sources", L)])), tdir / "posts.parquet")
        pq.write_table(pa.Table.from_pylist(inters, schema=pa.schema([
            ("type", pa.string()), ("uri", pa.string()), ("actor_did", pa.string()), ("subject", pa.string()),
            ("list_uri", pa.string()), ("created_at", TS), ("rkey_time", TS), ("time_us", pa.int64())])),
            tdir / "interactions.parquet")
        plc = [{"did": B, "op_type": "plc_operation", "handle": "b.bsky.social", "pds": "https://pds.example",
                "rotation_keys_changed": False, "created_at": ts(T0 - 400 * DAY), "nullified": False},
               {"did": B, "op_type": "plc_operation", "handle": "b-new.example", "pds": "https://pds.example",
                "rotation_keys_changed": False, "created_at": ts(T0 + 190 * DAY), "nullified": False},
               {"did": B, "op_type": "plc_operation", "handle": "b-later.example", "pds": "https://other.example",
                "rotation_keys_changed": True, "created_at": ts(ANCHOR + DAY), "nullified": False}]   # after anchor
        pq.write_table(pa.Table.from_pylist(plc, schema=pa.schema([
            ("did", pa.string()), ("op_type", pa.string()), ("handle", pa.string()), ("pds", pa.string()),
            ("rotation_keys_changed", pa.bool_()), ("created_at", TS), ("nullified", pa.bool_())])),
            tdir / "plc_ops.parquet")
        accts = [{"did": A, "pds_host": "shimeji.us-east.host.bsky.network"}, {"did": B, "pds_host": "pds.example"},
                 {"did": C, "pds_host": "shimeji.us-east.host.bsky.network"}]
        pq.write_table(pa.Table.from_pylist(accts), tdir / "accounts.parquet")

    def fixture(self):
        tgt = f"at://{TGT}/app.bsky.feed.post/3kfaketgt2222"
        posts = [post(TGT, "3kfaketgt2222", T0),
                 post(A, "3kfakea000001", T0 + 5 * MIN, parent=tgt, indexed=T0 + 5 * MIN + 2_000_000),
                 post(A, "3kfakea000002", T0 + 30 * MIN, parent=tgt, links=["https://x.com/someone/status/1"],
                      indexed=T0 + 30 * MIN + 2 * 3_600_000_000),
                 post(A, "3kfakea000003", T0 + DAY, links=["https://example.org"]),
                 post(B, "3kfakeb000001", T0),                                  # then 200 days of silence
                 post(B, "3kfakeb000002", T0 + 200 * DAY)]
        inters = [inter("block", TGT, A, T0 + 10 * DAY, "3kfakeblk0001")]
        inters += [inter("follow", C, f"did:plc:f{i}", T0 + i * MIN, f"3kfakef{i:06d}") for i in range(12)]
        inters += [inter("like", C, tgt, T0 + DAY, "3kfakelk00001")]
        return posts, inters

    def run_features(self):
        return {f["did"]: f for f in [r for r in self._build()]}

    def _build(self):
        bo.build(self.data, {}, {A: ANCHOR, B: ANCHOR, C: ANCHOR}, out_name="t", log=lambda *a: None)
        return pq.read_table(self.data / "processed" / "features" / "t.parquet").to_pylist()

    def test_features(self):
        self.write(*self.fixture())
        f = self.run_features()
        a, b, c = f[A], f[B], f[C]
        self.assertEqual((a["n_items"], a["n_top"], a["n_replies"]), (3, 1, 2))
        self.assertAlmostEqual(a["median_reply_minutes"], 17.5)                  # 5 and 30 minutes
        self.assertAlmostEqual(a["share_replies_under_10min"], 0.5)
        self.assertAlmostEqual(a["reddit_x_link_share"], 1 / 3)
        self.assertAlmostEqual(a["share_skew_over_1h"], 0.5)                    # one reply indexed 2 h late
        self.assertEqual(a["blocks_received"], 1)
        self.assertFalse(a["reply_only"])
        self.assertFalse(a["self_hosted_pds"])
        self.assertTrue(b["dormant_180"])
        self.assertTrue(b["change_before_resume"])                              # handle change 10 days before
        self.assertEqual((b["handle_changes"], b["pds_migrations"], b["key_rotations"]), (1, 0, 0))
        self.assertTrue(b["self_hosted_pds"])
        self.assertAlmostEqual(b["account_age_days"], 700)
        self.assertEqual((c["follows_given"], c["max_follows_per_hour"], c["likes_given"]), (12, 12, 1))
        self.assertAlmostEqual(c["share_follows_in_bursts"], 1.0)
        self.assertTrue(c["likes_with_zero_posts"])
        self.assertEqual(c["pds_accounts"], 2)

    def test_nothing_after_the_anchor_changes_a_feature(self):
        posts, inters = self.fixture()
        self.write(posts, inters)
        before = self.run_features()
        # after the anchor: a burst of replies, an unlike-able like, follows, blocks received, a takedown-era post
        later = ANCHOR + DAY
        posts2 = posts + [post(A, f"3kfakeaz{i:05d}", later + i * MIN, parent=posts[0]["uri"]) for i in range(50)]
        posts2 += [post(C, "3kfakec000009", later)]
        inters2 = inters + [inter("block", TGT, A, later, "3kfakeblk0002"), inter("like", A, posts[0]["uri"], later, "3kfakelkz0001")]
        inters2 += [inter("follow", B, f"did:plc:g{i}", later + i * MIN, f"3kfakeg{i:06d}") for i in range(30)]
        self.write(posts2, inters2)
        after = self.run_features()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
