"""Unit and integration tests for the Escalation Decision Agent (Component 7).

Covers:
- Normal inquiry that does not need escalation
- Explicit human-support or supervisor requests
- High-frustration or negative-sentiment cases
- Unresolved troubleshooting cases (suggest_escalation=True)
- Payment or refund issues requiring human review under policy
- Insufficient or conflicting information handling
- Gemini failure and deterministic fallback
- Invalid Gemini output handling
- Hard safety rules overriding model's recommendation against escalation
- Ticket creation and duplicate prevention across turns
- Compatibility with existing workflow and response schema
"""

import copy
import unittest
from unittest.mock import MagicMock, patch

from backend.mock_data import ORDERS, PAYMENTS, reset_mock_data
from backend.ticket_service import create_ticket, list_tickets, clear_tickets
from backend.agents.escalation_decision_agent import (
    EscalationDecisionAgent,
    EscalationDecisionResult,
    LLMEscalationOutput,
    decide_escalation,
)
from backend.agents.multi_turn_memory_agent import clear_memory_store
from backend.support_workflow import run_support_workflow
from backend.schemas import ChatResponse


class TestEscalationDecisionAgent(unittest.TestCase):
    """Test suite for the Escalation Decision Agent."""

    def setUp(self):
        clear_tickets()
        clear_memory_store()
        reset_mock_data()
        self.agent = EscalationDecisionAgent()

    def tearDown(self):
        clear_tickets()
        clear_memory_store()
        reset_mock_data()

    def test_normal_inquiry_does_not_escalate(self):
        """Standard self-service order tracking or policy inquiries do not trigger escalation."""
        # Order tracking inquiry
        res_tracking = self.agent.decide(
            message="Where is my order ORD1001?",
            intent="order_tracking",
            investigation={"status": "found", "order_id": "ORD1001"},
        )
        self.assertIsInstance(res_tracking, EscalationDecisionResult)
        self.assertFalse(res_tracking.should_escalate)
        self.assertIsNone(res_tracking.escalation_reason)
        self.assertEqual(res_tracking.priority, "low")
        self.assertFalse(res_tracking.requires_human_review)
        self.assertIn("self-service", res_tracking.explanation)

        # Knowledge base policy inquiry
        res_policy = self.agent.decide(
            message="What is your return policy?",
            intent="return_or_replacement",
            knowledge_results=[{"id": "KB-RET-001", "title": "Return Policy"}],
        )
        self.assertFalse(res_policy.should_escalate)

    def test_explicit_human_support_request_escalates(self):
        """Explicit customer requests to speak with a human or agent mandate escalation."""
        res = self.agent.decide(
            message="I need to speak to a human representative right now",
            intent="general_inquiry",
        )
        self.assertTrue(res.should_escalate)
        self.assertEqual(res.target_team, "general_support")
        self.assertEqual(res.priority, "medium")
        self.assertTrue(res.requires_human_review)
        self.assertIn("human support representative", res.escalation_reason)

    def test_explicit_supervisor_request_escalates_to_senior_support(self):
        """Requests for a supervisor or manager escalate to senior support with high priority."""
        res = self.agent.decide(
            message="Please transfer me to a supervisor or manager immediately",
            intent="general_inquiry",
        )
        self.assertTrue(res.should_escalate)
        self.assertEqual(res.target_team, "senior_support")
        self.assertEqual(res.priority, "high")
        self.assertTrue(res.requires_human_review)
        self.assertIn("supervisor", res.escalation_reason)

    def test_payment_failure_mandates_billing_escalation(self):
        """Failed or pending payment records on verified orders require urgent billing escalation."""
        res = self.agent.decide(
            message="My card was charged but payment shows failed for ORD1004",
            intent="payment_issue",
            investigation={
                "status": "found",
                "order_id": "ORD1004",
                "order": {"id": "ORD1004", "status": "payment_failed"},
                "payments": [{"id": "PAY-004", "status": "failed", "amount": 89.99}],
            },
        )
        self.assertTrue(res.should_escalate)
        self.assertEqual(res.target_team, "billing_support")
        self.assertEqual(res.priority, "urgent")
        self.assertTrue(res.requires_human_review)
        self.assertIn("payment failure", res.escalation_reason.lower())

    def test_payment_deduction_for_unrecognized_order_escalates(self):
        """Payment issue for non-existent order ID escalates to billing support with high priority."""
        res = self.agent.decide(
            message="Money was debited from my bank for order ORD9999 but it's not showing",
            intent="payment_issue",
            investigation={
                "status": "order_not_found",
                "order_id": "ORD9999",
            },
        )
        self.assertTrue(res.should_escalate)
        self.assertEqual(res.target_team, "billing_support")
        self.assertEqual(res.priority, "high")
        self.assertIn("ORD9999", res.escalation_reason)

    def test_severe_customer_frustration_escalates(self):
        """Frustrated sentiment with severe dissatisfaction terms triggers senior support escalation."""
        res = self.agent.decide(
            message="This is completely unacceptable service, it is ridiculous and horrible!",
            intent="general_inquiry",
            understanding={"sentiment": "frustrated", "priority": "high"},
        )
        self.assertTrue(res.should_escalate)
        self.assertEqual(res.target_team, "senior_support")
        self.assertEqual(res.priority, "high")
        self.assertIn("frustration", res.escalation_reason.lower())

    def test_mild_dissatisfaction_alone_does_not_escalate(self):
        """Mild negative sentiment without hard blocker or severe frustration does not trigger escalation."""
        res = self.agent.decide(
            message="I'm slightly disappointed the shipping took an extra day",
            intent="order_tracking",
            understanding={"sentiment": "negative", "priority": "medium"},
            investigation={"status": "found", "order_id": "ORD1001"},
        )
        self.assertFalse(res.should_escalate)

    def test_unresolved_troubleshooting_diagnosis_escalates(self):
        """When Troubleshooting Agent diagnoses an unresolvable issue, escalation is triggered."""
        res = self.agent.decide(
            message="Why won't my payment go through?",
            intent="payment_issue",
            troubleshooting={
                "suggest_escalation": True,
                "diagnosis": "Card declined repeatedly due to merchant processing error.",
                "evidence": ["Transaction TXN-001 returned decline code 51"],
            },
        )
        self.assertTrue(res.should_escalate)
        self.assertEqual(res.target_team, "billing_support")
        self.assertIn("Card declined repeatedly", res.escalation_reason)

    def test_repeated_unsuccessful_turns_in_memory_escalates(self):
        """Multiple prior conversation turns with persistent failure trigger escalation."""
        res = self.agent.decide(
            message="I already told you that, it is still not working!",
            intent="account_issue",
            memory={"turn_count": 4, "recent_intents": ["account_issue", "account_issue", "account_issue"]},
        )
        self.assertTrue(res.should_escalate)
        self.assertEqual(res.target_team, "senior_support")
        self.assertEqual(res.priority, "high")
        self.assertIn("repeated unsuccessful", res.escalation_reason.lower())

    def test_gemini_failure_falls_back_to_deterministic_rules(self):
        """When Gemini model invocation raises an exception, fallback executes cleanly."""
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = RuntimeError("Google API Quota Exceeded (429)")

        agent = EscalationDecisionAgent(llm=mock_llm)
        res = agent.decide(
            message="I want to speak with a representative please",
            intent="general_inquiry",
        )
        self.assertTrue(res.should_escalate)
        self.assertEqual(res.decision_source, "deterministic_fallback")
        self.assertIn("human support representative", res.escalation_reason)

    def test_invalid_gemini_output_type_falls_back_cleanly(self):
        """When Gemini returns an unparseable object, fallback handles it safely."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "Just some unexpected raw string"

        agent = EscalationDecisionAgent(llm=mock_llm)
        res = agent.decide(
            message="Please connect me to an operator",
            intent="general_inquiry",
        )
        self.assertTrue(res.should_escalate)
        self.assertEqual(res.decision_source, "deterministic_fallback")

    def test_hard_safety_rule_overrides_gemini_recommendation(self):
        """If Gemini incorrectly advises not to escalate a payment failure, hard safety rule overrides it."""
        # Mock LLM claiming NO escalation is needed for a payment failure
        mock_output = LLMEscalationOutput(
            should_escalate=False,
            escalation_reason=None,
            priority="low",
            target_team="general_support",
            supporting_evidence=["Model incorrectly believed order was fine"],
            requires_human_review=False,
            explanation="Model hallucinated that self-service is sufficient",
        )
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_output

        agent = EscalationDecisionAgent(llm=mock_llm)
        res = agent.decide(
            message="Payment failed for order ORD1004",
            intent="payment_issue",
            investigation={
                "status": "found",
                "order_id": "ORD1004",
                "order": {"id": "ORD1004", "status": "payment_failed"},
                "payments": [{"id": "PAY-004", "status": "failed", "amount": 89.99}],
            },
        )
        # Verify hard safety rule overrode the model
        self.assertTrue(res.should_escalate)
        self.assertEqual(res.decision_source, "deterministic_safety_override")
        self.assertEqual(res.target_team, "billing_support")
        self.assertEqual(res.priority, "urgent")
        self.assertIn("Hard safety policy rule overrode", res.explanation)

    def test_workflow_integration_escalates_and_creates_ticket(self):
        """Full support workflow execution produces escalation decision, attaches ticket, and populates metadata."""
        chat_res = run_support_workflow("Can you please connect me to a human agent?")

        self.assertEqual(chat_res["decision"], "escalated")
        self.assertIsNotNone(chat_res["ticket"])
        self.assertIsNotNone(chat_res.get("escalation"))
        self.assertTrue(chat_res["escalation"]["should_escalate"])
        self.assertEqual(chat_res["escalation"]["target_team"], "general_support")
        self.assertIn("Ticket ID:", chat_res["assistant_message"])

    def test_duplicate_ticket_prevention_across_turns(self):
        """Multi-turn conversation in the same session does not create duplicate tickets for the same issue."""
        session_id = "test-session-no-duplicate-tickets"

        # Turn 1: Triggers escalation
        res1 = run_support_workflow("Payment failed for order ORD1004", session_id=session_id)
        self.assertEqual(res1["decision"], "escalated")
        ticket1 = res1["ticket"]
        self.assertIsNotNone(ticket1)
        ticket_id = ticket1["ticket_id"]
        self.assertEqual(len(list_tickets()), 1)

        # Turn 2: Follow-up question in the same session
        res2 = run_support_workflow("Any update on that?", session_id=session_id)
        # Should reuse the existing ticket rather than creating a duplicate
        self.assertEqual(len(list_tickets()), 1)
        if res2.get("ticket"):
            self.assertEqual(res2["ticket"]["ticket_id"], ticket_id)

    def test_api_schema_contract_compatibility(self):
        """ChatResponse schema parses and validates workflow output including escalation metadata."""
        chat_res = run_support_workflow("Please transfer me to a manager")

        response_obj = ChatResponse(**chat_res)
        self.assertEqual(response_obj.decision, "escalated")
        self.assertIsNotNone(response_obj.ticket)
        self.assertIsNotNone(response_obj.escalation)
        self.assertTrue(response_obj.escalation["should_escalate"])
        self.assertEqual(response_obj.escalation["target_team"], "senior_support")


if __name__ == "__main__":
    unittest.main()
