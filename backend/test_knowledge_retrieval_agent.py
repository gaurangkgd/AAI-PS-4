"""Unit tests for the Knowledge Retrieval / Knowledge Base Agent."""

import unittest
from unittest.mock import MagicMock, patch

try:
    from backend.agents.knowledge_retrieval_agent import (
        KnowledgeRetrievalAgent,
        KnowledgeRetrievalResult,
        LLMRerankOutput,
        retrieve_knowledge_context,
        score_knowledge_entries,
    )
    from backend.knowledge_base import KNOWLEDGE_BASE
    from backend.support_workflow import run_support_workflow
except ImportError:
    from agents.knowledge_retrieval_agent import (
        KnowledgeRetrievalAgent,
        KnowledgeRetrievalResult,
        LLMRerankOutput,
        retrieve_knowledge_context,
        score_knowledge_entries,
    )
    from knowledge_base import KNOWLEDGE_BASE
    from support_workflow import run_support_workflow


class TestKnowledgeRetrievalAgent(unittest.TestCase):
    """Test suite for KnowledgeRetrievalAgent covering scoring, safety, and integration."""

    def setUp(self):
        self.agent = KnowledgeRetrievalAgent(api_key=None)  # Explicitly deterministic
        self.valid_kb_ids = {entry["id"] for entry in KNOWLEDGE_BASE}
        self.valid_kb_titles = {entry["id"]: entry["title"] for entry in KNOWLEDGE_BASE}

    def test_relevant_policy_retrieval_for_payment_issue(self):
        """Payment issue query should retrieve verified payment troubleshooting articles."""
        result = self.agent.retrieve(
            query="My money was debited from card but order payment failed",
            intent="payment_issue",
            top_k=2,
        )
        self.assertIsInstance(result, KnowledgeRetrievalResult)
        self.assertTrue(result.has_sufficient_knowledge)
        self.assertGreater(len(result.entries), 0)
        self.assertLessEqual(len(result.entries), 2)
        self.assertEqual(result.sources[0], "KB-PAY-001")
        self.assertIn("payment", result.source_titles[0].lower())
        self.assertIn(result.sources[0], result.relevance_scores)
        self.assertGreater(result.relevance_scores[result.sources[0]], 0.5)
        self.assertEqual(result.retrieval_method, "keyword_intent_scored")

    def test_relevant_policy_retrieval_for_order_tracking(self):
        """Order tracking query should retrieve shipment tracking guidance."""
        result = self.agent.retrieve(
            query="Where is my shipment? Can you track the courier delivery status?",
            intent="order_tracking",
            top_k=2,
        )
        self.assertTrue(result.has_sufficient_knowledge)
        self.assertEqual(result.sources[0], "KB-TRK-001")
        self.assertIn("Tracking", result.source_titles[0])
        self.assertIn("courier", result.entries[0]["guidance"].lower())

    def test_relevant_policy_retrieval_for_return_or_replacement(self):
        """Damaged product query should retrieve return/replacement policy."""
        result = self.agent.retrieve(
            query="The package arrived damaged and the item is broken inside",
            intent="return_or_replacement",
            top_k=2,
        )
        self.assertTrue(result.has_sufficient_knowledge)
        self.assertIn(result.sources[0], {"KB-RET-001", "KB-RET-002"})
        self.assertIn("damaged", result.entries[0]["guidance"].lower())

    def test_empty_or_whitespace_query(self):
        """Empty or whitespace queries must return insufficient knowledge with no entries."""
        for empty_text in ["", "   ", None]:
            result = self.agent.retrieve(query=empty_text, intent="general_inquiry")
            self.assertFalse(result.has_sufficient_knowledge)
            self.assertEqual(result.entries, [])
            self.assertEqual(result.sources, [])
            self.assertEqual(result.relevance_scores, {})
            self.assertIn("Empty", result.explanation)

    def test_irrelevant_or_gibberish_query(self):
        """Gibberish queries with no matching keywords or title hits must yield no entries."""
        result = self.agent.retrieve(
            query="xyz999 qwertyuiop zzzzz lkjhgfdsa",
            intent="general_inquiry",
        )
        self.assertFalse(result.has_sufficient_knowledge)
        self.assertEqual(result.entries, [])
        self.assertEqual(result.sources, [])
        self.assertEqual(result.relevance_scores, {})
        self.assertIn("No relevant", result.explanation)

    def test_sources_and_titles_strictly_match_approved_knowledge_base(self):
        """All sources and titles returned must match approved KNOWLEDGE_BASE entries."""
        intents_and_queries = [
            ("refund_status", "When will my refund money be credited back to my bank statement?"),
            ("cancellation", "How do I cancel my order before it is dispatched?"),
            ("account_issue", "I forgot my password and cannot sign in to my account"),
            ("product_inquiry", "Are the technical specifications and warranty details available?"),
            ("general_inquiry", "What are customer support operating hours?"),
        ]
        for intent, query in intents_and_queries:
            result = self.agent.retrieve(query=query, intent=intent, top_k=3)
            self.assertTrue(result.has_sufficient_knowledge, f"Failed for intent {intent}")
            for entry, src_id, src_title in zip(result.entries, result.sources, result.source_titles):
                self.assertIn(src_id, self.valid_kb_ids)
                self.assertEqual(entry["id"], src_id)
                self.assertEqual(src_title, self.valid_kb_titles[src_id])
                self.assertEqual(entry["title"], self.valid_kb_titles[src_id])

    def test_agent_never_fabricates_or_hallucinates_policies(self):
        """Verified entries must be genuine deep copies of mock knowledge base records."""
        result = self.agent.retrieve(
            query="Double deduction on credit card statement",
            intent="payment_issue",
            top_k=2,
        )
        self.assertTrue(result.has_sufficient_knowledge)
        for entry in result.entries:
            # Must strictly match the canonical record
            canonical = next(kb for kb in KNOWLEDGE_BASE if kb["id"] == entry["id"])
            self.assertEqual(entry["title"], canonical["title"])
            self.assertEqual(entry["guidance"], canonical["guidance"])
            self.assertEqual(entry["intent"], canonical["intent"])

    def test_missing_api_key_deterministic_fallback(self):
        """Without API key, agent operates deterministically without network calls."""
        agent = KnowledgeRetrievalAgent(api_key="")
        result = agent.retrieve("Double deduction on credit card", intent="payment_issue")
        self.assertTrue(result.has_sufficient_knowledge)
        self.assertEqual(result.retrieval_method, "keyword_intent_scored")
        self.assertIn("KB-PAY-002", result.sources)

    def test_optional_llm_reranking_success(self):
        """When LLM is provided and returns valid candidate IDs, reranking is applied."""
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.return_value = LLMRerankOutput(
            selected_ids=["KB-PAY-002"],
            has_sufficient_knowledge=True,
            explanation="Selected duplicate deduction article as it directly targets multiple charges.",
        )

        agent = KnowledgeRetrievalAgent(api_key="fake-key", llm=mock_llm)
        result = agent.retrieve(
            query="I was charged twice for the same transaction",
            intent="payment_issue",
            top_k=2,
        )

        self.assertTrue(result.has_sufficient_knowledge)
        self.assertEqual(result.retrieval_method, "keyword_intent_scored_with_gemini_rerank")
        self.assertEqual(result.sources, ["KB-PAY-002"])
        self.assertIn("Selected duplicate deduction", result.explanation)

    def test_llm_reranking_rejects_hallucinated_ids_and_falls_back(self):
        """If LLM hallucinates an unknown ID, it is discarded; if none remain, falls back cleanly."""
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        # LLM returns a completely invented ID
        mock_structured.invoke.return_value = LLMRerankOutput(
            selected_ids=["KB-HALLUCINATED-999"],
            has_sufficient_knowledge=True,
            explanation="Hallucinated policy ID",
        )

        agent = KnowledgeRetrievalAgent(api_key="fake-key", llm=mock_llm)
        result = agent.retrieve(
            query="I was charged twice for the same transaction",
            intent="payment_issue",
            top_k=2,
        )

        # Hallucinated ID is filtered out -> has_sufficient_knowledge becomes False
        self.assertFalse(result.has_sufficient_knowledge)
        self.assertEqual(result.entries, [])
        self.assertEqual(result.sources, [])

    def test_llm_reranking_exception_falls_back_to_deterministic(self):
        """If LLM invocation throws an exception, system falls back seamlessly to deterministic score."""
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.side_effect = RuntimeError("LLM API connection timed out")

        agent = KnowledgeRetrievalAgent(api_key="fake-key", llm=mock_llm)
        result = agent.retrieve(
            query="Double deduction on credit card statement",
            intent="payment_issue",
            top_k=2,
        )

        self.assertTrue(result.has_sufficient_knowledge)
        self.assertEqual(result.retrieval_method, "keyword_intent_scored")
        self.assertIn("KB-PAY-002", result.sources)

    def test_workflow_integration_preserves_contract(self):
        """Full support workflow execution must populate knowledge_retrieval and preserve contract."""
        chat_res = run_support_workflow("What are customer support operating hours and contact info?")
        self.assertEqual(chat_res["intent"], "general_inquiry")
        self.assertEqual(chat_res["decision"], "knowledge_guidance")

        # Check knowledge_results backwards compatibility
        self.assertIsInstance(chat_res["knowledge_results"], list)
        self.assertGreater(len(chat_res["knowledge_results"]), 0)
        self.assertEqual(chat_res["knowledge_results"][0]["id"], "KB-GEN-001")

        # Check new knowledge_retrieval structured dictionary
        kr = chat_res.get("knowledge_retrieval")
        self.assertIsNotNone(kr)
        self.assertTrue(kr["has_sufficient_knowledge"])
        self.assertIn("KB-GEN-001", kr["sources"])
        self.assertIn("KB-GEN-001", kr["relevance_scores"])
        self.assertIn(kr["retrieval_method"], {"keyword_intent_scored", "keyword_intent_scored_with_gemini_rerank"})


if __name__ == "__main__":
    unittest.main()
