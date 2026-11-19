"""Bluesky collectors on synthetic fixtures (test/make_fake_bsky.py). No network, no real accounts."""
import gzip
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path

from bluesky.collect import appview, backlinks, jetstream, labels, pilot_check, plc
import bsky_common as bc  # the collectors put bluesky/collect on sys.path

from test import make_fake_bsky as fk

try:
    import cbor2  # noqa: F401
    HAVE_CBOR = True
except ImportError:
    HAVE_CBOR = False


class Clock:
    def __init__(self, t=1_795_000_000.0):
        self.t = t

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def opener(script, seen=None):
    """urlopen stand-in: `script` is a list of status codes or JSON bodies, used in order."""
    it = iter(script)

    def op(req, timeout=None):
        if seen is not None:
            seen.append(req.full_url)
        x = next(it)
        if isinstance(x, int):
            raise urllib.error.HTTPError(req.full_url, x, "err", {}, None)
        return FakeResp(json.dumps(x).encode())
    return op


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.cfg = bc.load_config()

    def test_targets_are_dids_and_no_account_is_on_two_sides(self):
        rows = [(s, t) for s, ts in self.cfg["sides"].items() for t in ts]
        dids = [t["did"] for _, t in rows]
        self.assertTrue(all(d.startswith("did:plc:") and len(d) == 32 for d in dids))
        self.assertEqual(len(dids), len(set(dids)))
        self.assertEqual(set(self.cfg["sides"]), {"progressive", "government_right"})
        self.assertEqual(len(bc.targets(self.cfg)), len(dids))

    def test_label_whitelists_hold_no_political_values(self):
        political = {"maga-trump", "hammer-sickle", "terf-gc", "alt-gov", "elon-musk", "fringe-media",
                     "blue-heart-emoji", "inverted-red-triangle", "nazi-symbolism", "tankie", "troll",
                     "us-gov-account", "alt-tech", "intolerance"}
        for name, lab in self.cfg["calibration"]["labelers"].items():
            for v in political:
                self.assertFalse(labels.keep(v, lab["keep_vals"], lab.get("keep_prefixes", ())), (name, v))
        sky = self.cfg["calibration"]["labelers"]["skywatch"]
        self.assertTrue(labels.keep("follow-farming", sky["keep_vals"], sky["keep_prefixes"]))
        self.assertTrue(labels.keep("repetitive-domain-spam-x.example", sky["keep_vals"], sky["keep_prefixes"]))

    def test_window_is_unset_until_the_pilot_passes(self):
        self.assertIsNone(self.cfg["window"]["start"])
        self.assertEqual(self.cfg["window"]["days"], 21)


class TestTid(unittest.TestCase):
    def test_known_value_and_round_trip(self):
        us = bc.iso_to_us("2025-01-01")
        self.assertEqual(bc.tid_from_us(us), "3lenax2ss2222")   # matched a live listRecords page, Nov 19 2026
        self.assertEqual(bc.tid_to_us(bc.tid_from_us(us)), us)
        self.assertIsNone(bc.tid_to_us("self"))
        self.assertLess(bc.tid_from_us(us - 1), bc.tid_from_us(us))   # keys sort by time

    def test_did_of(self):
        self.assertEqual(bc.did_of(fk.post_uri(fk.TARGET)), fk.TARGET)
        self.assertEqual(bc.did_of(fk.TARGET), fk.TARGET)
        self.assertIsNone(bc.did_of(None))


class TestRecorder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.clock = Clock()

    def tearDown(self):
        self.tmp.cleanup()

    def rec(self, **kw):
        return jetstream.Recorder(self.root / "raw", self.root / "state", self.root / "status",
                                  [fk.TARGET, fk.TARGET2], clock=self.clock, **kw)

    def lines(self):
        out = []
        for p in sorted((self.root / "raw").glob("20*")):
            op = gzip.open if p.suffix == ".gz" else open
            with op(p, "rt") as f:
                out += [json.loads(x) for x in f]
        return out

    def test_what_is_kept(self):
        r = self.rec()
        tp = fk.post_uri(fk.TARGET)
        replier, liker, stranger, blocker = fk.did(1), fk.did(2), fk.did(3), fk.did(4)
        cases = [
            (fk.post(stranger), None),                                  # unrelated post
            (fk.post(replier, reply_root=tp), "reply_to_target"),
            (fk.post(replier), "author"),                               # replier's later, unrelated post
            (fk.like(liker, tp), "points_at_target"),
            (fk.like(stranger, fk.post_uri(replier)), "points_at_replier"),
            (fk.like(fk.did(5), fk.post_uri(fk.did(6))), None),
            (fk.post(fk.did(7), quote=tp), "points_at_target"),
            (fk.graph(blocker, "block", fk.TARGET), "points_at_target"),
            (fk.graph(fk.did(8), "follow", fk.did(9)), None),
            (fk.graph(fk.did(8), "listitem", replier), "points_at_replier"),
            (fk.post(fk.TARGET, reply_root=tp), "author"),              # a target replying in its own thread
            (fk.delete(liker, "app.bsky.feed.like"), "delete"),         # unlike by someone we kept a record from
            (fk.delete(fk.did(5), "app.bsky.feed.like"), None),
            (fk.identity(replier), "identity"),
            (fk.identity(fk.did(5)), None),
        ]
        for raw, want in cases:
            self.assertEqual(r.decide(json.loads(raw)), want, raw[:120])
        self.assertEqual(r.repliers, {replier})
        self.assertNotIn(fk.TARGET, r.repliers)
        self.assertIn(liker, r.seen)
        self.assertNotIn(replier, r.seen)
        r.close()

    def test_reply_to_a_reply_in_a_target_thread_counts(self):
        r = self.rec()
        raw = fk.post(fk.did(1), reply_root=fk.post_uri(fk.TARGET), reply_parent=fk.post_uri(fk.did(2)))
        self.assertEqual(r.decide(json.loads(raw)), "reply_to_target")
        r.close()

    def test_replier_cap(self):
        r = self.rec(max_repliers=1)
        for i in (1, 2):
            r.handle(fk.post(fk.did(i), reply_root=fk.post_uri(fk.TARGET)))
        self.assertEqual(len(r.repliers), 1)
        self.assertEqual(r.counts["replier_cap_hits"], 1)
        self.assertEqual(len(self.lines()), 2)       # the reply itself is still kept
        r.close()

    def test_hour_files_cursor_and_resume(self):
        r = self.rec()
        tp = fk.post_uri(fk.TARGET)
        hour = 3_600_000_000
        r.open_session("host-a")
        r.handle(fk.like(fk.did(1), tp, t=fk.T0))
        r.handle("{cut off")                                   # bad line from the wire is counted, not fatal
        r.handle(fk.like(fk.did(2), tp, t=fk.T0 + hour))       # next hour: the first file is compressed
        self.clock.t += 61
        r.handle(fk.post(fk.did(3), t=fk.T0 + hour + 5))       # not kept, but moves the cursor
        self.assertEqual(r.counts["bad_json"], 1)
        files = sorted(p.name for p in (self.root / "raw").glob("20*"))
        self.assertEqual(len(files), 2)
        self.assertTrue(files[0].endswith(".jsonl.gz") and files[1].endswith(".jsonl"))
        saved = json.load(open(self.root / "state" / "cursor.json"))
        self.assertEqual(saved["time_us"], fk.T0 + hour + 5)
        # killed here: no close_session, no close. A new process picks up from the files.
        r2 = self.rec()
        self.assertEqual(r2.resume_cursor(), fk.T0 + hour + 5 - jetstream.REWIND_US)
        self.assertEqual(r2.seen, {fk.did(1), fk.did(2)})
        r2.open_session("host-b")
        r2.handle(fk.like(fk.did(2), tp, t=fk.T0 + hour))      # replayed duplicate lands in the same hour
        r2.handle(fk.delete(fk.did(1), "app.bsky.feed.like", t=fk.T0 + hour + 9))
        r2.close_session("closed")
        sess = [json.loads(x) for x in open(self.root / "raw" / "sessions.jsonl")]
        self.assertEqual(len(sess), 1)                         # the killed session left no line
        self.assertEqual(sess[0]["host"], "host-b")
        self.assertEqual(sess[0]["resume_gap_s"], round((fk.T0 + hour - sess[0]["cursor"]) / 1e6, 1))
        self.assertEqual(len(self.lines()), 4)
        self.assertIn("&cursor=", jetstream.stream_url("h", ["a.b"], r2.resume_cursor()))
        self.assertNotIn("cursor", jetstream.stream_url("h", ["a.b"], None))
        r2.close()

    def test_old_cursor_is_flagged(self):
        r = self.rec()
        r.cursor = int((self.clock.t - 40 * 3600) * 1e6)
        r.open_session("h")
        self.assertIn("gap_possible", r.session)
        r.close()

    def test_status_has_counts_and_no_ids(self):
        r = self.rec()
        r.open_session("h")
        r.handle(fk.post(fk.did(1), reply_root=fk.post_uri(fk.TARGET)))
        r.close_session("closed")
        text = (self.root / "status" / "status.json").read_text()
        st = json.loads(text)
        self.assertEqual(st["repliers"], 1)
        self.assertEqual(st["counts_since_start"]["kept:app.bsky.feed.post"], 1)
        self.assertNotIn("did:", text)
        self.assertNotIn("synthetic", text)       # no post text
        self.assertNotIn("did:", (self.root / "raw" / "sessions.jsonl").read_text())
        r.close()


class TestHttp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.clock = Clock()

    def tearDown(self):
        self.tmp.cleanup()

    def http(self, script, seen=None, **kw):
        return bc.Http("appview", "https://example.invalid", 4.0, "ua", self.tmp.name,
                       opener=opener(script, seen), sleep=self.clock.sleep, clock=self.clock, **kw)

    def test_backs_off_on_429_and_logs_counts_without_urls(self):
        seen = []
        h = self.http([429, 503, {"ok": 1}], seen)
        t0 = self.clock.t
        self.assertEqual(h.get("xrpc/x", {"actor": "did:plc:fakeuser"}), {"ok": 1})
        self.assertGreaterEqual(self.clock.t - t0, 6)        # 2 s, then 4 s
        self.assertEqual(h.total, {"429": 1, "503": 1, "200": 1})
        h.flush()
        log = (Path(self.tmp.name) / "requests_appview.jsonl").read_text()
        self.assertEqual(sum(json.loads(x)["codes"].get("429", 0) for x in log.splitlines()), 1)
        self.assertNotIn("did:", log)
        self.assertIn("actor=did", seen[0])

    def test_gives_up_and_missing(self):
        with self.assertRaises(bc.Throttled):
            self.http([429] * 3, retries=2).get("x")
        self.assertIsNone(self.http([400]).get("x", ok_missing=True))
        with self.assertRaises(urllib.error.HTTPError):
            self.http([400]).get("x")

    def test_rate_gap(self):
        h = self.http([{}, {}])
        t0 = self.clock.t
        h.get("x")
        h.get("x")
        self.assertAlmostEqual(self.clock.t - t0, 0.25)


@unittest.skipUnless(HAVE_CBOR, "cbor2 not installed")
class TestLabels(unittest.TestCase):
    def test_whitelist_counts_negation_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            sink = labels.LabelSink(tmp, ["spam", "follow-farming"], ["repetitive-domain-spam-"])
            a, b = fk.did(1), fk.did(2)
            self.assertTrue(sink.frame(fk.label_frame(1, [fk.label(a, "follow-farming"), fk.label(a, "maga-trump")])))
            self.assertTrue(sink.frame(fk.label_frame(2, [fk.label(b, "spam", cts="2026-07-01T00:00:00Z"),
                                                          fk.label(a, "follow-farming", neg=True)])))
            self.assertTrue(sink.frame(fk.label_frame(3, [], t="#info")))
            self.assertFalse(sink.frame(fk.label_frame(0, [], op=-1)))
            sink.close()
            rows = [json.loads(x) for x in gzip.open(Path(tmp) / "labels.jsonl.gz", "rt")]
            self.assertEqual([(r["val"], r["neg"]) for r in rows],
                             [("follow-farming", False), ("spam", False), ("follow-farming", True)])
            self.assertTrue(all("sig" not in r for r in rows))
            raw = gzip.open(Path(tmp) / "labels.jsonl.gz", "rt").read()
            self.assertNotIn("maga-trump", raw)                       # the political value never reaches disk
            counts = json.load(open(Path(tmp) / "counts.json"))
            self.assertEqual(counts["maga-trump"], {"2026-06": 1})    # but its volume is counted
            self.assertEqual(counts["neg:follow-farming"], {"2026-06": 1})
            self.assertEqual(labels.LabelSink(tmp, [], []).seq, 2)    # next run resumes after seq 2


class TestAppview(unittest.TestCase):
    def test_thread_repliers(self):
        t = fk.thread(fk.TARGET, [(fk.did(1), fk.did(2)), (fk.did(3), fk.did(1))])
        self.assertEqual(appview.thread_repliers(t["thread"]), {fk.did(1), fk.did(2), fk.did(3)})

    def test_should_fetch(self):
        now = bc.iso_to_us("2026-11-20T12:00:00+00:00")
        self.assertTrue(appview.should_fetch(None, 0, now))
        self.assertFalse(appview.should_fetch({"final": True, "fetched": "2026-11-01T00:00:00+00:00"}, 0, now))
        self.assertFalse(appview.should_fetch({"final": False, "fetched": "2026-11-20T08:00:00+00:00"}, 0, now))
        self.assertTrue(appview.should_fetch({"final": False, "fetched": "2026-11-20T05:00:00+00:00"}, 0, now))

    def test_target_posts_stop_at_since_and_skip_reposts(self):
        def item(author, created, repost=False):
            it = {"post": {"uri": fk.post_uri(author, created[:10]), "author": {"did": author},
                           "record": {"createdAt": created}, "replyCount": 3}}
            if repost:
                it["reason"] = {"$type": "app.bsky.feed.defs#reasonRepost"}
            return it
        page = {"cursor": "c", "feed": [item(fk.TARGET, "2026-11-20T10:00:00Z"),
                                        item(fk.did(1), "2026-11-20T09:00:00Z", repost=True),
                                        item(fk.TARGET, "2026-11-10T00:00:00Z")]}
        clock = Clock()
        h = bc.Http("appview", "https://example.invalid", 0, "ua", opener=opener([page]), sleep=clock.sleep,
                    clock=clock)
        got = appview.target_posts(h, fk.TARGET, bc.iso_to_us("2026-11-19"))
        self.assertEqual([g["uri"] for g in got], [fk.post_uri(fk.TARGET, "2026-11-20")])

    def _pds(self, pages, seen):
        clock = Clock()
        return bc.Http("pds", "https://pds.invalid", 0, "ua", opener=opener(pages, seen), sleep=clock.sleep,
                       clock=clock)

    def test_history_starts_at_the_anchor_and_caps_each_kind(self):
        anchor = bc.iso_to_us("2026-06-01")

        def rec(i, reply):
            v = {"text": "synthetic", "createdAt": "2026-05-01T00:00:00Z"}
            if reply:
                v["reply"] = {"root": {"uri": "at://x/y/z"}, "parent": {"uri": "at://x/y/z"}}
            return {"uri": fk.post_uri(fk.did(1), bc.tid_from_us(anchor - i * 1000)), "value": v}
        p1 = {"cursor": "next1", "records": [rec(i, reply=True) for i in range(1, 6)]}
        p2 = {"cursor": "next2", "records": [rec(i, reply=False) for i in range(6, 9)] + [rec(9, True)]}
        seen = []
        recs, s = appview.history(self._pds([p1, p2], seen), fk.did(1), anchor, cap_posts=2, cap_replies=3)
        self.assertIn("cursor=" + bc.tid_from_us(anchor + 1), seen[0])   # the pull starts at the anchor
        self.assertIn("cursor=next1", seen[1])
        self.assertEqual((s["posts"], s["replies"], s["ended"], s["pages"]), (2, 3, "both caps full", 2))
        self.assertEqual(len(recs), 5)
        self.assertTrue(all(bc.tid_to_us(r["uri"].rsplit("/", 1)[1]) <= anchor for r in recs))

    def test_history_of_a_gone_account_and_a_short_one(self):
        recs, s = appview.history(self._pds([400], []), fk.did(1), 1, 10, 10)
        self.assertEqual((recs, s["gone"]), ([], True))
        recs, s = appview.history(self._pds([{"records": [{"uri": fk.post_uri(fk.did(1), "self"), "value": {}}]}],
                                            []), fk.did(1), 1, 10, 10)
        self.assertEqual((len(recs), s["ended"], s["non_tid_keys"]), (1, "exhausted", 1))

    def test_profiles_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            clock = Clock()
            dids = [fk.did(i) for i in range(30)]
            pages = [{"profiles": [{"did": d} for d in dids[:24]]}, {"profiles": [{"did": d} for d in dids[25:]]}]
            h = bc.Http("appview", "https://example.invalid", 0, "ua", opener=opener(pages), sleep=clock.sleep,
                        clock=clock)
            n = appview.profiles(h, tmp, dids)
            self.assertEqual((n["asked"], n["returned"]), (30, 29))    # one account was not returned
            h2 = bc.Http("appview", "https://example.invalid", 0, "ua", opener=opener([]), sleep=clock.sleep,
                         clock=clock)
            self.assertEqual(appview.profiles(h2, tmp, dids)["asked"], 0)  # nothing left; no request made


class TestPlcAndBacklinks(unittest.TestCase):
    def test_pds_of_takes_the_newest_standing_operation(self):
        log = [{"operation": {"services": {"atproto_pds": {"endpoint": "https://old.invalid"}}}},
               {"operation": {"services": {"atproto_pds": {"endpoint": "https://new.invalid/"}}}},
               {"nullified": True, "operation": {"services": {"atproto_pds": {"endpoint": "https://bad.invalid"}}}}]
        self.assertEqual(plc.pds_of(log), "https://new.invalid")
        self.assertIsNone(plc.pds_of([]))

    def test_plc_audit_is_cached_forever(self):
        with tempfile.TemporaryDirectory() as tmp:
            clock = Clock()
            h = bc.Http("plc", "https://plc.invalid", 0, "ua", opener=opener([[{"operation": {}}]]),
                        sleep=clock.sleep, clock=clock)
            self.assertEqual(len(plc.audit(h, tmp, fk.did(1))), 1)
            self.assertEqual(len(plc.audit(h, tmp, fk.did(1))), 1)     # second call: the script is empty
            self.assertIsNone(plc.audit(h, tmp, "did:web:example.invalid"))

    def test_constellation_caches_and_survives_an_outage(self):
        with tempfile.TemporaryDirectory() as tmp:
            clock = Clock()
            pages = [{"total": 3, "records": [{"n": 1}, {"n": 2}], "cursor": "c2"},
                     {"total": 3, "records": [{"n": 3}], "cursor": None}]
            h = bc.Http("constellation", "https://c.invalid", 0, "ua", opener=opener(pages), sleep=clock.sleep,
                        clock=clock)
            con = backlinks.Constellation(h, tmp)
            uri = fk.post_uri(fk.TARGET)
            self.assertEqual(len(con.records(uri, "likes")), 3)
            self.assertEqual(len(con.records(uri, "likes")), 3)        # from the cache; no request left to give
            self.assertEqual((con.misses, con.hits), (2, 2))
            down = bc.Http("constellation", "https://c.invalid", 0, "ua", opener=opener([500] * 9), retries=1,
                           sleep=clock.sleep, clock=clock)
            con2 = backlinks.Constellation(down, tmp)
            self.assertIsNone(con2.records(uri, "reposts"))            # caller falls back to Jetstream counts
            self.assertIsNone(con2.count(uri, "likes"))


class TestPilotCheck(unittest.TestCase):
    def test_longest_429_run(self):
        rows = [{"minute": m * 60, "codes": c} for m, c in
                [(10, {"200": 5}), (11, {"429": 1}), (12, {"429": 2, "200": 1}), (14, {"429": 1})]]
        run, total = pilot_check.longest_429_run(rows)
        self.assertEqual(run, 2)
        self.assertEqual(total, {"200": 6, "429": 4})

    def test_session_checks(self):
        s = pilot_check.session_checks([
            {"reason": "time limit", "events": 10, "kept": 2},
            {"reason": "closed", "cursor": 5, "resume_gap_s": 0.4, "events": 5, "kept": 1}])
        self.assertEqual((s["sessions"], s["resumed_sessions"], s["largest_resume_gap_s"], s["kept"]),
                         (2, 1, 0.4, 3))


if __name__ == "__main__":
    unittest.main()
