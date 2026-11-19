"""Bluesky -> frozen v7.1 adapter (bluesky/features/shared.py) on synthetic records. No network, no real accounts."""
import contextlib
import io
import json
import math
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "bluesky"))
from features import shared  # noqa: E402
from socialscope import lookup_core as LC  # noqa: E402

AUTHOR = "did:plc:aaaaaaaaaaaaaaaaaaaaaaaa"


def rec(key, iso, text, reply_to=None, root=None, link=None):
    v = {"$type": "app.bsky.feed.post", "text": text, "createdAt": iso}
    if reply_to:
        v["reply"] = {"root": {"uri": f"at://{AUTHOR}/app.bsky.feed.post/{root or reply_to}"},
                      "parent": {"uri": f"at://{AUTHOR}/app.bsky.feed.post/{reply_to}"}}
    if link:
        v["embed"] = {"$type": "app.bsky.embed.external", "external": {"uri": link}}
    return {"uri": f"at://{AUTHOR}/app.bsky.feed.post/{key}", "cid": "x", "value": v}


def history(n=120):
    out = []
    for i in range(n):
        day, hour = 1 + i // 12, i % 12 + 8
        iso = f"2026-10-{day:02d}T{hour:02d}:{(i * 7) % 60:02d}:00.000Z"
        if i % 4 == 0:
            out.append(rec(f"p{i}", iso, f"Top-level post number {i} about the weather and some news today.",
                           link="https://example.com/a" if i % 8 == 0 else None))
        elif i % 4 == 1:
            out.append(rec(f"r{i}", iso, f"I agree with this point, reply {i}.", reply_to=f"p{i - 1}"))
        else:
            out.append(rec(f"r{i}", iso, f"Replying further down the thread, {i}.", reply_to=f"r{i - 1}", root=f"p{i - 2 - (i % 4 == 3)}"))
    return out


class Mapping(unittest.TestCase):
    def test_post_becomes_submission(self):
        it = shared.to_item(rec("k1", "2026-11-01T12:00:00Z", "hello", link="https://ex.com/x"), "u")
        self.assertEqual(it["title"], "hello")
        self.assertEqual(it["selftext"], "")
        self.assertEqual(it["url"], "https://ex.com/x")
        self.assertNotIn("subreddit", it)
        self.assertNotIn("score", it)
        self.assertEqual(it["created_utc"], 1793534400.0)

    def test_reply_to_root_is_top_level_comment(self):
        it = shared.to_item(rec("k2", "2026-11-01T12:00:00Z", "hi", reply_to="root1"), "u")
        self.assertEqual(it["body"], "hi")
        self.assertEqual(it["link_id"], "t3_root1")
        self.assertEqual(it["parent_id"], "t3_root1")

    def test_nested_reply_points_at_parent_comment(self):
        it = shared.to_item(rec("k3", "2026-11-01T12:00:00Z", "hi", reply_to="mid", root="root1"), "u")
        self.assertEqual(it["link_id"], "t3_root1")
        self.assertEqual(it["parent_id"], "t1_mid")

    def test_bad_time_is_dropped_and_counted(self):
        bad = rec("k4", "not a date", "x")
        items, n_bad = shared.to_items([bad, rec("k5", "2026-11-01T00:00:00Z", "y")], "u")
        self.assertEqual((len(items), n_bad), (1, 1))

    def test_facet_link_used_when_no_embed(self):
        r = rec("k6", "2026-11-01T00:00:00Z", "see link")
        r["value"]["facets"] = [{"features": [{"$type": "app.bsky.richtext.facet#link", "uri": "https://ex.org/y"}]}]
        self.assertEqual(shared.to_item(r, "u")["url"], "https://ex.org/y")


class Mask(unittest.TestCase):
    def test_mask_covers_recon_subreddit_and_score_inputs(self):
        for c in ("subs", "farm_share", "top_sub_share", "sub_spread", "pw_new_subreddit_share",
                  "pw_distinct_subs_per_item", "sh", "sb", "political_early", "political_late", "primary",
                  "bot_score", "pw_score_median_change"):
            self.assertIn(c, shared.MASKED)

    def test_mask_blanks_in_place(self):
        row = {"subs": 1, "items": 5}
        shared.mask(row)
        self.assertTrue(math.isnan(row["subs"]))
        self.assertEqual(row["items"], 5)


class EndToEnd(unittest.TestCase):
    def test_frozen_features_and_model_run_on_adapted_items(self):
        M = json.load(open(os.path.join(REPO, "site", "public", "lookup", "model.json")))
        items, bad = shared.to_items(history(), "acct_test")
        self.assertEqual(bad, 0)
        with contextlib.redirect_stdout(io.StringIO()):
            row = LC.features("acct_test", items, items[0]["created_utc"] - 86400 * 400)
        shared.mask(row)
        x = LC.feature_vector(row, M)
        p = LC.predict(M, x)
        self.assertTrue(0.0 <= p <= 1.0)
        self.assertEqual(row["n_cut"], 120)
        self.assertGreater(float(row["top_level_share"]), 0.0)   # replies to the root map to top-level comments


if __name__ == "__main__":
    unittest.main()
