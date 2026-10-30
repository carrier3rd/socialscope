import unittest
from socialscope.prewindow import DAY_SECONDS, compute_prewindow_features


class TestPrewindowFeatures(unittest.TestCase):
    def setUp(self):
        self.anchor = 1790000000.0  # Fixed synthetic anchor timestamp

    def test_normal_comparative_history(self):
        # Earlier items: 90 days and 60 days before anchor (30-day span before window_start at -30d)
        # Window start is anchor - 30d. First earlier is anchor - 90d -> earlier_span_days = 60 days.
        history = [
            {
                "created_utc": self.anchor - 90 * DAY_SECONDS,
                "subreddit": "SubOne",
                "body": "A normal thoughtful comment of forty chars",
                "score": 10,
            },
            {
                "created_utc": self.anchor - 60 * DAY_SECONDS,
                "subreddit": "SubOne",
                "body": "Another baseline comment with forty chars!",
                "score": 12,
            },
            # Window items (within 30 days before anchor)
            {
                "created_utc": self.anchor - 10 * DAY_SECONDS,
                "subreddit": "SubTwo",
                "body": "short",
                "score": 1,
            },
            {
                "created_utc": self.anchor - 5 * DAY_SECONDS,
                "subreddit": "SubThree",
                "body": "Check https://example.com",
                "score": 3,
            },
        ]
        feats = compute_prewindow_features(history, anchor_utc=self.anchor)
        self.assertEqual(feats["earlier_items"], 2)
        self.assertEqual(feats["window_items"], 2)
        self.assertAlmostEqual(feats["new_subreddit_share"], 1.0)
        self.assertAlmostEqual(feats["distinct_subs_per_item"], 1.0)
        # Earlier rate: 2 items / 60 days = 1/30 per day. Window rate: 2 items / 30 days = 2/30 per day -> ratio 2.0
        self.assertAlmostEqual(feats["posting_rate_ratio"], 2.0)
        # Earlier median len: 42. Window lengths: len("short")=5, len("Check https://example.com")=25 -> median 15.0 -> 15/42
        self.assertAlmostEqual(feats["median_length_ratio"], 15.0 / 42.0, places=5)
        # Earlier links: 0/2 = 0. Window links: 1/2 = 0.5 -> +0.5
        self.assertAlmostEqual(feats["link_share_change"], 0.5)
        # Window short comments (<=20 chars): 1 of 2 -> 0.5
        self.assertAlmostEqual(feats["short_comment_share"], 0.5)
        # Earlier median score: 11.0, Window median score: 2.0 -> -9.0
        self.assertAlmostEqual(feats["score_median_change"], -9.0)
        # Gaps before window: (-90d to -60d = 30d), (-60d to -10d = 50d) -> 50.0 days
        self.assertAlmostEqual(feats["longest_silence_before_window"], 50.0)

    def test_edge_case_short_or_empty_history(self):
        feats_empty = compute_prewindow_features([], anchor_utc=self.anchor)
        self.assertEqual(feats_empty["window_items"], 0)
        self.assertEqual(feats_empty["earlier_items"], 0)
        self.assertEqual(feats_empty["posting_rate_ratio"], 0.0)

        # Single item in window
        feats_one = compute_prewindow_features(
            [{"created_utc": self.anchor - 100, "subreddit": "AskReddit", "body": "ok", "score": 1}],
            anchor_utc=self.anchor,
        )
        self.assertEqual(feats_one["window_items"], 1)
        self.assertEqual(feats_one["earlier_items"], 0)
        self.assertEqual(feats_one["new_subreddit_share"], 1.0)
        self.assertEqual(feats_one["short_comment_share"], 1.0)
        self.assertEqual(feats_one["longest_silence_before_window"], 0.0)

    def test_edge_case_nothing_in_window(self):
        history = [
            {"created_utc": self.anchor - 100 * DAY_SECONDS, "subreddit": "SubA", "body": "hello world", "score": 5},
            {"created_utc": self.anchor - 40 * DAY_SECONDS, "subreddit": "SubA", "body": "second post", "score": 7},
        ]
        feats = compute_prewindow_features(history, anchor_utc=self.anchor)
        self.assertEqual(feats["window_items"], 0)
        self.assertEqual(feats["earlier_items"], 2)
        self.assertEqual(feats["new_subreddit_share"], 0.0)
        self.assertEqual(feats["distinct_subs_per_item"], 0.0)
        self.assertEqual(feats["posting_rate_ratio"], 0.0)
        self.assertEqual(feats["median_length_ratio"], 0.0)
        self.assertEqual(feats["link_share_change"], 0.0)
        self.assertEqual(feats["short_comment_share"], 0.0)
        self.assertEqual(feats["score_median_change"], 0.0)
        # Gap between -100d and -40d is 60.0 days (transition gap to -30d is 10d)
        self.assertAlmostEqual(feats["longest_silence_before_window"], 60.0)

    def test_edge_case_all_items_in_window(self):
        history = [
            {"created_utc": self.anchor - 20 * DAY_SECONDS, "subreddit": "SubA", "body": "first item", "score": 2},
            {"created_utc": self.anchor - 2 * DAY_SECONDS, "subreddit": "SubB", "body": "second item in window via https://test.org", "score": 4},
        ]
        feats = compute_prewindow_features(history, anchor_utc=self.anchor)
        self.assertEqual(feats["window_items"], 2)
        self.assertEqual(feats["earlier_items"], 0)
        self.assertEqual(feats["new_subreddit_share"], 1.0)
        self.assertEqual(feats["distinct_subs_per_item"], 1.0)
        self.assertEqual(feats["posting_rate_ratio"], 0.0)
        self.assertEqual(feats["median_length_ratio"], 0.0)
        self.assertEqual(feats["link_share_change"], 0.0)
        self.assertEqual(feats["short_comment_share"], 0.5)
        self.assertEqual(feats["score_median_change"], 0.0)
        self.assertEqual(feats["longest_silence_before_window"], 0.0)


if __name__ == "__main__":
    unittest.main()

