"""Unit tests for safe e-commerce action service using unittest."""

import copy
import unittest

try:
    from backend.mock_data import ORDERS, PAYMENTS
    from backend.action_service import (
        cancel_order,
        clear_action_data,
        get_return_request,
        list_return_requests,
        request_return,
    )
except ImportError:
    from mock_data import ORDERS, PAYMENTS
    from action_service import (
        cancel_order,
        clear_action_data,
        get_return_request,
        list_return_requests,
        request_return,
    )


class TestActionService(unittest.TestCase):
    def setUp(self):
        clear_action_data()

    def tearDown(self):
        clear_action_data()

    def test_cancel_processing_order_succeeds(self):
        # ORD1002 is originally 'processing'
        res = cancel_order("ORD1002", reason="Changed mind")
        self.assertTrue(res["success"])
        self.assertEqual(res["order_id"], "ORD1002")
        self.assertEqual(res["order"]["status"], "cancelled")

        # Verify underlying mock data updated only for ORD1002
        ord1002 = next(o for o in ORDERS if o["id"] == "ORD1002")
        self.assertEqual(ord1002["status"], "cancelled")

        # Verify other orders not modified
        ord1001 = next(o for o in ORDERS if o["id"] == "ORD1001")
        self.assertEqual(ord1001["status"], "delivered")

    def test_cancel_shipped_order_rejected(self):
        # ORD1003 is 'shipped'
        res = cancel_order("ORD1003")
        self.assertFalse(res["success"])
        self.assertIn("already shipped", res["message"])
        ord1003 = next(o for o in ORDERS if o["id"] == "ORD1003")
        self.assertEqual(ord1003["status"], "shipped")

    def test_cancel_delivered_order_rejected(self):
        # ORD1001 is 'delivered'
        res = cancel_order("ORD1001")
        self.assertFalse(res["success"])
        self.assertIn("already been delivered", res["message"])
        ord1001 = next(o for o in ORDERS if o["id"] == "ORD1001")
        self.assertEqual(ord1001["status"], "delivered")

    def test_cancel_nonexistent_order_rejected(self):
        res = cancel_order("ORD9999")
        self.assertFalse(res["success"])
        self.assertIn("was not found", res["message"])
        self.assertIsNone(res["order"])

    def test_return_delivered_order_succeeds(self):
        # ORD1001 is 'delivered'
        res = request_return("ORD1001", request_type="return", reason="Wrong size")
        self.assertTrue(res["success"])
        self.assertEqual(res["order_id"], "ORD1001")
        ret = res["return_request"]
        self.assertIsNotNone(ret)
        self.assertTrue(ret["request_id"].startswith("RET-"))
        self.assertEqual(ret["status"], "pending")
        self.assertEqual(ret["request_type"], "return")

        # Verify recorded in service
        all_reqs = list_return_requests("ORD1001")
        self.assertEqual(len(all_reqs), 1)

    def test_return_ineligible_processing_order_rejected(self):
        # ORD1002 is 'processing'
        res = request_return("ORD1002", request_type="return")
        self.assertFalse(res["success"])
        self.assertIn("only permitted for 'delivered' orders", res["message"])
        self.assertIsNone(res["return_request"])
        self.assertEqual(len(list_return_requests("ORD1002")), 0)

    def test_duplicate_active_return_prevented(self):
        # First request succeeds
        res1 = request_return("ORD1001", request_type="return")
        self.assertTrue(res1["success"])

        # Second request for same order is rejected
        res2 = request_return("ORD1001", request_type="replacement")
        self.assertFalse(res2["success"])
        self.assertIn("already exists", res2["message"])
        self.assertEqual(len(list_return_requests("ORD1001")), 1)

    def test_payments_remain_unmodified(self):
        payments_before = copy.deepcopy(PAYMENTS)
        cancel_order("ORD1002")
        request_return("ORD1001")
        cancel_order("ORD9999")
        self.assertEqual(PAYMENTS, payments_before)


if __name__ == "__main__":
    unittest.main()
