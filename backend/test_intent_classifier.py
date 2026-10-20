"""Unit tests for deterministic intent classifier using built-in unittest."""

import unittest

try:
    from backend.intent_classifier import (
        classify_intent,
        INTENT_PAYMENT_ISSUE,
        INTENT_ORDER_TRACKING,
        INTENT_CANCELLATION,
        INTENT_RETURN_OR_REPLACEMENT,
        INTENT_REFUND_STATUS,
        INTENT_ACCOUNT_ISSUE,
        INTENT_PRODUCT_INQUIRY,
        INTENT_GENERAL_INQUIRY,
    )
except ImportError:
    from intent_classifier import (
        classify_intent,
        INTENT_PAYMENT_ISSUE,
        INTENT_ORDER_TRACKING,
        INTENT_CANCELLATION,
        INTENT_RETURN_OR_REPLACEMENT,
        INTENT_REFUND_STATUS,
        INTENT_ACCOUNT_ISSUE,
        INTENT_PRODUCT_INQUIRY,
        INTENT_GENERAL_INQUIRY,
    )


class TestIntentClassifier(unittest.TestCase):
    def test_payment_issue(self):
        msg = "Payment deducted but order failed"
        self.assertEqual(classify_intent(msg), INTENT_PAYMENT_ISSUE)

    def test_order_tracking(self):
        msg = "Where is my order"
        self.assertEqual(classify_intent(msg), INTENT_ORDER_TRACKING)

    def test_cancellation(self):
        msg = "Cancel my order"
        self.assertEqual(classify_intent(msg), INTENT_CANCELLATION)

    def test_return_or_replacement(self):
        msg = "Received a damaged product"
        self.assertEqual(classify_intent(msg), INTENT_RETURN_OR_REPLACEMENT)

    def test_refund_status(self):
        msg = "Where is my refund"
        self.assertEqual(classify_intent(msg), INTENT_REFUND_STATUS)

    def test_account_issue(self):
        msg = "Cannot log in"
        self.assertEqual(classify_intent(msg), INTENT_ACCOUNT_ISSUE)

    def test_product_inquiry(self):
        msg = "Is this product available"
        self.assertEqual(classify_intent(msg), INTENT_PRODUCT_INQUIRY)

    def test_general_inquiry(self):
        msg = "Hello, how are you today?"
        self.assertEqual(classify_intent(msg), INTENT_GENERAL_INQUIRY)

    def test_case_insensitivity(self):
        self.assertEqual(
            classify_intent("WHERE IS MY ORDER"),
            INTENT_ORDER_TRACKING,
        )
        self.assertEqual(
            classify_intent("pAyMeNt DeDuCtEd bUt No cOnFiRmAtIoN"),
            INTENT_PAYMENT_ISSUE,
        )
        self.assertEqual(
            classify_intent("CAN I CANCEL THIS ORDER"),
            INTENT_CANCELLATION,
        )

    def test_payment_priority_over_tracking(self):
        # Even if 'order' or 'track' appears, payment deduction takes priority
        msg = "My money was deducted for order ORD1001, please check"
        self.assertEqual(classify_intent(msg), INTENT_PAYMENT_ISSUE)

    def test_refund_distinction_from_return(self):
        msg = "What is the status of my refund?"
        self.assertEqual(classify_intent(msg), INTENT_REFUND_STATUS)


if __name__ == "__main__":
    unittest.main()
