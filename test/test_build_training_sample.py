import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_training_sample import (
    build_training_sample,
    parse_cutoff,
    write_sample_outputs,
)


class TestBuildTrainingSample(unittest.TestCase):
    def test_temporal_split_and_exclusions_and_fixed_seed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            inv_csv = tmp_path / "inventory.csv"
            weekly_jsonl = tmp_path / "weekly_comments.jsonl"
            exclude_txt = tmp_path / "exclude.txt"

            # Cutoff: 2026-10-01T00:00:00Z = 1790812800
            cutoff_ts = parse_cutoff("2026-10-01")

            with inv_csv.open("w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["username", "flair", "listed_utc"])
                w.writerow(["example_bot_train", "banned", cutoff_ts - 86400])
                w.writerow(["example_bot_test", "banned", cutoff_ts + 86400])
                w.writerow(["example_bot_excluded", "banned", cutoff_ts - 1000])
                w.writerow(["example_org_train", "organic", cutoff_ts - 172800])
                w.writerow(["example_org_test", "organic", cutoff_ts + 3600])

            with weekly_jsonl.open("w") as f:
                for row in [
                    {"author": "example_active_1", "created_utc": cutoff_ts - 5000},
                    {"author": "example_active_2", "created_utc": cutoff_ts + 5000},
                    {"author": "example_bot_train", "created_utc": cutoff_ts - 2000},  # In inventory, must not be in random
                    {"author": "example_active_excluded", "created_utc": cutoff_ts - 1000},
                    {"author": "[deleted]", "created_utc": cutoff_ts},
                ]:
                    f.write(json.dumps(row) + "\n")

            exclude_txt.write_text("example_bot_excluded\nu/example_active_excluded\n")

            rec1 = build_training_sample(
                inventory_path=inv_csv,
                weekly_paths=[weekly_jsonl],
                n_per_group=2,
                cutoff_utc=cutoff_ts,
                exclude_path=exclude_txt,
                seed=42,
            )
            rec2 = build_training_sample(
                inventory_path=inv_csv,
                weekly_paths=[weekly_jsonl],
                n_per_group=2,
                cutoff_utc=cutoff_ts,
                exclude_path=exclude_txt,
                seed=42,
            )
            self.assertEqual(rec1, rec2)

            by_user = {r["username"]: r for r in rec1}
            self.assertNotIn("example_bot_excluded", by_user)
            self.assertNotIn("example_active_excluded", by_user)
            self.assertEqual(by_user["example_bot_train"]["split"], "train")
            self.assertEqual(by_user["example_bot_test"]["split"], "test")
            self.assertEqual(by_user["example_org_train"]["split"], "train")
            self.assertEqual(by_user["example_org_test"]["split"], "test")
            self.assertEqual(by_user["example_active_1"]["group"], "random")
            self.assertEqual(by_user["example_active_1"]["split"], "train")
            self.assertEqual(by_user["example_active_2"]["split"], "test")

            users_path, groups_path = write_sample_outputs(rec1, tmp_path / "out")
            self.assertTrue(users_path.exists())
            self.assertTrue(groups_path.exists())


if __name__ == "__main__":
    unittest.main()

