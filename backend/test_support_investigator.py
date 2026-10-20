"""Unit tests for support investigator service and chat integration using unittest."""

import copy
import unittest

try:
    from backend.mock_data import ORDERS, PAYMENTS
    from backend.schemas import ChatRequest
    from backend.main import chat_endpoint
    from backend.support_investigator import extract_order_id, investigate_order_context
except ImportError:
    from mock_data import ORDERS, PAYMENTS
    from schemas import ChatRequest
    from main import chat_endpoint
    from support_investigator import extract_order_id, investigate_order_context


class TestSupportInvestigator(unittest.TestCase):
    def test_extract_existing_order_and_details(self):
        msg = "I want to check the status of my order ORD1001"
        result = investigate_order_context(msg)
        self.assertTrue(result["attempted"])
        self.assertEqual(result["status"], "found")
        self.assertEqual(result["order_id"], "ORD1001")
        self.assertIsNotNone(result["order"])
        self.assertEqual(result["order"]["id"], "ORD1001")
        self.assertEqual(result["order"]["customer_id"], "CUST001")
        self.assertIn("delivered", result["summary"])

    def test_order_with_payment_records(self):
        msg = "Payment inquiry for ORD1001"
        result = investigate_order_context(msg)
        self.assertIsNotNone(result["payments"])
        self.assertGreater(len(result["payments"]), 0)
        self.assertEqual(result["payments"][0]["id"], "PAY2001")
        self.assertEqual(result["payments"][0]["status"], "successful")
        self.assertEqual(result["payments"][0]["transaction_ref"], "TXN-908123-SUCCESS")

    def test_missing_order_id(self):
        msg = "Where is my package? It is late."
        result = investigate_order_context(msg)
        self.assertFalse(result["attempted"])
        self.assertEqual(result["status"], "order_id_required")
        self.assertIsNone(result["order_id"])
        self.assertIsNone(result["order"])
        self.assertIsNone(result["payments"])
        self.assertIn("order ID", result["summary"])

    def test_nonexistent_order_id(self):
        msg = "Could you please locate ORD9999?"
        result = investigate_order_context(msg)
        self.assertTrue(result["attempted"])
        self.assertEqual(result["status"], "order_not_found")
        self.assertEqual(result["order_id"], "ORD9999")
        self.assertIsNone(result["order"])
        self.assertIsNone(result["payments"])
        self.assertIn("ORD9999", result["summary"])

    def test_case_insensitive_order_id(self):
        self.assertEqual(extract_order_id("Please track ord1001"), "ORD1001")
        self.assertEqual(extract_order_id("Check OrD1002 now"), "ORD1002")

        res_lower = investigate_order_context("Status for ord1001 please")
        self.assertEqual(res_lower["status"], "found")
        self.assertEqual(res_lower["order_id"], "ORD1001")

    def test_no_mock_data_mutation(self):
        orig_order_0 = copy.deepcopy(ORDERS[0])
        orig_payment_0 = copy.deepcopy(PAYMENTS[0])

        result = investigate_order_context("Check ORD1001")
        # Mutate the returned dictionary
        result["order"]["status"] = "MUTATED_TEST_STATUS"
        result["order"]["total_amount"] = 99999.99
        result["payments"][0]["status"] = "MUTATED_PAYMENT"

        # Assert mock data remains untouched
        self.assertEqual(ORDERS[0]["status"], orig_order_0["status"])
        self.assertEqual(ORDERS[0]["total_amount"], orig_order_0["total_amount"])
        self.assertEqual(PAYMENTS[0]["status"], orig_payment_0["status"])

    def test_chat_endpoint_integration(self):
        req = ChatRequest(message="Where is my order ord1001?", session_id="test-session")
        resp = chat_endpoint(req)
        self.assertEqual(resp.session_id, "test-session")
        self.assertEqual(resp.intent, "order_tracking")
        self.assertIsNotNone(resp.investigation)
        self.assertEqual(resp.investigation.status, "found")
        self.assertEqual(resp.investigation.order_id, "ORD1001")
        self.assertEqual(resp.investigation.order.id, "ORD1001")
        self.assertGreater(len(resp.investigation.payments), 0)


if __name__ == "__main__":
    unittest.main()
