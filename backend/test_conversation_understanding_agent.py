"""Unit tests for the Conversation Understanding Agent.

Covers:
- Valid structured output generation
- All 8 supported intent labels
- Compound and ambiguous message interpretation
- Handling of invalid or malformed model output
- Missing API credentials fallback behavior
- Provider exceptions and graceful recovery
- End-to-end support workflow integration
All tests mock the LLM client to prevent network calls or API costs.
"""

import unittest
from unittest.mock import MagicMock, patch

from backend.agents.conversation_understanding_agent import (
    ConversationUnderstandingAgent,
    ConversationUnderstandingResult,
    understand_conversation,
    rule_based_understanding,
    VALID_INTENTS,
)
from backend.support_workflow import run_support_workflow


class TestConversationUnderstandingAgent(unittest.TestCase):
    """Test suite for ConversationUnderstandingAgent with mocked LLM interactions."""

    def test_missing_api_key_uses_deterministic_fallback(self):
        """When no API key is supplied, agent seamlessly uses rule-based fallback."""
        agent = ConversationUnderstandingAgent(api_key=None)
        # Ensure environment doesn't provide key for this test
        with patch.dict("os.environ", {}, clear=True):
            agent.api_key = None
            result = agent.understand("Where is my order ORD1001?")

        self.assertIsInstance(result, ConversationUnderstandingResult)
        self.assertEqual(result.intent, "order_tracking")
        self.assertEqual(result.category, "logistics")
        self.assertEqual(result.source, "rule_based_fallback")
        self.assertIn("rule-based", result.explanation.lower())

    def test_all_supported_intent_labels_in_fallback(self):
        """Verify each of the 8 supported intent labels maps to valid structured output."""
        sample_messages = {
            "payment_issue": "My card was debited twice for order ORD1001",
            "order_tracking": "Where is my package ORD1001?",
            "cancellation": "Please cancel my processing order ORD1002",
            "return_or_replacement": "I received a damaged and defective keyboard",
            "refund_status": "What is the status of my refund money back?",
            "account_issue": "I am locked out and cannot log in to my account",
            "product_inquiry": "Is the mechanical keyboard in stock?",
            "general_inquiry": "Hello, good morning support team!",
        }

        for expected_intent, message in sample_messages.items():
            result = rule_based_understanding(message)
            self.assertIn(result.intent, VALID_INTENTS)
            self.assertEqual(result.intent, expected_intent)
            self.assertTrue(0.0 <= result.confidence <= 1.0)
            self.assertIn(result.priority, {"low", "medium", "high", "urgent"})
            self.assertIn(result.sentiment, {"positive", "neutral", "negative", "frustrated", "urgent"})
            self.assertEqual(result.source, "rule_based_fallback")

    def test_llm_mock_structured_output_success(self):
        """When LLM is configured and succeeds, result reflects LLM classification."""
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        mock_structured.invoke.return_value = ConversationUnderstandingResult(
            intent="cancellation",
            category="order_management",
            priority="high",
            sentiment="frustrated",
            confidence=0.98,
            needs_clarification=False,
            explanation="Customer explicitly requested order cancellation due to long processing time.",
            source="llm",
        )

        agent = ConversationUnderstandingAgent(api_key="fake-test-key", llm=mock_llm)
        result = agent.understand("I want to cancel order ORD1002 right now, this is ridiculous!")

        self.assertEqual(result.intent, "cancellation")
        self.assertEqual(result.category, "order_management")
        self.assertEqual(result.priority, "high")
        self.assertEqual(result.sentiment, "frustrated")
        self.assertEqual(result.confidence, 0.98)
        self.assertFalse(result.needs_clarification)
        self.assertEqual(result.source, "llm")
        self.assertIn("Customer explicitly requested", result.explanation)

    def test_compound_request_interpretation(self):
        """Compound message handling accurately prioritizes the actionable intent."""
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        # Compound message: tracking delay + cancellation request
        mock_structured.invoke.return_value = ConversationUnderstandingResult(
            intent="cancellation",
            category="order_management",
            priority="medium",
            sentiment="negative",
            confidence=0.94,
            needs_clarification=False,
            explanation="Customer mentioned delivery delay but primary action requested is order cancellation.",
            source="llm",
        )

        agent = ConversationUnderstandingAgent(api_key="fake-test-key", llm=mock_llm)
        result = agent.understand("My package has been delayed for a week so please cancel ORD1002.")

        self.assertEqual(result.intent, "cancellation")
        self.assertEqual(result.source, "llm")
        self.assertFalse(result.needs_clarification)

    def test_ambiguous_message_sets_needs_clarification(self):
        """Vague or ambiguous message sets needs_clarification=True."""
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        mock_structured.invoke.return_value = ConversationUnderstandingResult(
            intent="general_inquiry",
            category="general",
            priority="low",
            sentiment="neutral",
            confidence=0.35,
            needs_clarification=True,
            explanation="Customer input is too brief and lacks context to identify a specific support intent.",
            source="llm",
        )

        agent = ConversationUnderstandingAgent(api_key="fake-test-key", llm=mock_llm)
        result = agent.understand("help")

        self.assertEqual(result.intent, "general_inquiry")
        self.assertTrue(result.needs_clarification)
        self.assertLess(result.confidence, 0.5)

    def test_provider_exception_triggers_graceful_fallback(self):
        """When LLM provider raises an exception, agent catches it and returns fallback."""
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        # Simulate provider failure (e.g. rate limit, connection timeout)
        mock_structured.invoke.side_effect = RuntimeError("ResourceExhausted: 429 Quota Exceeded")

        agent = ConversationUnderstandingAgent(api_key="fake-test-key", llm=mock_llm)
        result = agent.understand("Where is my order ORD1001?")

        self.assertIsInstance(result, ConversationUnderstandingResult)
        self.assertEqual(result.intent, "order_tracking")
        self.assertEqual(result.source, "rule_based_fallback")
        self.assertIn("LLM provider error", result.explanation)

    def test_invalid_model_output_type_fallback(self):
        """When LLM returns an unexpected type (e.g., int or string), fallback is used."""
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        mock_structured.invoke.return_value = "Unexpected non-dict string output"

        agent = ConversationUnderstandingAgent(api_key="fake-test-key", llm=mock_llm)
        result = agent.understand("Please cancel order ORD1002")

        self.assertEqual(result.intent, "cancellation")
        self.assertEqual(result.source, "rule_based_fallback")

    def test_intent_normalization_handles_variations(self):
        """Pydantic validator normalizes hyphenated or non-standard intent strings."""
        res1 = ConversationUnderstandingResult(
            intent="ORDER-TRACKING",
            category="logistics",
            explanation="Normalized test",
        )
        self.assertEqual(res1.intent, "order_tracking")

        res2 = ConversationUnderstandingResult(
            intent="unknown_unsupported_tag",
            category="general",
            explanation="Fallback test",
        )
        self.assertEqual(res2.intent, "general_inquiry")

    def test_support_workflow_integration_includes_understanding(self):
        """Verify LangGraph workflow output includes the structured understanding payload."""
        response = run_support_workflow("Where is my order ORD1001?")

        self.assertIn("understanding", response)
        self.assertIsNotNone(response["understanding"])
        understanding = response["understanding"]

        self.assertEqual(understanding["intent"], "order_tracking")
        self.assertEqual(understanding["category"], "logistics")
        self.assertIn("confidence", understanding)
        self.assertIn("source", understanding)
        self.assertIn("explanation", understanding)


if __name__ == "__main__":
    unittest.main()
