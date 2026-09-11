import unittest
from datetime import timedelta
from unittest.mock import MagicMock, patch

from worker import (
    PROCESSING_TIMEOUT,
    _build_parent_issues,
    _merge_first_detected,
    recover_stale_processing,
)


class FakeExecuteResult:
    def scalar_one_or_none(self):
        return None


class FakeSession:
    def __init__(self):
        self.execute_calls = []
        self.commit_calls = 0
        self.rollback_calls = 0
        self.closed = False

    def execute(self, statement):
        self.execute_calls.append(statement)
        return FakeExecuteResult()

    def commit(self):
        self.commit_calls += 1

    def rollback(self):
        self.rollback_calls += 1

    def close(self):
        self.closed = True


class TestPhase2Worker(unittest.TestCase):
    def test_merge_first_detected_uses_first_detected_value(self):
        first = MagicMock()
        first.declarations = {
            "mrp": None,
            "net_quantity": "500 g",
            "date_of_mfg": None,
            "manufacturer_address": None,
            "consumer_care": None,
        }

        second = MagicMock()
        second.declarations = {
            "mrp": "MRP ₹100",
            "net_quantity": "1 kg",
            "date_of_mfg": "Jan 2026",
            "manufacturer_address": "Example Address",
            "consumer_care": "1800 123 4567",
        }

        result = _merge_first_detected([first, second])

        self.assertEqual(result["mrp"], "MRP ₹100")
        self.assertEqual(result["net_quantity"], "500 g")
        self.assertEqual(result["date_of_mfg"], "Jan 2026")
        self.assertEqual(
            result["manufacturer_address"],
            "Example Address",
        )
        self.assertEqual(
            result["consumer_care"],
            "1800 123 4567",
        )

    def test_merge_first_detected_returns_none_when_missing(self):
        image = MagicMock()
        image.declarations = {}

        result = _merge_first_detected([image])

        self.assertEqual(
            result,
            {
                "mrp": None,
                "net_quantity": None,
                "date_of_mfg": None,
                "manufacturer_address": None,
                "consumer_care": None,
            },
        )

    def test_build_parent_issues_reports_missing_declarations(self):
        declarations = {
            "mrp": None,
            "net_quantity": None,
            "date_of_mfg": None,
            "manufacturer_address": None,
            "consumer_care": None,
        }

        issues = _build_parent_issues(
            declarations,
            False,
            None,
        )

        self.assertEqual(len(issues), 6)
        self.assertIn(
            "Rule 6(1)(e): Retail sale price (MRP) not detected",
            issues,
        )
        self.assertIn(
            "Rule 6(1)(c): Net quantity not detected",
            issues,
        )
        self.assertIn(
            "Rule 7: Text may be smaller than the required numeral height",
            issues,
        )

    def test_build_parent_issues_empty_when_complete_and_readable(self):
        declarations = {
            "mrp": "MRP ₹100",
            "net_quantity": "Net Qty 500 g",
            "date_of_mfg": "Jan 2026",
            "manufacturer_address": "Manufactured by Example",
            "consumer_care": "18001234567",
        }

        issues = _build_parent_issues(
            declarations,
            True,
            2,
        )

        self.assertEqual(issues, [])

    def test_recover_stale_processing_runs_update_and_commit(self):
        fake_session = FakeSession()

        with patch(
            "worker.SessionLocal",
            return_value=fake_session,
        ):
            recover_stale_processing()

        self.assertEqual(len(fake_session.execute_calls), 1)
        self.assertEqual(fake_session.commit_calls, 1)
        self.assertEqual(fake_session.rollback_calls, 0)
        self.assertTrue(fake_session.closed)

    def test_processing_timeout_is_15_minutes(self):
        self.assertEqual(
            PROCESSING_TIMEOUT,
            timedelta(minutes=15),
        )


if __name__ == "__main__":
    unittest.main()
