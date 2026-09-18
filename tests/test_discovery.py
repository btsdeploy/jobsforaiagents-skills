import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("client", Path(__file__).parents[1] / "skills/find-paid-onchain-jobs/scripts/find_jobs.py")
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.row = {"id": "native_task_00000000-0000-4000-8000-000000000001", "kind": "native-escrow", "status": "open", "category": "marketing", "application_deadline": 2000, "payout": {"chain_id": 8453, "currency": "USDC", "monetary_value": True, "amount": "1.00", "amount_atomic": "1000000"}}

    def select(self, row, **kwargs):
        return client.select_jobs({"schema_version": "1", "jobs": [row], "partial": False}, now=1000, **kwargs)["count"]

    def test_valid_and_filters(self):
        self.assertEqual(self.select(self.row, minimum=100, category="marketing"), 1)
        self.assertEqual(self.select(self.row, minimum=101), 0)
        self.assertEqual(self.select(self.row, category="code"), 0)

    def test_expired_and_unfunded_excluded(self):
        for field, value in [("status", "awaiting_funding"), ("status", "paid"), ("kind", "reviewed-external"), ("application_deadline", 1000)]:
            row = copy.deepcopy(self.row)
            row[field] = value
            self.assertEqual(self.select(row), 0)

    def test_testnet_wrong_asset_and_inconsistent_amounts_excluded(self):
        for field, value in [("chain_id", 84532), ("currency", "ETH"), ("monetary_value", False), ("amount", "1.009"), ("amount_atomic", "999999")]:
            row = copy.deepcopy(self.row)
            row["payout"][field] = value
            self.assertEqual(self.select(row), 0)

    def test_money_and_schema(self):
        self.assertEqual(client.cents("10.52"), 1052)
        for invalid in ["10.519999", "1e2", "-1", "NaN"]:
            with self.assertRaises(ValueError): client.cents(invalid)
        with self.assertRaises(ValueError): client.select_jobs({"items": []})
        self.assertTrue(client.select_jobs({"schema_version": "1", "jobs": []})["partial"])


if __name__ == "__main__":
    unittest.main()
