import csv
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.bb_inventory import (
    build_inventory,
    extract_username,
    iter_records,
    normalize_flair,
    write_counts_csv,
    write_private_inventory_csv,
)


class TestBBInventory(unittest.TestCase):
    def test_extract_username_from_url_and_title(self):
        self.assertEqual(
            extract_username({"url": "https://www.reddit.com/user/example_user_1"}),
            "example_user_1",
        )
        self.assertEqual(
            extract_username({"url": "https://old.reddit.com/u/example_user_2/comments"}),
            "example_user_2",
        )
        self.assertEqual(
            extract_username({"url": "", "title": "Overview for example_user_3"}),
            "example_user_3",
        )
        self.assertIsNone(extract_username({"url": "https://reddit.com/r/BotBouncer", "title": "Meta thread"}))

    def test_deduplication_keeps_latest_verdict(self):
        # Synthetic records for example_user_1 listed twice: pending in Jan 2026, banned in Feb 2026
        records = [
            {
                "url": "https://www.reddit.com/user/example_user_1",
                "link_flair_text": "Pending",
                "created_utc": 1768435200,  # 2026-01-15
            },
            {
                "title": "Overview for EXAMPLE_USER_1",
                "link_flair_text": "Banned",
                "created_utc": 1770681600,  # 2026-02-10
            },
            {
                "url": "https://www.reddit.com/user/example_user_2",
                "link_flair_text": "Organic",
                "created_utc": 1770768000,  # 2026-02-11
            },
        ]
        latest_by_user, month_counts = build_inventory(records)
        self.assertEqual(len(latest_by_user), 2)
        user1_name, user1_flair, user1_ts = latest_by_user["example_user_1"]
        self.assertEqual(user1_flair, "banned")
        self.assertEqual(user1_ts, 1770681600)
        self.assertEqual(month_counts["2026-02"]["banned"], 1)
        self.assertEqual(month_counts["2026-02"]["organic"], 1)
        self.assertEqual(month_counts["2026-01"]["pending"], 0)

    def test_zip_and_csv_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            zip_path = tmp_path / "synthetic_bb.zip"
            rows = [
                {"url": "https://reddit.com/user/example_bot_1", "link_flair_text": "Banned", "created_utc": 1770681600},
                {"url": "https://reddit.com/user/example_org_1", "link_flair_text": "Organic", "created_utc": 1770768000},
            ]
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("dump.jsonl", "\n".join(json.dumps(r) for r in rows))

            loaded = list(iter_records([zip_path]))
            latest, month_counts = build_inventory(loaded)
            counts_csv = tmp_path / "counts.csv"
            priv_csv = tmp_path / "private.csv"
            write_counts_csv(month_counts, counts_csv)
            write_private_inventory_csv(latest, priv_csv)

            with counts_csv.open() as f:
                c_rows = list(csv.DictReader(f))
            self.assertEqual(len(c_rows), 1)
            self.assertEqual(c_rows[0]["month"], "2026-02")
            self.assertEqual(c_rows[0]["banned"], "1")
            self.assertEqual(c_rows[0]["organic"], "1")


if __name__ == "__main__":
    unittest.main()

