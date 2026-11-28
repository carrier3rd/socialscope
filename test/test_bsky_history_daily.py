"""Daily history pull (bluesky/collect/history_daily.py): caps, resume and dedupe, on a fake PDS. No network."""
import copy
import gzip
import io
import json
import tempfile
import unittest
import urllib.error
import urllib.parse
from pathlib import Path

from bluesky.collect import history_daily as hd
import bsky_common as bc  # the collectors put bluesky/collect on sys.path

T0 = bc.iso_to_us("2026-11-28T12:00:00Z")
DAY = 86_400_000_000
TARGET = "did:plc:" + "t" * 24


def did(i):
    return f"did:plc:{i:024d}"


class Clock:
    def __init__(self, us=T0):
        self.t = us / 1e6

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeNet:
    """PLC + one PDS. repos: {did: [records newest first]}; dup: DIDs whose first page repeats a record."""

    def __init__(self, repos, gone=(), fail=None, dup=()):
        self.repos, self.gone, self.fail, self.dup = repos, set(gone), fail, set(dup)
        self.calls = []

    def __call__(self, req, timeout=None):
        u = urllib.parse.urlparse(req.full_url)
        self.calls.append(u.path)
        if self.fail:
            raise urllib.error.HTTPError(req.full_url, self.fail, "err", {}, None)
        if u.path.endswith("/log/audit"):
            body = [{"operation": {"services": {"atproto_pds": {"endpoint": "https://pds.example"}}}}]
        else:
            q = dict(urllib.parse.parse_qsl(u.query))
            if q["repo"] in self.gone:
                raise urllib.error.HTTPError(req.full_url, 400, "gone", {}, None)
            recs = [r for r in self.repos.get(q["repo"], []) if r["uri"].rsplit("/", 1)[1] < q["cursor"]]
            page = recs[:100]
            if q["repo"] in self.dup and page:
                page = page + [page[0]]
            body = {"records": page}
            if len(recs) > 100:
                body["cursor"] = page[99]["uri"].rsplit("/", 1)[1]
        return FakeResp(json.dumps(body).encode())


def records(d, n, newest_us, step_us=3600_000_000):
    out = []
    for k in range(n):
        t = newest_us - k * step_us
        out.append({"uri": f"at://{d}/app.bsky.feed.post/{bc.tid_from_us(t)}",
                    "value": {"text": "x", "createdAt": hd._iso(t), **({"reply": {}} if k % 2 else {})}})
    return out


def jet_line(author, t_us, root_did=TARGET):
    rec = {"text": "r", "createdAt": hd._iso(t_us),
           "reply": {"root": {"uri": f"at://{root_did}/app.bsky.feed.post/3aaa"},
                     "parent": {"uri": f"at://{root_did}/app.bsky.feed.post/3aaa"}}}
    return json.dumps({"did": author, "time_us": t_us, "kind": "commit",
                       "commit": {"collection": "app.bsky.feed.post", "operation": "create", "rkey": "x",
                                  "record": rec}})


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / "bluesky"
        self.status = Path(self.tmp.name) / "bluesky_status"
        self.cfg = copy.deepcopy(bc.load_config())
        self.cfg["sides"] = {"progressive": [{"handle": "t.example", "did": TARGET}], "government_right": []}
        self.cfg["history_daily"] = {"accounts_per_run": 500, "requests_per_run": 20000, "repull_after_days": 14,
                                     "min_gap_s": 0.0, "stop_after_throttled": 3, "max_pages": 60,
                                     "max_minutes": 165}
        self.jet = self.data / "raw" / "jetstream"
        self.jet.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def hour(self, name, lines):
        with gzip.open(self.jet / f"{name}.jsonl.gz", "wt", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def run_once(self, net, clock=None, **kw):
        clock = clock or Clock()
        st = hd.run(self.cfg, self.data, self.status, opener=net, sleep=clock.sleep, clock=clock, log=lambda *a: 0,
                    **kw)
        hd.write_status(self.status, st)
        return st

    def ledger(self):
        p = self.data / "state" / "history_daily" / "pulls.jsonl"
        if not p.exists():
            return []
        with open(p, encoding="utf-8") as f:
            return [json.loads(x) for x in f]


class TestQueue(Base):
    def test_only_window_replies_to_target_threads_and_each_hour_once(self):
        w0 = bc.iso_to_us("2026-11-27T00:00:00Z")
        self.hour("2026-11-27T05", [jet_line(did(1), w0 + 5 * 3_600_000_000), jet_line(did(1), w0 + 5 * 3_600_000_000 + 1),
                                    jet_line(did(2), w0 + 5 * 3_600_000_000, root_did=did(9)),   # not a target thread
                                    jet_line(TARGET, w0 + 5 * 3_600_000_000)])                  # a target itself
        self.hour("2026-11-26T05", [jet_line(did(3), w0 - 19 * 3_600_000_000)])               # before the window
        (self.jet / "2026-11-27T06.jsonl").write_text(jet_line(did(4), w0 + 6 * 3_600_000_000) + "\n")  # open hour
        st = self.run_once(FakeNet({}), plan_only=True)
        self.assertEqual(st["queue_before"]["window_repliers"], 1)
        self.assertEqual(st["scan"]["replies"], 2)
        self.run_once(FakeNet({}))                        # saves the queue state
        st = self.run_once(FakeNet({}))
        self.assertEqual(st["scan"]["hours_read"], 0)     # nothing read twice
        q = bc.load_json(self.data / "state" / "history_daily" / "window_repliers.json", {})
        self.assertEqual(q["repliers"][did(1)][0], 2)

    def test_plan_order_and_skip(self):
        reps = {did(1): [1, 5], did(2): [9, 7], did(3): [9, 3], did(4): [1, 1], did(5): [1, 1]}
        last = {did(4): T0 - 20 * DAY, did(5): T0 - 2 * DAY}
        order, n = hd.plan(reps, last, T0, 14, 0)
        self.assertEqual(order, [did(3), did(2), did(1), did(4)])   # never pulled (most replies first), then due
        self.assertEqual(n, {"window_repliers": 5, "never_pulled": 3, "due_for_repull": 1, "pulled_recently": 1})
        self.assertEqual(hd.plan(reps, last, T0, 14, 2)[0], [did(3), did(2)])


class TestCaps(Base):
    def setUp(self):
        super().setUp()
        w0 = bc.iso_to_us("2026-11-27T00:00:00Z")
        self.hour("2026-11-27T05", [jet_line(did(i), w0 + 5 * 3_600_000_000 + i) for i in range(1, 11)])
        self.repos = {did(i): records(did(i), 30, T0 - DAY) for i in range(1, 11)}

    def test_account_cap(self):
        self.cfg["history_daily"]["accounts_per_run"] = 4
        st = self.run_once(FakeNet(self.repos))
        self.assertEqual(st["result"]["pulled_first"], 4)
        self.assertEqual(st["ended"], "account cap")
        self.assertEqual(len(self.ledger()), 4)
        self.assertEqual(st["queue_after"]["never_pulled"], 6)

    def test_request_cap_counts_every_attempt_and_never_starts_an_account_it_cannot_finish(self):
        # each account: 1 PLC + 1 page = 2 requests; worst case allowed for = max_pages + 1 = 3
        self.cfg["history_daily"].update(requests_per_run=8, max_pages=2)
        net = FakeNet(self.repos)
        st = self.run_once(net)
        self.assertLessEqual(len(net.calls), 8)
        self.assertEqual(st["requests_used"], len(net.calls))
        self.assertEqual(st["ended"], "request cap")
        self.assertEqual(st["result"]["pulled_first"], 3)          # 6 used, 2 left < 3 worst case

    def test_time_cap(self):
        self.cfg["history_daily"].update(min_gap_s=60.0, max_minutes=3)    # 2 requests a minute on the fake clock
        st = self.run_once(FakeNet(self.repos))
        self.assertEqual(st["ended"], "time cap")
        self.assertEqual(st["result"]["pulled_first"], 2)

    def test_budget_raises_at_cap_and_holds_the_gap(self):
        clock = Clock()
        b = hd.Budget(2, 1.0, opener=lambda req, timeout=None: "ok", sleep=clock.sleep, clock=clock)
        t = clock()
        b.opener(None), b.opener(None)
        self.assertAlmostEqual(clock() - t, 1.0)
        with self.assertRaises(hd.BudgetExhausted):
            b.opener(None)

    def test_throttled_host_stops_the_run(self):
        self.cfg["history_daily"]["stop_after_throttled"] = 2
        st = self.run_once(FakeNet(self.repos, fail=503))
        self.assertEqual(st["result"]["throttled"], 2)
        self.assertTrue(st["ended"].startswith("stopped"))
        self.assertEqual(st["result"]["pulled_first"], 0)
        self.assertEqual(hd.last_pulls(self.data / "raw" / "histories",
                                       self.data / "state" / "history_daily" / "pulls.jsonl"), {})  # retried later

    def test_status_has_counts_only(self):
        self.run_once(FakeNet(self.repos))
        text = (self.status / "histories.json").read_text()
        self.assertNotIn("did:", text)
        self.assertNotIn("did_plc", text)


class TestResumeAndDedupe(Base):
    def setUp(self):
        super().setUp()
        w0 = bc.iso_to_us("2026-11-27T00:00:00Z")
        self.hour("2026-11-27T05", [jet_line(did(i), w0 + 5 * 3_600_000_000 + i) for i in range(1, 4)])
        self.repos = {did(i): records(did(i), 30, T0 - DAY) for i in range(1, 4)}

    def files(self):
        return {p: p.read_bytes() for p in (self.data / "raw").rglob("*")
                if p.is_file() and "jetstream" not in p.parts and "plc" not in p.parts}

    def test_resume_skips_recent_pulls_and_retries_failures(self):
        self.cfg["history_daily"]["accounts_per_run"] = 2
        self.run_once(FakeNet(self.repos))
        st = self.run_once(FakeNet(self.repos), clock=Clock(T0 + 3600e6))
        self.assertEqual(st["result"]["pulled_first"], 1)          # only the one not pulled yet
        st = self.run_once(FakeNet(self.repos), clock=Clock(T0 + 2 * 3600e6))
        self.assertEqual(st["ended"], "queue empty")
        self.assertEqual(st["result"]["pulled_first"] + st["result"]["repulled"], 0)
        pulled = [x["did"] for x in self.ledger()]
        self.assertEqual(len(pulled), len(set(pulled)), "an account was pulled twice")

    def test_pilot_history_counts_as_a_pull(self):
        d = self.data / "raw" / "histories" / did(1)[-2:]
        d.mkdir(parents=True)
        bc.atomic_json(d / (did(1).replace(":", "_") + ".done.json"), {"fetched": hd._iso(T0 - DAY), "anchor_us": T0 - DAY})
        st = self.run_once(FakeNet(self.repos))
        self.assertEqual(st["queue_before"]["pulled_recently"], 1)
        self.assertEqual(st["result"]["pulled_first"], 2)

    def test_first_pull_writes_each_record_once_and_gone_accounts_are_marked(self):
        net = FakeNet(self.repos, gone={did(3)}, dup={did(1)})
        st = self.run_once(net)
        self.assertEqual((st["result"]["pulled_first"], st["result"]["gone"]), (2, 1))
        f = self.data / "raw" / "histories" / did(1)[-2:] / (did(1).replace(":", "_") + ".jsonl.gz")
        uris = [json.loads(x)["uri"] for x in gzip.open(f, "rt", encoding="utf-8")]
        self.assertEqual(len(uris), 30)
        self.assertEqual(len(set(uris)), 30)
        gone = bc.load_json(self.data / "raw" / "histories" / did(3)[-2:] / (did(3).replace(":", "_") + ".done.json"), {})
        self.assertTrue(gone["gone"])

    def test_repull_appends_only_new_records_and_changes_no_existing_file(self):
        self.run_once(FakeNet(self.repos))
        before = self.files()
        later = T0 + 20 * DAY
        for i in range(1, 4):                                       # 5 new posts each since the first pull
            self.repos[did(i)] = records(did(i), 5, later - 3600e6, step_us=3600e6) + self.repos[did(i)]
        st = self.run_once(FakeNet(self.repos, dup={did(1)}), clock=Clock(later))
        self.assertEqual(st["result"]["repulled"], 3)
        self.assertEqual(st["result"]["records_written"], 15)
        after = self.files()
        for p, b in before.items():
            self.assertEqual(after[p], b, f"{p.name} was changed")
        new = [p for p in after if p not in before and p.name.endswith(".jsonl.gz")]
        self.assertEqual(len(new), 3)
        self.assertTrue(all("histories_daily" in p.parts for p in new))
        all_uris = []
        for p in after:
            if p.name.endswith(".jsonl.gz"):
                all_uris += [json.loads(x)["uri"] for x in gzip.open(p, "rt", encoding="utf-8")]
        self.assertEqual(len(all_uris), len(set(all_uris)), "a record is on disk twice")
        st = self.run_once(FakeNet(self.repos), clock=Clock(later + 3600e6))   # and not again the same day
        self.assertEqual(st["result"]["repulled"], 0)

    def test_a_write_that_fails_halfway_leaves_nothing_normalize_would_read(self):
        # normalize stages raw/histories/<aa>/*.jsonl.gz while the nightly pull runs (both from 04:30)
        d = self.data / "raw" / "histories" / "aa"
        good = records(did(1), 3, T0)
        hd._write_gz(d / "x.jsonl.gz", good)
        before = (d / "x.jsonl.gz").read_bytes()
        with self.assertRaises(TypeError):
            hd._write_gz(d / "y.jsonl.gz", good + [{"uri": object()}])     # dies after writing some lines
        self.assertEqual(sorted(p.name for p in d.glob("*.jsonl.gz")), ["x.jsonl.gz"])
        self.assertEqual((d / "x.jsonl.gz").read_bytes(), before)

    def test_shipped_caps_leave_time_as_the_binding_limit(self):
        s = hd.settings(bc.load_config())
        sec_per_request, requests_per_account = 0.57, 56          # the Nov 28 check run (most active repliers)
        requests_by_time = s["max_minutes"] * 60 / sec_per_request
        self.assertGreater(s["requests_per_run"], requests_by_time)
        self.assertGreater(s["accounts_per_run"], requests_by_time / requests_per_account)
        self.assertLessEqual(s["max_minutes"], 360)                  # owner's window ends 07:00
        self.assertEqual((s["min_gap_s"], s["stop_after_throttled"]), (0.4, 3))

    def test_second_copy_cannot_start(self):
        a = hd.single_instance(self.data / "state")
        self.assertIsNotNone(a)
        self.assertIsNone(hd.single_instance(self.data / "state"))
        a.close()


if __name__ == "__main__":
    unittest.main()
