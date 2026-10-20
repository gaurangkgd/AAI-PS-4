"""Unit tests for the Customer Context Agent.

Covers:
- Known customer context (direct mention and order inference)
- Missing or unverified customer identity
- Relevant order history retrieval
- Existing ticket context retrieval
- Unknown customer IDs (no history)
- Ambiguity detection and conflict resolution without guessing
- Prevention of cross-customer data exposure
- Missing or unavailable data handling
- Read-only execution with zero data mutation
- End-to-end integration into support workflow
"""

import copy
import unittest

from backend.mock_data import ORDERS, reset_mock_data
from backend.ticket_service import create_ticket, clear_tickets
from backend.agents.customer_context_agent import (
    CustomerContextAgent,
    CustomerContextResult,
    resolve_customer_context,
)
from backend.support_workflow import run_support_workflow


class TestCustomerContextAgent(unittest.TestCase):
    """Test suite for CustomerContextAgent."""

    def setUp(self):
        clear_tickets()
        reset_mock_data()
        self.agent = CustomerContextAgent()

    def tearDown(self):
        clear_tickets()
        reset_mock_data()

    def test_known_customer_from_direct_id(self):
        """When customer ID is mentioned directly, retrieve only their orders."""
        result = self.agent.resolve_context("Hello, I am customer CUST001")

        self.assertIsInstance(result, CustomerContextResult)
        self.assertEqual(result.customer_id, "CUST001")
        self.assertFalse(result.is_authenticated)
        self.assertEqual(result.verification_status, "unverified_self_reported")
        self.assertEqual(result.identified_from, "customer_id_mention")
        self.assertFalse(result.is_ambiguous)
        self.assertFalse(result.needs_clarification)
        self.assertEqual(set(result.order_ids), {"ORD1001", "ORD1002"})
        self.assertEqual(len(result.orders), 2)
        self.assertIn("CUST001", result.summary)

    def test_known_customer_inferred_from_order(self):
        """When order ID is mentioned without customer ID, infer customer safely."""
        result = self.agent.resolve_context("Can you give me an update on ORD1003?")

        self.assertEqual(result.customer_id, "CUST002")
        self.assertFalse(result.is_authenticated)
        self.assertEqual(result.verification_status, "inferred_from_order")
        self.assertEqual(result.identified_from, "order_lookup")
        self.assertEqual(result.active_order_id, "ORD1003")
        self.assertIn("ORD1003", result.order_ids)
        self.assertNotIn("ORD1001", result.order_ids)

    def test_missing_unidentified_customer(self):
        """When no customer ID or order ID is present, return clean unidentified context."""
        result = self.agent.resolve_context("What are your return and refund policies?")

        self.assertIsNone(result.customer_id)
        self.assertFalse(result.is_authenticated)
        self.assertEqual(result.verification_status, "unidentified")
        self.assertEqual(result.identified_from, "none")
        self.assertFalse(result.is_ambiguous)
        self.assertFalse(result.needs_clarification)
        self.assertEqual(result.order_ids, [])
        self.assertEqual(result.orders, [])
        self.assertEqual(result.tickets, [])
        self.assertIn("unauthenticated", result.summary.lower())

    def test_unknown_customer_id(self):
        """When self-reported customer ID does not exist in records, state is unknown_customer."""
        result = self.agent.resolve_context("My customer account is CUST999")

        self.assertEqual(result.customer_id, "CUST999")
        self.assertFalse(result.is_authenticated)
        self.assertEqual(result.verification_status, "unknown_customer")
        self.assertEqual(result.order_ids, [])
        self.assertEqual(result.orders, [])
        self.assertEqual(result.tickets, [])
        self.assertIn("no matching order or ticket", result.summary.lower())

    def test_existing_ticket_context_retrieval(self):
        """Existing support tickets for the identified customer are included."""
        ticket = create_ticket(
            session_id="session-123",
            original_message="Payment failed for order",
            category="payment_issue",
            escalation_reason="Billing inquiry",
            customer_id="CUST001",
            priority="high",
        )

        result = self.agent.resolve_context("Status for customer CUST001")

        self.assertEqual(len(result.tickets), 1)
        self.assertEqual(result.tickets[0]["ticket_id"], ticket["ticket_id"])
        self.assertEqual(result.tickets[0]["category"], "payment_issue")
        self.assertEqual(result.tickets[0]["priority"], "high")

    def test_ambiguous_multiple_customer_ids(self):
        """Multiple conflicting customer IDs trigger ambiguity and clarification requirement."""
        result = self.agent.resolve_context("I am CUST001 but asking on behalf of CUST002")

        self.assertIsNone(result.customer_id)
        self.assertTrue(result.is_ambiguous)
        self.assertTrue(result.needs_clarification)
        self.assertEqual(result.verification_status, "ambiguous")
        self.assertEqual(result.orders, [])
        self.assertIn("conflicting customer ids", result.summary.lower())

    def test_ambiguous_customer_and_order_mismatch(self):
        """Cross-account order mismatch triggers ambiguity to protect privacy."""
        # ORD1003 belongs to CUST002, but message claims CUST001
        result = self.agent.resolve_context("I am CUST001 and my order is ORD1003")

        self.assertIsNone(result.customer_id)
        self.assertTrue(result.is_ambiguous)
        self.assertTrue(result.needs_clarification)
        self.assertEqual(result.verification_status, "ambiguous")
        self.assertEqual(result.orders, [])
        self.assertIn("conflicting identity", result.summary.lower())

    def test_prevent_cross_customer_data_exposure(self):
        """Ensure customer context strictly isolates data between different customers."""
        res_cust1 = self.agent.resolve_context("Customer CUST001")
        res_cust2 = self.agent.resolve_context("Customer CUST002")
        res_cust3 = self.agent.resolve_context("Customer CUST003")

        self.assertEqual(set(res_cust1.order_ids), {"ORD1001", "ORD1002"})
        self.assertEqual(set(res_cust2.order_ids), {"ORD1003"})
        self.assertEqual(set(res_cust3.order_ids), {"ORD1004"})

        # No intersection between customer orders
        self.assertEqual(set(res_cust1.order_ids).intersection(set(res_cust2.order_ids)), set())
        self.assertEqual(set(res_cust2.order_ids).intersection(set(res_cust3.order_ids)), set())

    def test_read_only_no_data_mutation(self):
        """Resolving customer context must not mutate mock orders or create tickets."""
        initial_orders = copy.deepcopy(ORDERS)

        self.agent.resolve_context("Where is ORD1001 for CUST001?")
        self.agent.resolve_context("Please check CUST002 and ORD1003")
        self.agent.resolve_context("Cancel order ORD1002")

        # In-memory orders must remain identical
        self.assertEqual(ORDERS, initial_orders)

    def test_workflow_integration_returns_customer_context(self):
        """LangGraph workflow output includes the structured customer_context payload."""
        result = run_support_workflow("Where is my order ORD1001?")

        self.assertIn("customer_context", result)
        ctx = result["customer_context"]
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx["customer_id"], "CUST001")
        self.assertEqual(ctx["verification_status"], "inferred_from_order")
        self.assertIn("ORD1001", ctx["order_ids"])


if __name__ == "__main__":
    unittest.main()
