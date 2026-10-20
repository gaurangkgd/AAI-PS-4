"""Unit tests for knowledge base retrieval service using unittest."""

import unittest

try:
    from backend.knowledge_retriever import retrieve_knowledge
except ImportError:
    from knowledge_retriever import retrieve_knowledge


class TestKnowledgeRetriever(unittest.TestCase):
    def test_payment_deduction_query(self):
        msg = "My payment was deducted from bank account but order is failed"
        intent = "payment_issue"
        results = retrieve_knowledge(msg, intent, top_k=3)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["intent"], "payment_issue")
        self.assertIn("payment", results[0]["title"].lower())

    def test_order_tracking_query(self):
        msg = "Where is my order? Can you track delivery shipment?"
        intent = "order_tracking"
        results = retrieve_knowledge(msg, intent, top_k=3)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["intent"], "order_tracking")
        self.assertIn("tracking", results[0]["title"].lower())

    def test_refund_status_query(self):
        msg = "What is the status of my refund timeline for returned product?"
        intent = "refund_status"
        results = retrieve_knowledge(msg, intent, top_k=3)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["intent"], "refund_status")
        self.assertIn("refund", results[0]["title"].lower())

    def test_login_account_troubleshooting(self):
        msg = "I forgot my password and cannot log in to my account"
        intent = "account_issue"
        results = retrieve_knowledge(msg, intent, top_k=3)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["intent"], "account_issue")
        self.assertIn("login", results[0]["title"].lower())

    def test_irrelevant_input_handled_gracefully(self):
        # Gibberish input with no keyword or intent relevance
        msg = "xyz123 random meaningless gibberish test input"
        intent = "general_inquiry"
        results = retrieve_knowledge(msg, intent, top_k=3)
        self.assertEqual(results, [])

    def test_ranking_and_max_limit(self):
        # Even if multiple articles might have low score, top_k should be strictly enforced
        msg = "Payment and refund issue with order cancellation"
        intent = "payment_issue"
        top_k = 2
        results = retrieve_knowledge(msg, intent, top_k=top_k)
        self.assertLessEqual(len(results), top_k)
        # Top result should match primary intent
        self.assertEqual(results[0]["intent"], "payment_issue")


if __name__ == "__main__":
    unittest.main()
