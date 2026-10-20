"""Unit tests for the Troubleshooting Agent in PS-04 Agentic Customer Support System."""

import copy
import unittest
from unittest.mock import MagicMock

try:
    from backend.agents.troubleshooting_agent import (
        TroubleshootingAgent,
        TroubleshootingResult,
        LLMTroubleshootingOutput,
        diagnose_support_issue,
    )
    from backend.mock_data import ORDERS, PAYMENTS
    from backend.support_investigator import investigate_order_context
    from backend.ticket_service import list_tickets, clear_tickets
    from backend.support_workflow import run_support_workflow
except ImportError:
    from agents.troubleshooting_agent import (
        TroubleshootingAgent,
        TroubleshootingResult,
        LLMTroubleshootingOutput,
        diagnose_support_issue,
    )
    from mock_data import ORDERS, PAYMENTS
    from support_investigator import investigate_order_context
    from ticket_service import list_tickets, clear_tickets
    from support_workflow import run_support_workflow


class TestTroubleshootingAgent(unittest.TestCase):
    """Test suite for TroubleshootingAgent ensuring grounded diagnosis, safety, and integration."""

    def setUp(self):
        clear_tickets()
        self.agent = TroubleshootingAgent(api_key=None)  # Explicitly deterministic

    def tearDown(self):
        clear_tickets()

    def test_diagnosis_grounded_in_payment_failure_facts(self):
        """Payment failure (ORD1004) should be diagnosed with exact gateway decline and transaction facts."""
        msg = "Why was my payment for order ORD1004 declined?"
        inv = investigate_order_context(msg)
        self.assertEqual(inv["status"], "found")

        result = self.agent.diagnose(
            message=msg,
            intent="payment_issue",
            investigation=inv,
            knowledge_results=[{"id": "KB-PAY-001"}],
        )

        self.assertIsInstance(result, TroubleshootingResult)
        self.assertEqual(result.order_id, "ORD1004")
        self.assertEqual(result.order_status, "payment_failed")
        self.assertIn("failed", result.diagnosis.lower())
        self.assertIn("TXN-909012-FAILED", result.diagnosis)
        self.assertTrue(result.suggest_escalation)
        self.assertFalse(result.needs_more_info)
        self.assertGreaterEqual(result.confidence, 0.90)
        self.assertEqual(result.source, "deterministic_rule_based")
        self.assertIn("KB-PAY-001", result.knowledge_sources)

    def test_diagnosis_grounded_in_delivered_order_facts(self):
        """Delivered order (ORD1001) should diagnose completed delivery and inspection window."""
        msg = "Where is my order ORD1001?"
        inv = investigate_order_context(msg)
        result = self.agent.diagnose(
            message=msg,
            intent="order_tracking",
            investigation=inv,
            knowledge_results=[{"id": "KB-TRK-001"}],
        )

        self.assertEqual(result.order_id, "ORD1001")
        self.assertEqual(result.order_status, "delivered")
        self.assertIn("delivered", result.diagnosis.lower())
        self.assertFalse(result.needs_more_info)
        self.assertFalse(result.suggest_escalation)
        self.assertIn("KB-TRK-001", result.knowledge_sources)

    def test_cancellation_eligibility_grounded_in_order_status(self):
        """Processing order (ORD1002) is eligible for cancellation; Shipped order (ORD1003) is not."""
        # 1. Processing order (ORD1002)
        inv_proc = investigate_order_context("Cancel order ORD1002")
        res_proc = self.agent.diagnose(
            message="Cancel order ORD1002",
            intent="cancellation",
            investigation=inv_proc,
            knowledge_results=[{"id": "KB-CAN-001"}],
        )
        self.assertIn("eligible", res_proc.diagnosis.lower())
        self.assertFalse(res_proc.needs_more_info)

        # 2. Shipped order (ORD1003)
        inv_ship = investigate_order_context("Cancel order ORD1003")
        res_ship = self.agent.diagnose(
            message="Cancel order ORD1003",
            intent="cancellation",
            investigation=inv_ship,
            knowledge_results=[{"id": "KB-CAN-001"}],
        )
        self.assertIn("cannot be cancelled", res_ship.diagnosis.lower())
        self.assertFalse(res_ship.needs_more_info)

    def test_missing_order_id_requires_more_info(self):
        """When an order ID is required but missing, agent asks for clarification."""
        msg = "Please check my payment deduction"
        inv = investigate_order_context(msg)
        self.assertEqual(inv["status"], "order_id_required")

        result = self.agent.diagnose(
            message=msg,
            intent="payment_issue",
            investigation=inv,
        )

        self.assertTrue(result.needs_more_info)
        self.assertIsNone(result.order_id)
        self.assertIn("Order ID", result.diagnosis)
        self.assertTrue(any("Provide your Order ID" in step for step in result.recommended_steps))

    def test_unknown_order_id_diagnoses_not_found(self):
        """When order ID is unrecognized (ORD9999), agent diagnoses not found and suggests verification."""
        msg = "Check status of order ORD9999"
        inv = investigate_order_context(msg)
        self.assertEqual(inv["status"], "order_not_found")

        result = self.agent.diagnose(
            message=msg,
            intent="order_tracking",
            investigation=inv,
        )

        self.assertTrue(result.needs_more_info)
        self.assertEqual(result.order_id, "ORD9999")
        self.assertIn("not found", result.diagnosis.lower())
        self.assertTrue(any("confirmation email" in step for step in result.recommended_steps))

    def test_diagnosis_grounded_in_knowledge_policy_without_order(self):
        """General inquiry or account issues should be grounded in matched knowledge base articles."""
        result = self.agent.diagnose(
            message="I forgot my password and cannot sign in",
            intent="account_issue",
            investigation=None,
            knowledge_retrieval={"sources": ["KB-ACC-001"]},
        )

        self.assertFalse(result.needs_more_info)
        self.assertIn("KB-ACC-001", result.knowledge_sources)
        self.assertIn("KB-ACC-001", result.diagnosis)
        self.assertGreater(len(result.recommended_steps), 0)

    def test_missing_api_key_deterministic_fallback(self):
        """Without API key, agent operates deterministically with source='deterministic_rule_based'."""
        agent = TroubleshootingAgent(api_key="")
        result = agent.diagnose(
            message="Payment deducted for order ORD1004",
            intent="payment_issue",
            investigation=investigate_order_context("ORD1004"),
        )

        self.assertEqual(result.source, "deterministic_rule_based")
        self.assertEqual(result.order_id, "ORD1004")
        self.assertTrue(result.suggest_escalation)

    def test_optional_llm_reasoning_success(self):
        """When LLM is provided and returns structured output, source is 'llm_assisted'."""
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.return_value = LLMTroubleshootingOutput(
            issue="Payment Gateway Decline",
            diagnosis="Payment gateway declined transaction TXN-909012-FAILED due to card issuer security policy.",
            evidence=["Order ORD1004 has payment_failed status", "TXN-909012-FAILED returned decline"],
            recommended_steps=["Call bank customer care to authorize online merchant transaction"],
            needs_more_info=False,
            suggest_escalation=True,
            confidence=0.96,
        )

        agent = TroubleshootingAgent(api_key="fake-key", llm=mock_llm)
        result = agent.diagnose(
            message="Payment declined for order ORD1004",
            intent="payment_issue",
            investigation=investigate_order_context("ORD1004"),
        )

        self.assertEqual(result.source, "llm_assisted")
        self.assertEqual(result.issue, "Payment Gateway Decline")
        self.assertEqual(result.order_id, "ORD1004")
        self.assertEqual(result.order_status, "payment_failed")
        self.assertTrue(result.suggest_escalation)
        self.assertEqual(result.confidence, 0.96)

    def test_llm_failure_falls_back_to_deterministic_diagnosis(self):
        """When LLM throws an exception, agent falls back seamlessly to deterministic diagnosis."""
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.side_effect = RuntimeError("LLM request timeout")

        agent = TroubleshootingAgent(api_key="fake-key", llm=mock_llm)
        result = agent.diagnose(
            message="Why is order ORD1001 delivered?",
            intent="order_tracking",
            investigation=investigate_order_context("ORD1001"),
        )

        self.assertEqual(result.source, "deterministic_rule_based")
        self.assertEqual(result.order_id, "ORD1001")
        self.assertEqual(result.order_status, "delivered")

    def test_read_only_invariance_no_data_mutation(self):
        """TroubleshootingAgent must be strictly read-only and never mutate orders, payments, or tickets."""
        orders_snapshot = copy.deepcopy(ORDERS)
        payments_snapshot = copy.deepcopy(PAYMENTS)
        tickets_snapshot = copy.deepcopy(list_tickets())

        self.agent.diagnose(
            message="Cancel order ORD1002 immediately and refund payment",
            intent="cancellation",
            investigation=investigate_order_context("ORD1002"),
        )

        self.assertEqual(ORDERS, orders_snapshot)
        self.assertEqual(PAYMENTS, payments_snapshot)
        self.assertEqual(list_tickets(), tickets_snapshot)

    def test_workflow_integration_preserves_contract_and_enriches_response(self):
        """Support workflow execution populates troubleshooting and preserves existing ChatResponse contract."""
        res = run_support_workflow("Payment deducted for order ORD1004 but order failed")

        self.assertEqual(res["intent"], "payment_issue")
        self.assertEqual(res["decision"], "escalated")
        self.assertIsNotNone(res["ticket"])

        # Verify troubleshooting metadata
        tb = res.get("troubleshooting")
        self.assertIsNotNone(tb)
        self.assertEqual(tb["order_id"], "ORD1004")
        self.assertEqual(tb["order_status"], "payment_failed")
        self.assertTrue(tb["suggest_escalation"])
        self.assertFalse(tb["needs_more_info"])
        self.assertIn("failed", tb["diagnosis"].lower())
        self.assertIn(tb["source"], {"deterministic_rule_based", "llm_assisted"})


if __name__ == "__main__":
    unittest.main()
