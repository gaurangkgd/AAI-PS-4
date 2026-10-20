"""Unit tests for the Action Execution Agent in PS-04 Agentic Customer Support System."""

import copy
import unittest
from unittest.mock import patch

try:
    from backend.agents.action_execution_agent import (
        ActionExecutionAgent,
        ActionExecutionResult,
        execute_support_action,
    )
    from backend.action_service import clear_action_data, list_return_requests
    from backend.mock_data import ORDERS, PAYMENTS
    from backend.support_workflow import run_support_workflow
except ImportError:
    from agents.action_execution_agent import (
        ActionExecutionAgent,
        ActionExecutionResult,
        execute_support_action,
    )
    from action_service import clear_action_data, list_return_requests
    from mock_data import ORDERS, PAYMENTS
    from support_workflow import run_support_workflow


class TestActionExecutionAgent(unittest.TestCase):
    """Test suite verifying safe action execution, business rule enforcement, and privacy isolation."""

    def setUp(self):
        clear_action_data()
        self.agent = ActionExecutionAgent()

    def tearDown(self):
        clear_action_data()

    def test_eligible_order_cancellation_mutates_and_reports_execution(self):
        """Cancelling processing order (ORD1002) should succeed, mutate status, and report mutation_performed=True."""
        # Initial check
        ord1002 = next(o for o in ORDERS if o["id"] == "ORD1002")
        self.assertEqual(ord1002["status"], "processing")

        result = self.agent.execute(
            action="cancellation",
            order_id="ORD1002",
            message="Please cancel my order ORD1002 immediately",
        )

        self.assertIsInstance(result, ActionExecutionResult)
        self.assertTrue(result.is_supported)
        self.assertTrue(result.is_eligible)
        self.assertEqual(result.status, "executed")
        self.assertTrue(result.mutation_performed)
        self.assertEqual(result.order_id, "ORD1002")
        self.assertIn("successfully cancelled", result.message)

        # Confirm underlying mock data actually changed to cancelled
        updated_ord = next(o for o in ORDERS if o["id"] == "ORD1002")
        self.assertEqual(updated_ord["status"], "cancelled")

    def test_ineligible_order_cancellation_rejected_without_mutation(self):
        """Cancelling shipped order (ORD1003) or delivered order (ORD1001) must be rejected with mutation_performed=False."""
        # 1. Shipped order ORD1003
        res_shipped = self.agent.execute(
            action="cancellation",
            order_id="ORD1003",
            message="Cancel order ORD1003",
        )
        self.assertFalse(res_shipped.is_eligible)
        self.assertEqual(res_shipped.status, "rejected")
        self.assertFalse(res_shipped.mutation_performed)
        self.assertIn("already shipped", res_shipped.message)
        ord1003 = next(o for o in ORDERS if o["id"] == "ORD1003")
        self.assertEqual(ord1003["status"], "shipped")

        # 2. Delivered order ORD1001
        res_deliv = self.agent.execute(
            action="cancellation",
            order_id="ORD1001",
            message="Cancel order ORD1001",
        )
        self.assertFalse(res_deliv.is_eligible)
        self.assertEqual(res_deliv.status, "rejected")
        self.assertFalse(res_deliv.mutation_performed)
        self.assertIn("already been delivered", res_deliv.message)

    def test_eligible_return_request_creates_record_and_reports_execution(self):
        """Return request for delivered order (ORD1001) creates return request and reports mutation_performed=True."""
        result = self.agent.execute(
            action="return_or_replacement",
            order_id="ORD1001",
            message="I need to return order ORD1001 because the headphones are defective",
            request_type="return",
            reason="Defective headphones",
        )

        self.assertTrue(result.is_supported)
        self.assertTrue(result.is_eligible)
        self.assertEqual(result.status, "executed")
        self.assertTrue(result.mutation_performed)
        self.assertIsNotNone(result.action_id)
        self.assertTrue(result.action_id.startswith("RET-"))

        # Verify record exists in return requests
        returns = list_return_requests("ORD1001")
        self.assertEqual(len(returns), 1)
        self.assertEqual(returns[0]["request_id"], result.action_id)

    def test_ineligible_return_request_rejected(self):
        """Return request for processing order (ORD1002) is rejected with mutation_performed=False."""
        result = self.agent.execute(
            action="return_or_replacement",
            order_id="ORD1002",
            message="Return order ORD1002",
        )
        self.assertFalse(result.is_eligible)
        self.assertEqual(result.status, "rejected")
        self.assertFalse(result.mutation_performed)
        self.assertIn("only permitted for 'delivered' orders", result.message)

    def test_missing_or_unknown_order_id_rejected(self):
        """Missing order ID or unknown order ID (ORD9999) rejected safely."""
        # Missing
        res_missing = self.agent.execute(action="cancellation", order_id=None)
        self.assertFalse(res_missing.is_eligible)
        self.assertEqual(res_missing.status, "rejected")
        self.assertFalse(res_missing.mutation_performed)

        # Unknown
        res_unknown = self.agent.execute(action="cancellation", order_id="ORD9999")
        self.assertFalse(res_unknown.is_eligible)
        self.assertEqual(res_unknown.status, "rejected")
        self.assertFalse(res_unknown.mutation_performed)
        self.assertIn("was not found", res_unknown.message)

    def test_ambiguous_customer_context_blocks_execution(self):
        """When customer context is flagged as ambiguous, execution is refused for safety."""
        ambiguous_context = {
            "customer_id": None,
            "is_ambiguous": True,
            "needs_clarification": True,
        }
        result = self.agent.execute(
            action="cancellation",
            order_id="ORD1002",
            customer_context=ambiguous_context,
        )
        self.assertFalse(result.is_eligible)
        self.assertEqual(result.status, "rejected")
        self.assertFalse(result.mutation_performed)
        self.assertIn("ambiguous", result.message.lower())

    def test_customer_ownership_mismatch_blocks_execution(self):
        """Customer CUST002 trying to cancel order ORD1002 belonging to CUST001 must be refused."""
        mismatched_context = {
            "customer_id": "CUST002",
            "is_ambiguous": False,
        }
        result = self.agent.execute(
            action="cancellation",
            order_id="ORD1002",  # Belongs to CUST001
            customer_context=mismatched_context,
        )
        self.assertFalse(result.is_eligible)
        self.assertEqual(result.status, "rejected")
        self.assertFalse(result.mutation_performed)
        self.assertIn("does not belong to verified customer", result.message)

    def test_unsupported_action_requests_rejected(self):
        """Unsupported actions like refund or change address must be rejected without mutation."""
        for unsupported_act in ["refund", "payment_reversal", "change_address", "delete_account"]:
            result = self.agent.execute(
                action=unsupported_act,
                order_id="ORD1001",
                message=f"Please {unsupported_act} for my order ORD1001",
            )
            self.assertFalse(result.is_supported)
            self.assertFalse(result.is_eligible)
            self.assertEqual(result.status, "unsupported")
            self.assertFalse(result.mutation_performed)
            self.assertIn("not supported", result.message.lower())

    def test_confirmation_required_for_hypothetical_inquiry(self):
        """Hypothetical inquiry like 'Can I cancel order ORD1002?' triggers confirmation_required without mutating."""
        result = self.agent.execute(
            action="cancellation",
            order_id="ORD1002",
            message="Can I cancel my order ORD1002 please?",
        )
        self.assertTrue(result.is_supported)
        self.assertTrue(result.is_eligible)
        self.assertTrue(result.needs_confirmation)
        self.assertEqual(result.status, "confirmation_required")
        self.assertFalse(result.mutation_performed)
        self.assertIn("Please confirm", result.message)

        # Order ORD1002 must remain in 'processing' status
        ord1002 = next(o for o in ORDERS if o["id"] == "ORD1002")
        self.assertEqual(ord1002["status"], "processing")

    def test_duplicate_active_return_request_prevented(self):
        """Submitting a second return request for the same order ORD1001 must be rejected idempotently."""
        # 1. First return succeeds
        res1 = self.agent.execute(
            action="return_or_replacement",
            order_id="ORD1001",
            request_type="return",
        )
        self.assertTrue(res1.mutation_performed)
        self.assertEqual(res1.status, "executed")

        # 2. Second return request is rejected
        res2 = self.agent.execute(
            action="return_or_replacement",
            order_id="ORD1001",
            request_type="replacement",
        )
        self.assertFalse(res2.mutation_performed)
        self.assertEqual(res2.status, "rejected")
        self.assertIn("already exists", res2.message)

    def test_service_failure_handled_gracefully(self):
        """Unexpected service exception is captured and returned with status='failed' and mutation_performed=False."""
        with patch("backend.agents.action_execution_agent.cancel_order", side_effect=RuntimeError("Database lock")):
            result = self.agent.execute(
                action="cancellation",
                order_id="ORD1002",
                message="Cancel order ORD1002",
            )
            self.assertEqual(result.status, "failed")
            self.assertFalse(result.mutation_performed)
            self.assertIn("failed", result.message.lower())

    def test_ensures_no_real_payment_or_refund_is_performed(self):
        """PAYMENTS table must never be modified by action execution."""
        payments_snapshot = copy.deepcopy(PAYMENTS)

        self.agent.execute(
            action="cancellation",
            order_id="ORD1002",
            message="Cancel order ORD1002 and refund full amount",
        )

        self.assertEqual(PAYMENTS, payments_snapshot)

    def test_workflow_integration_preserves_contract_and_populates_action_execution(self):
        """Full support workflow execution produces valid action_execution metadata and preserves ChatResponse contract."""
        chat_res = run_support_workflow("Please cancel my order ORD1002")

        self.assertEqual(chat_res["intent"], "cancellation")
        self.assertEqual(chat_res["decision"], "action_completed")
        self.assertIsNotNone(chat_res["action_result"])
        self.assertTrue(chat_res["action_result"]["success"])

        # Check action_execution metadata
        ae = chat_res.get("action_execution")
        self.assertIsNotNone(ae)
        self.assertEqual(ae["action"], "cancellation")
        self.assertEqual(ae["status"], "executed")
        self.assertTrue(ae["mutation_performed"])
        self.assertEqual(ae["order_id"], "ORD1002")
        self.assertEqual(ae["execution_mode"], "service_backed_deterministic")


if __name__ == "__main__":
    unittest.main()
