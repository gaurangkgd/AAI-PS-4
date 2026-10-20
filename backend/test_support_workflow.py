"""Unit tests for LangGraph support workflow coordination using unittest."""

import copy
import unittest

try:
    from backend.mock_data import ORDERS, PAYMENTS
    from backend.support_workflow import (
        build_support_graph,
        run_support_workflow,
        support_graph,
    )
    from backend.schemas import ChatRequest
    from backend.main import chat_endpoint
    from backend.ticket_service import clear_tickets, list_tickets
    from backend.action_service import clear_action_data, list_return_requests
except ImportError:
    from mock_data import ORDERS, PAYMENTS
    from support_workflow import (
        build_support_graph,
        run_support_workflow,
        support_graph,
    )
    from schemas import ChatRequest
    from main import chat_endpoint
    from ticket_service import clear_tickets, list_tickets
    from action_service import clear_action_data, list_return_requests


class TestSupportWorkflow(unittest.TestCase):
    def setUp(self):
        clear_tickets()
        clear_action_data()

    def tearDown(self):
        clear_tickets()
        clear_action_data()

    def test_graph_nodes_present(self):
        graph = build_support_graph().get_graph()
        expected_nodes = {
            "classify_intent_node",
            "retrieve_knowledge_node",
            "investigate_order_node",
            "decide_next_step_node",
            "execute_action_node",
            "escalate_node",
            "compose_response_node",
        }
        node_names = set(graph.nodes.keys())
        self.assertTrue(expected_nodes.issubset(node_names))

    def test_general_inquiry_does_not_create_ticket(self):
        result = run_support_workflow("Hello, what are your operating hours?")
        self.assertEqual(result["intent"], "general_inquiry")
        self.assertEqual(result["decision"], "knowledge_guidance")
        self.assertIn("Regarding your inquiry", result["assistant_message"])
        self.assertGreater(len(result["knowledge_results"]), 0)
        self.assertIsNone(result.get("ticket"))
        self.assertEqual(len(list_tickets()), 0)

    def test_known_order_id_verified_no_ticket(self):
        result = run_support_workflow("Where is my order ORD1001?")
        self.assertEqual(result["intent"], "order_tracking")
        self.assertEqual(result["decision"], "order_found")
        self.assertIn("verified status", result["assistant_message"])
        self.assertIn("ORD1001", result["assistant_message"])
        self.assertIn("delivered", result["assistant_message"])
        self.assertIsNotNone(result["investigation"])
        self.assertEqual(result["investigation"]["status"], "found")
        self.assertIsNone(result.get("ticket"))
        self.assertEqual(len(list_tickets()), 0)

    def test_missing_order_id_requests_order_no_ticket(self):
        result = run_support_workflow("Where is my order? Please track my shipment.")
        self.assertEqual(result["intent"], "order_tracking")
        self.assertEqual(result["decision"], "order_id_required")
        self.assertIn("provide your Order ID", result["assistant_message"])
        self.assertEqual(result["investigation"]["status"], "order_id_required")
        self.assertIsNone(result.get("ticket"))
        self.assertEqual(len(list_tickets()), 0)

    def test_missing_order_id_for_cancellation_prompts_customer(self):
        result = run_support_workflow("I want to cancel my order please")
        self.assertEqual(result["intent"], "cancellation")
        self.assertEqual(result["decision"], "order_id_required")
        self.assertIn("provide your Order ID", result["assistant_message"])
        self.assertIsNone(result.get("action_result"))
        self.assertIsNone(result.get("ticket"))

    def test_unknown_order_id_not_found(self):
        result = run_support_workflow("Can you check order ORD9999?")
        self.assertEqual(result["decision"], "order_not_found")
        self.assertIn("could not find any records for order ID 'ORD9999'", result["assistant_message"])
        self.assertEqual(result["investigation"]["status"], "order_not_found")

    def test_payment_failure_escalates_and_creates_ticket(self):
        initial_ticket_count = len(list_tickets())
        result = run_support_workflow("Payment deducted for order ORD1004 but order failed")
        self.assertEqual(result["intent"], "payment_issue")
        self.assertEqual(result["decision"], "escalated")
        self.assertIsNotNone(result.get("ticket"))
        self.assertTrue(result["ticket"]["ticket_id"].startswith("TKT-"))
        self.assertIn("referred for human support review", result["assistant_message"])
        self.assertIn(result["ticket"]["ticket_id"], result["assistant_message"])
        self.assertIn("TXN-909012-FAILED", result["assistant_message"])

        # Exactly 1 ticket created
        self.assertEqual(len(list_tickets()), initial_ticket_count + 1)

    def test_cancel_processing_order_via_workflow(self):
        # ORD1002 is processing
        result = run_support_workflow("Please cancel my order ORD1002")
        self.assertEqual(result["intent"], "cancellation")
        self.assertEqual(result["decision"], "action_completed")
        self.assertIsNotNone(result.get("action_result"))
        self.assertTrue(result["action_result"]["success"])
        self.assertIn("successfully cancelled", result["assistant_message"])
        self.assertIsNone(result.get("ticket"))

        # Verify underlying order state updated
        ord1002 = next(o for o in ORDERS if o["id"] == "ORD1002")
        self.assertEqual(ord1002["status"], "cancelled")

    def test_cancel_delivered_order_rejected_via_workflow(self):
        # ORD1001 is delivered
        result = run_support_workflow("Please cancel my order ORD1001")
        self.assertEqual(result["intent"], "cancellation")
        self.assertEqual(result["decision"], "action_rejected")
        self.assertIsNotNone(result.get("action_result"))
        self.assertFalse(result["action_result"]["success"])
        self.assertIn("already been delivered", result["assistant_message"])
        self.assertIsNone(result.get("ticket"))

    def test_return_delivered_order_via_workflow(self):
        # ORD1001 is delivered
        result = run_support_workflow("I received a damaged product for order ORD1001, please start a return")
        self.assertEqual(result["intent"], "return_or_replacement")
        self.assertEqual(result["decision"], "action_completed")
        self.assertIsNotNone(result.get("action_result"))
        self.assertTrue(result["action_result"]["success"])
        ret_id = result["action_result"]["return_request"]["request_id"]
        self.assertTrue(ret_id.startswith("RET-"))
        self.assertIn(ret_id, result["assistant_message"])
        self.assertEqual(len(list_return_requests("ORD1001")), 1)

    def test_insufficient_evidence_handled(self):
        result = run_support_workflow("xyz123 meaningless gibberish input")
        self.assertEqual(result["decision"], "insufficient_evidence")
        self.assertIn("could not find specific information", result["assistant_message"])

    def test_no_data_mutation_on_tracking(self):
        initial_orders = copy.deepcopy(ORDERS)
        initial_payments = copy.deepcopy(PAYMENTS)

        run_support_workflow("Where is my order ORD1001?")
        self.assertEqual(ORDERS, initial_orders)
        self.assertEqual(PAYMENTS, initial_payments)

    def test_chat_endpoint_uses_workflow(self):
        req = ChatRequest(message="Where is order ORD1002?", session_id="workflow-sess-1")
        resp = chat_endpoint(req)
        self.assertEqual(resp.session_id, "workflow-sess-1")
        self.assertEqual(resp.intent, "order_tracking")
        self.assertEqual(resp.decision, "order_found")
        self.assertIn("ORD1002", resp.assistant_message)
        self.assertIn("processing", resp.assistant_message)


if __name__ == "__main__":
    unittest.main()
