"""Unit and integration tests for the Ticket Generation Agent (Component 8).

Covers:
1. Escalated issue produces a ticket
2. Ordinary inquiry does not create a ticket
3. Human-review-required issue produces a ticket
4. Relevant order information is included only when verified
5. Customer claims are distinguished from verified facts
6. Existing open ticket is reused for the same issue
7. Unrelated issues do not get incorrectly merged
8. Repeated turns do not create duplicate tickets
9. Gemini failure and malformed output use deterministic fallback
10. Existing ticket routes and ChatResponse remain compatible
11. Ticket generation never executes an action
"""

import copy
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.mock_data import ORDERS, PAYMENTS, reset_mock_data
from backend.ticket_service import create_ticket, list_tickets, clear_tickets, get_ticket
from backend.agents.ticket_generation_agent import (
    TicketGenerationAgent,
    TicketGenerationResult,
    LLMTicketSummaryOutput,
    generate_support_ticket,
)
from backend.agents.multi_turn_memory_agent import clear_memory_store
from backend.support_workflow import run_support_workflow
from backend.schemas import ChatResponse
from backend.main import app


def _get_mock_order(order_id: str):
    """Helper to retrieve a deep copy of an order from mock data."""
    order = next((o for o in ORDERS if o["id"] == order_id), None)
    return copy.deepcopy(order) if order else None


class TestTicketGenerationAgent(unittest.TestCase):
    """Test suite for the Ticket Generation Agent (Component 8)."""

    def setUp(self):
        clear_tickets()
        clear_memory_store()
        reset_mock_data()
        self.agent = TicketGenerationAgent()
        self.client = TestClient(app)

    def tearDown(self):
        clear_tickets()
        clear_memory_store()
        reset_mock_data()

    def test_escalated_issue_produces_ticket(self):
        """1. Escalated issue produces a valid structured ticket with proper metadata."""
        escalation_data = {
            "should_escalate": True,
            "requires_human_review": True,
            "escalation_reason": "Payment deducted for failed order ORD1004",
            "priority": "urgent",
            "target_team": "billing_support",
            "category": "payment_issue",
        }
        investigation_data = {
            "status": "found",
            "order_id": "ORD1004",
            "order": _get_mock_order("ORD1004"),
            "summary": "Order ORD1004 payment failed, charged $49.99.",
        }

        result = self.agent.generate_ticket(
            message="Payment was deducted for ORD1004 but my order failed! Please help!",
            session_id="session-test-1",
            intent="payment_issue",
            escalation=escalation_data,
            investigation=investigation_data,
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, TicketGenerationResult)
        self.assertTrue(result.ticket_id.startswith("TKT-"))
        self.assertEqual(result.session_id, "session-test-1")
        self.assertEqual(result.order_id, "ORD1004")
        self.assertEqual(result.priority, "urgent")
        self.assertEqual(result.target_team, "billing_support")
        self.assertEqual(result.status, "open")
        self.assertFalse(result.is_reused)
        self.assertIn("ORD1004", result.title)
        self.assertIn("ORD1004", result.customer_safe_summary)

        # Ticket should now exist in ticket_service store
        all_tickets = list_tickets()
        self.assertEqual(len(all_tickets), 1)
        self.assertEqual(all_tickets[0]["ticket_id"], result.ticket_id)

    def test_ordinary_inquiry_does_not_create_ticket(self):
        """2. Standard inquiries without escalation or human review requirement do not create tickets."""
        escalation_data = {
            "should_escalate": False,
            "requires_human_review": False,
            "escalation_reason": None,
            "priority": "low",
            "target_team": "general_support",
        }
        investigation_data = {
            "status": "found",
            "order_id": "ORD1001",
            "order": _get_mock_order("ORD1001"),
            "summary": "Order ORD1001 is delivered.",
        }

        result = self.agent.generate_ticket(
            message="Where is my order ORD1001?",
            session_id="session-test-2",
            intent="order_tracking",
            escalation=escalation_data,
            investigation=investigation_data,
        )

        self.assertIsNone(result)
        self.assertEqual(len(list_tickets()), 0)

    def test_human_review_required_issue_produces_ticket(self):
        """3. Issue requiring human review produces a ticket even if should_escalate is False."""
        escalation_data = {
            "should_escalate": False,
            "requires_human_review": True,
            "escalation_reason": "Custom policy exception review requested by customer.",
            "priority": "medium",
            "target_team": "policy_exceptions",
            "category": "return_or_replacement",
        }

        result = self.agent.generate_ticket(
            message="I want an exception to the 30-day return policy for my item.",
            session_id="session-test-3",
            intent="return_or_replacement",
            escalation=escalation_data,
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, TicketGenerationResult)
        self.assertEqual(result.target_team, "policy_exceptions")
        self.assertEqual(len(list_tickets()), 1)

    def test_relevant_order_information_included_only_when_verified(self):
        """4. Order details are attached only when officially verified in database records."""
        # Unverified order
        investigation_unverified = {
            "status": "order_not_found",
            "order_id": "ORD9999",
            "order": None,
        }
        escalation_data = {
            "should_escalate": True,
            "requires_human_review": True,
            "escalation_reason": "Customer inquiry about missing order",
            "priority": "medium",
            "target_team": "general_support",
        }

        result_unverified = self.agent.generate_ticket(
            message="My order ORD9999 is missing, help!",
            session_id="session-test-4a",
            intent="order_tracking",
            escalation=escalation_data,
            investigation=investigation_unverified,
        )

        self.assertIsNotNone(result_unverified)
        self.assertIsNone(result_unverified.order_id)
        # Customer claims record the claimed order ID
        self.assertTrue(any("ORD9999" in str(claim) for claim in result_unverified.customer_claims))
        # Verified facts must NOT list order ORD9999 as verified
        self.assertTrue(any("NOT found" in str(fact) for fact in result_unverified.verified_facts))

        # Verified order
        investigation_verified = {
            "status": "found",
            "order_id": "ORD1002",
            "order": _get_mock_order("ORD1002"),
        }
        result_verified = self.agent.generate_ticket(
            message="Package damaged for order ORD1002",
            session_id="session-test-4b",
            intent="return_or_replacement",
            escalation=escalation_data,
            investigation=investigation_verified,
        )

        self.assertIsNotNone(result_verified)
        self.assertEqual(result_verified.order_id, "ORD1002")
        self.assertTrue(any("ORD1002" in str(fact) for fact in result_verified.verified_facts))

    def test_customer_claims_distinguished_from_verified_facts(self):
        """5. Customer claims are partitioned from verified database facts."""
        investigation_data = {
            "status": "found",
            "order_id": "ORD1001",
            "order": _get_mock_order("ORD1001"),
            "summary": "Order ORD1001 status is delivered.",
        }
        customer_ctx = {
            "customer_id": "CUST001",
            "verification_status": "verified_account",
        }
        escalation_data = {
            "should_escalate": True,
            "escalation_reason": "Customer claims never received package despite delivery status.",
            "priority": "high",
            "target_team": "logistics_support",
        }

        user_msg = "I never received order ORD1001 even though your site says delivered! I demand a refund!"
        result = self.agent.generate_ticket(
            message=user_msg,
            session_id="session-test-5",
            intent="order_tracking",
            escalation=escalation_data,
            investigation=investigation_data,
            customer_context=customer_ctx,
        )

        self.assertIsNotNone(result)
        # Claims list user's statement
        self.assertTrue(any(user_msg in str(claim) for claim in result.customer_claims))
        # Verified facts list official database state
        self.assertTrue(any("ORD1001" in str(fact) and "delivered" in str(fact) for fact in result.verified_facts))
        self.assertTrue(any("CUST001" in str(fact) for fact in result.verified_facts))
        self.assertIn("Verified facts", result.internal_notes)

    def test_existing_open_ticket_reused_for_same_issue(self):
        """6. Existing open or in-progress ticket for the same issue in the same session is reused."""
        escalation_data = {
            "should_escalate": True,
            "escalation_reason": "Payment dispute",
            "priority": "urgent",
            "target_team": "billing_support",
            "category": "payment_issue",
        }
        investigation_data = {
            "status": "found",
            "order_id": "ORD1004",
            "order": _get_mock_order("ORD1004"),
        }

        # First turn: creates ticket
        first_res = self.agent.generate_ticket(
            message="Payment deducted for failed order ORD1004",
            session_id="session-same-issue",
            intent="payment_issue",
            escalation=escalation_data,
            investigation=investigation_data,
        )
        self.assertIsNotNone(first_res)
        self.assertFalse(first_res.is_reused)
        original_tkt_id = first_res.ticket_id
        self.assertEqual(len(list_tickets()), 1)

        # Second turn: same issue in same session
        second_res = self.agent.generate_ticket(
            message="Still waiting on update for ORD1004 payment!",
            session_id="session-same-issue",
            intent="payment_issue",
            escalation=escalation_data,
            investigation=investigation_data,
        )
        self.assertIsNotNone(second_res)
        self.assertTrue(second_res.is_reused)
        self.assertEqual(second_res.ticket_id, original_tkt_id)
        self.assertEqual(len(list_tickets()), 1)  # No duplicate ticket created

    def test_unrelated_issues_do_not_get_incorrectly_merged(self):
        """7. Different, unrelated issues in the same session get separate tickets."""
        # Issue 1: Payment issue on ORD1004
        res1 = self.agent.generate_ticket(
            message="Payment failed for ORD1004",
            session_id="session-multi-issue",
            intent="payment_issue",
            escalation={
                "should_escalate": True,
                "category": "payment_issue",
                "escalation_reason": "Payment failure",
                "target_team": "billing_support",
            },
            investigation={
                "status": "found",
                "order_id": "ORD1004",
                "order": _get_mock_order("ORD1004"),
            },
        )
        self.assertIsNotNone(res1)
        self.assertEqual(len(list_tickets()), 1)

        # Issue 2: Completely unrelated technical / account lockout inquiry (no order ID, different category)
        res2 = self.agent.generate_ticket(
            message="My 2FA token is broken and I am locked out of my account entirely!",
            session_id="session-multi-issue",
            intent="account_access",
            escalation={
                "should_escalate": True,
                "category": "account_access",
                "escalation_reason": "Security lockout",
                "target_team": "security_team",
            },
            investigation={"status": "order_id_required"},
        )
        self.assertIsNotNone(res2)
        self.assertFalse(res2.is_reused)
        self.assertNotEqual(res1.ticket_id, res2.ticket_id)
        self.assertEqual(len(list_tickets()), 2)

    def test_repeated_turns_do_not_create_duplicate_tickets(self):
        """8. Repeated turns in workflow reuse open ticket without duplicating records."""
        # Turn 1
        resp1 = run_support_workflow(
            "Payment deducted for order ORD1004 but order failed",
            session_id="session-turn-test",
        )
        self.assertEqual(resp1.get("decision"), "escalated")
        tkt1 = resp1.get("ticket")
        self.assertIsNotNone(tkt1)
        tkt_id = tkt1.get("ticket_id")
        self.assertEqual(len(list_tickets()), 1)

        # Turn 2: User follows up with escalation request in same session
        resp2 = run_support_workflow(
            "Payment failed for order ORD1004, please connect me to a human specialist",
            session_id="session-turn-test",
        )
        self.assertEqual(resp2.get("decision"), "escalated")
        tkt2 = resp2.get("ticket")
        self.assertIsNotNone(tkt2)
        self.assertEqual(tkt2.get("ticket_id"), tkt_id)
        # Verify no duplicate was added to ticket store
        self.assertEqual(len(list_tickets()), 1)

    def test_gemini_failure_and_malformed_output_use_deterministic_fallback(self):
        """9. Gemini failure and invalid output gracefully fall back to deterministic generation."""
        mock_llm_exception = MagicMock()
        mock_llm_exception.with_structured_output.side_effect = Exception("Gemini 429 Quota Exceeded")

        agent_fallback = TicketGenerationAgent(llm=mock_llm_exception)
        res = agent_fallback.generate_ticket(
            message="Connect me with a supervisor right now!",
            session_id="session-fallback",
            intent="general_inquiry",
            escalation={
                "should_escalate": True,
                "escalation_reason": "Customer demands supervisor",
                "priority": "high",
                "target_team": "support_supervisors",
            },
        )
        self.assertIsNotNone(res)
        self.assertIn("deterministic", res.generation_source)
        self.assertIn("Customer demands supervisor", res.title)

        # Malformed model output
        mock_llm_malformed = MagicMock()
        structured_mock = MagicMock()
        structured_mock.invoke.return_value = "Non-model string"
        mock_llm_malformed.with_structured_output.return_value = structured_mock

        agent_malformed = TicketGenerationAgent(llm=mock_llm_malformed)
        res_malformed = agent_malformed.generate_ticket(
            message="Order ORD1004 is broken",
            session_id="session-malformed",
            intent="payment_issue",
            escalation={
                "should_escalate": True,
                "escalation_reason": "Payment issue",
                "priority": "urgent",
            },
        )
        self.assertIsNotNone(res_malformed)
        self.assertIn("deterministic", res_malformed.generation_source)

    def test_existing_ticket_routes_and_chat_response_remain_compatible(self):
        """10. Existing ticket routes (GET /tickets, GET /tickets/{id}) and ChatResponse remain compatible."""
        # Run workflow to generate a ticket
        chat_res = run_support_workflow(
            "Payment deducted for order ORD1004 but order failed",
            session_id="session-routes-test",
        )
        self.assertEqual(chat_res.get("decision"), "escalated")
        tkt = chat_res.get("ticket")
        self.assertIsNotNone(tkt)
        ticket_id = tkt["ticket_id"]

        # Validate that ChatResponse schema parses the response cleanly
        validated_chat = ChatResponse(**chat_res)
        self.assertIsNotNone(validated_chat.ticket)
        self.assertIsNotNone(validated_chat.ticket_generation)
        self.assertEqual(validated_chat.ticket_generation["ticket_id"], ticket_id)

        # Test GET /tickets/{id}
        response = self.client.get(f"/tickets/{ticket_id}")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["ticket_id"], ticket_id)
        self.assertEqual(body["session_id"], "session-routes-test")
        self.assertEqual(body["priority"], "urgent")
        self.assertIn("customer_safe_summary", body)

        # Test GET /tickets
        list_resp = self.client.get("/tickets")
        self.assertEqual(list_resp.status_code, 200)
        all_tkts = list_resp.json()
        self.assertTrue(any(t["ticket_id"] == ticket_id for t in all_tkts))

    def test_ticket_generation_never_executes_an_action(self):
        """11. Ticket generation never executes an order cancellation, return, or refund action."""
        initial_order_state = copy.deepcopy(ORDERS)
        initial_payments_state = copy.deepcopy(PAYMENTS)

        res = self.agent.generate_ticket(
            message="I want to cancel order ORD1001 immediately and demand a full refund!",
            session_id="session-no-action",
            intent="cancellation",
            escalation={
                "should_escalate": True,
                "escalation_reason": "Customer cancellation dispute",
                "priority": "high",
                "target_team": "cancellations_team",
            },
            investigation={
                "status": "found",
                "order_id": "ORD1001",
                "order": _get_mock_order("ORD1001"),
            },
        )

        self.assertIsNotNone(res)
        # Verify that ORDERS and PAYMENTS were not mutated
        self.assertEqual(ORDERS, initial_order_state)
        self.assertEqual(PAYMENTS, initial_payments_state)


if __name__ == "__main__":
    unittest.main()
