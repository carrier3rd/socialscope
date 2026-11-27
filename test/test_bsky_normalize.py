"""Phase 2 normalize (bluesky/normalize/to_parquet.py) on a synthetic raw folder. No network, no real accounts."""
import gzip
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "bluesky", "normalize"))
sys.path.insert(0, os.path.join(REPO, "bluesky", "collect"))
sys.path.insert(0, os.path.join(REPO, "test"))
import make_fake_bsky as fk  # noqa: E402
import to_parquet as tp  # noqa: E402

try:
    import duckdb  # noqa: F401
    import pyarrow.parquet as pq
except ImportError:                       # the collectors' venv may not have the Phase 2 packages
    pq = None

HOUR = 3_600_000_000
CFG = {"sides": {"left": [{"did": fk.TARGET}], "right": [{"did": fk.TARGET2}]}}


def gz_lines(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for x in lines:
            f.write(x.rstrip("\n") + "\n")


def account(did, status, active, t):
    return json.dumps({"did": did, "time_us": t, "kind": "account",
                       "account": {"active": active, "did": did, "seq": 1, "status": status, "time": "x"}})


@unittest.skipIf(pq is None, "pyarrow/duckdb not installed")
class TestNormalize(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / "bluesky"
        self.raw = self.data / "raw"

    def tearDown(self):
        self.tmp.cleanup()

    def run_all(self, full=False):
        staged = tp.stage_all(self.data, full=full, log=lambda *a: None)
        return staged, tp.build_tables(self.data, CFG, log=lambda *a: None)

    def table(self, name):
        return pq.read_table(self.data / "processed" / "tables" / f"{name}.parquet").to_pylist()

    def write_fixture(self):
        tpost = fk.post_uri(fk.TARGET, "3kfaketgt2222")
        a, b, c, gone, sleepy = fk.did(1), fk.did(2), fk.did(3), fk.did(4), fk.did(5)
        reply = fk.post(a, t=fk.T0, reply_root=tpost, text="a reply")
        reply_other_host = reply.replace(f'"time_us": {fk.T0}', f'"time_us": {fk.T0 + 7}')
        h0 = [
            reply, reply,                                                    # replayed line, written twice
            reply_other_host,                                                # same event from the other host
            fk.commit(b, tp.POST, {"text": "deleted later", "createdAt": "2026-11-18T11:06:41Z"},
                      t=fk.T0 + 10, rkey="3kfakedel2222"),
            fk.delete(b, tp.POST, t=fk.T0 + 20, rkey="3kfakedel2222"),
            fk.commit(b, tp.POST, {"text": "gone then back", "createdAt": "2026-11-18T11:06:41Z"},
                      t=fk.T0 + 10, rkey="3kfakeback222"),
            fk.delete(b, tp.POST, t=fk.T0 + 20, rkey="3kfakeback222"),
            fk.commit(b, tp.POST, {"text": "gone then back", "createdAt": "2026-11-18T11:06:42Z"},
                      t=fk.T0 + 30, rkey="3kfakeback222"),
            fk.like(c, tpost, t=fk.T0 + 40, rkey="3kfakelikea22"),
            fk.like(c, tpost, t=fk.T0 + 41, rkey="3kfakelikeb22"),
            fk.delete(c, "app.bsky.feed.like", t=fk.T0 + 50, rkey="3kfakelikeb22"),   # an unlike
            fk.graph(c, "follow", fk.TARGET2, t=fk.T0 + 60),
            fk.post(gone, t=fk.T0 + 70, reply_root=fk.post_uri(fk.TARGET2, "3kfaketgt3333")),
            account(gone, "deleted", False, fk.T0 + 80),
            fk.post(sleepy, t=fk.T0 + 90, reply_root=fk.post_uri(fk.TARGET2, "3kfaketgt3333")),
            account(sleepy, "deactivated", False, fk.T0 + 95),
            "{not json",
        ]
        gz_lines(self.raw / "jetstream" / "2026-11-18T11.jsonl.gz", h0)
        (self.raw / "jetstream" / "2026-11-18T12.jsonl").write_text(          # the hour still being written
            fk.commit(a, tp.POST, {"text": "next hour", "createdAt": "2026-11-18T12:06:40Z"}, t=fk.T0 + HOUR,
                      rkey="3kfakenext222") + "\n")
        # a history repeats a's reply (now with a link facet) and adds an older post
        reply_uri = f"at://{a}/app.bsky.feed.post/3kfakerkey222"
        hist = [{"uri": reply_uri, "cid": "x",
                 "value": json.loads(reply)["commit"]["record"]},
                {"uri": f"at://{a}/app.bsky.feed.post/3kfakeold2222", "cid": "x",
                 "value": {"text": "old", "createdAt": "2026-10-01T00:00:00.123456789Z", "langs": ["en"],
                           "facets": [{"features": [{"$type": "app.bsky.richtext.facet#link",
                                                     "uri": "https://example.org"}]}]}}]
        gz_lines(self.raw / "histories" / a[-2:] / (a.replace(":", "_") + ".jsonl.gz"), [json.dumps(h) for h in hist])
        thread = {"thread": {"post": {"uri": tpost, "author": {"did": fk.TARGET}, "indexedAt": "2026-11-18T11:00:00Z",
                                      "record": {"text": "target", "createdAt": "2026-11-18T11:00:00Z"}},
                             "replies": [{"post": {"uri": reply_uri, "author": {"did": a},
                                                   "indexedAt": "2026-11-18T11:06:40.500Z",
                                                   "record": json.loads(reply)["commit"]["record"]}, "replies": []},
                                         {"$type": "app.bsky.feed.defs#notFoundPost", "uri": "at://x/y/z"}]}}
        t_dir = self.raw / "threads" / fk.TARGET.replace(":", "_")
        t_dir.mkdir(parents=True)
        with gzip.open(t_dir / "3kfaketgt2222.json.gz", "wt", encoding="utf-8") as f:
            json.dump(thread, f)
        gz_lines(self.raw / "profiles" / "part-0000.jsonl.gz", [
            json.dumps({"fetched": "2026-11-19T00:00:00Z", "profile": {"did": a, "handle": "old.bsky.social"}}),
            json.dumps({"fetched": "2026-11-20T00:00:00Z", "profile": {
                "did": a, "handle": "a.example.com", "displayName": "A", "createdAt": "2024-01-01T00:00:00Z",
                "labels": [{"src": a, "val": "!no-unauthenticated"}, {"src": "did:plc:other", "val": "spam"}]}})])
        plc_dir = self.raw / "plc" / a[-2:]
        plc_dir.mkdir(parents=True)
        (plc_dir / (a.replace(":", "_") + ".json")).write_text(json.dumps([
            {"did": a, "createdAt": "2024-01-01T00:00:00Z", "nullified": False,
             "operation": {"type": "plc_operation", "rotationKeys": ["k1"], "alsoKnownAs": ["at://old.bsky.social"],
                           "services": {"atproto_pds": {"endpoint": "https://pds-1.example"}}}},
            {"did": a, "createdAt": "2026-11-01T00:00:00Z", "nullified": False,
             "operation": {"type": "plc_operation", "rotationKeys": ["k2"], "alsoKnownAs": ["at://a.example.com"],
                           "services": {"atproto_pds": {"endpoint": "https://pds-2.example"}}}}]))
        lab = self.raw / "labels" / "fake_labeler" / "labels.jsonl.gz"
        gz_lines(lab, [json.dumps({"seq": 1, "src": "did:plc:lab", "uri": a, "val": "spam", "neg": False,
                                   "cts": "2026-11-01T00:00:00Z"}),
                       json.dumps({"seq": 2, "src": "did:plc:lab", "uri": a, "val": "spam", "neg": True,
                                   "cts": "2026-11-02T00:00:00Z"}),
                       json.dumps({"seq": 3, "src": "did:plc:lab", "uri": b, "val": "spam", "neg": False,
                                   "cts": "2026-11-02T00:00:00Z"})])
        return a, b, c, gone, sleepy

    def test_tables_dedupe_and_apply_deletes(self):
        a, b, c, gone, sleepy = self.write_fixture()
        staged, out = self.run_all()
        self.assertEqual(staged["jetstream"]["lines"], 17)
        self.assertEqual(staged["jetstream"]["duplicate_lines"], 1)
        self.assertEqual(staged["jetstream"]["bad_lines"], 1)
        posts = {p["uri"]: p for p in self.table("posts")}
        reply_uri = f"at://{a}/app.bsky.feed.post/3kfakerkey222"
        # one row for the reply, from three sources (the replay, the other host, the history and the thread)
        self.assertEqual(sorted(posts[reply_uri]["sources"]), ["history", "jetstream", "thread"])
        self.assertEqual(posts[reply_uri]["indexed_at"].microsecond, 500_000)           # the AppView's indexedAt
        self.assertIn(fk.post_uri(fk.TARGET, "3kfaketgt2222"), posts)                    # the thread's root post
        self.assertNotIn(f"at://{b}/app.bsky.feed.post/3kfakedel2222", posts)        # deleted
        back = posts[f"at://{b}/app.bsky.feed.post/3kfakeback222"]                    # deleted, then written again
        self.assertEqual(back["text"], "gone then back")
        self.assertFalse(any(p["did"] == gone for p in posts.values()))                 # deleted account
        self.assertTrue(any(p["did"] == sleepy for p in posts.values()))                # deactivated: kept
        old = posts[f"at://{a}/app.bsky.feed.post/3kfakeold2222"]
        self.assertEqual(old["facet_links"], ["https://example.org"])
        self.assertEqual((old["created_at"].month, old["created_at"].microsecond), (10, 123456))   # 9 digits parse
        inter = self.table("interactions")
        self.assertEqual(sorted((i["type"], i["uri"].rsplit("/", 1)[1]) for i in inter),
                         [("follow", "3kfakerkey222"), ("like", "3kfakelikea22")])        # the unliked one is gone
        accts = {x["did"]: x for x in self.table("accounts")}
        self.assertEqual(accts[a]["handle"], "a.example.com")                            # newest profile wins
        self.assertTrue(accts[a]["domain_handle"])
        self.assertEqual(accts[a]["pds_host"], "pds-2.example")
        self.assertEqual(accts[a]["self_labels"], ["!no-unauthenticated"])               # other labelers' are not self
        self.assertEqual(accts[a]["side_seen"], ["left"])
        self.assertEqual(accts[sleepy]["status"], "deactivated")
        self.assertEqual(accts[sleepy]["side_seen"], ["right"])
        self.assertNotIn(fk.TARGET, [d for d, x in accts.items() if x["side_seen"]])     # a target has no side here
        plc = self.table("plc_ops")
        self.assertEqual([p["rotation_keys_changed"] for p in plc], [False, True])
        labels = {(x["uri_or_did"], x["val"]): x for x in self.table("labels")}
        self.assertTrue(labels[(a, "spam")]["neg"])                                       # the newest event wins
        self.assertFalse(labels[(b, "spam")]["neg"])
        self.assertEqual(out["posts"], len(posts))
        self.assertEqual(out["in"]["deleted_accounts"], 1)

    def test_open_hour_is_skipped_and_reruns_only_stage_changes(self):
        self.write_fixture()
        first, _ = self.run_all()
        self.assertEqual(first["jetstream"]["lines"], 17)                  # the open 12:00 hour was not read
        again, _ = self.run_all()
        self.assertEqual(again, {})                                        # nothing changed: nothing staged
        open_hour = self.raw / "jetstream" / "2026-11-18T12.jsonl"
        gz_lines(open_hour.with_name(open_hour.name + ".gz"), open_hour.read_text().splitlines())
        open_hour.unlink()                                                 # the recorder closed the hour
        later, out = self.run_all()
        self.assertEqual(later["jetstream"]["lines"], 1)
        self.assertEqual(out["posts"], len(self.table("posts")))

    def test_time_parsing(self):
        self.assertEqual(tp._ts("1970-01-01T00:00:01Z"), 1_000_000)
        self.assertEqual(tp._ts("1970-01-01T00:00:01.5+00:00"), 1_500_000)
        self.assertEqual(tp._ts("1970-01-01T00:00:01.123456789Z"), 1_123_456)
        self.assertIsNone(tp._ts("yesterday"))
        self.assertIsNone(tp._ts(None))


if __name__ == "__main__":
    unittest.main()
