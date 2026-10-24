"""Unit and integration tests for LangGraph Autonomous Support Multi-Agent Graph."""

import unittest

from backend.mock_data import reset_mock_data
from backend.graph import run_support_workflow


class TestSupportGraph(unittest.TestCase):

    def setUp(self):
        reset_mock_data()

    def tearDown(self):
        reset_mock_data()

    def test_order_tracking_lookup(self):
        res = run_support_workflow("Where is my order ORD1001?", session_id="test-trk-1")
        self.assertEqual(res["intent"], "order_tracking")
        self.assertEqual(res["decision"], "order_found")
        self.assertIn("ORD1001", res["assistant_message"])
        self.assertIn("delivered", res["assistant_message"])
        self.assertTrue(res["investigation"]["attempted"])

    def test_anaphoric_memory_retention(self):
        session_id = "test-mem-thread-42"
        # Turn 1: Mention order
        turn1 = run_support_workflow("Where is my order ORD1001?", session_id=session_id)
        self.assertEqual(turn1["decision"], "order_found")

        # Turn 2: Anaphoric follow-up without explicitly repeating ORD1001
        turn2 = run_support_workflow("When was it ordered?", session_id=session_id)
        self.assertEqual(turn2["decision"], "order_found")
        self.assertIn("ORD1001", turn2["assistant_message"])

    def test_cancellation_confirmation_and_execution(self):
        session_id = "test-cancel-flow-1"
        # Turn 1: Request cancellation
        turn1 = run_support_workflow("I want to cancel order ORD1002", session_id=session_id)
        self.assertEqual(turn1["decision"], "confirmation_required")
        self.assertIn("Are you sure you would like to proceed", turn1["assistant_message"])
        self.assertFalse(turn1["action_result"]["success"])

        # Turn 2: Confirm with 'yes'
        turn2 = run_support_workflow("yes", session_id=session_id)
        self.assertEqual(turn2["decision"], "action_completed")
        self.assertTrue(turn2["action_result"]["success"])
        self.assertEqual(turn2["action_result"]["order"]["status"], "cancelled")

    def test_cancellation_rejected_for_delivered_order(self):
        res = run_support_workflow("Please cancel order ORD1001", session_id="test-cancel-inelig")
        self.assertEqual(res["decision"], "action_rejected")
        self.assertIn("delivered", res["assistant_message"])
        self.assertFalse(res["action_result"]["success"])

    def test_return_request_execution(self):
        res = run_support_workflow("I want to return order ORD1001 because it is defective", session_id="test-ret-1")
        self.assertEqual(res["decision"], "action_completed")
        self.assertTrue(res["action_result"]["success"])
        self.assertIn("RET-", res["action_result"]["return_request"]["request_id"])

    def test_payment_dispute_escalation(self):
        res = run_support_workflow("Payment was deducted for order ORD1004 but the order failed!", session_id="test-pay-esc")
        self.assertEqual(res["decision"], "escalated")
        self.assertIsNotNone(res["ticket"])
        self.assertEqual(res["ticket"]["category"], "payment_issue")
        self.assertIn("TKT-", res["ticket"]["ticket_id"])

    def test_explicit_human_agent_escalation(self):
        res = run_support_workflow("I want to speak with a human manager right now", session_id="test-human-esc")
        self.assertEqual(res["decision"], "escalated")
        self.assertIsNotNone(res["ticket"])
        self.assertIn("TKT-", res["ticket"]["ticket_id"])

    def test_general_policy_guidance(self):
        res = run_support_workflow("What is your cancellation policy?", session_id="test-kb-1")
        self.assertEqual(res["intent"], "cancellation")
        self.assertIn("Order Cancellation Policy", res["assistant_message"])
        self.assertGreaterEqual(len(res["knowledge_results"]), 1)


if __name__ == "__main__":
    unittest.main()
