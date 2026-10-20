"""Rule-based customer intent classification for e-commerce support."""

import re

# Supported intent labels
INTENT_PAYMENT_ISSUE = "payment_issue"
INTENT_ORDER_TRACKING = "order_tracking"
INTENT_CANCELLATION = "cancellation"
INTENT_RETURN_OR_REPLACEMENT = "return_or_replacement"
INTENT_REFUND_STATUS = "refund_status"
INTENT_ACCOUNT_ISSUE = "account_issue"
INTENT_PRODUCT_INQUIRY = "product_inquiry"
INTENT_GENERAL_INQUIRY = "general_inquiry"

ALL_INTENTS = [
    INTENT_PAYMENT_ISSUE,
    INTENT_ORDER_TRACKING,
    INTENT_CANCELLATION,
    INTENT_RETURN_OR_REPLACEMENT,
    INTENT_REFUND_STATUS,
    INTENT_ACCOUNT_ISSUE,
    INTENT_PRODUCT_INQUIRY,
    INTENT_GENERAL_INQUIRY,
]


def classify_intent(message: str) -> str:
    """Classify the primary support intent from a customer's message.

    Applies deterministic keyword/pattern rules in prioritized order:
    1. Refund status queries
    2. Payment issues (takes precedence over generic tracking terms)
    3. Cancellation requests
    4. Return or replacement requests
    5. Order tracking and delivery status
    6. Account and authentication issues
    7. Product availability and feature inquiries
    8. General inquiry (fallback)
    """
    if not message or not isinstance(message, str):
        return INTENT_GENERAL_INQUIRY

    text = message.lower().strip()

    # 1. Refund Status: specifically check for refund queries
    refund_patterns = [
        r"\brefund\b",
        r"\bmoney back\b",
        r"\breimburse(ment)?\b",
    ]
    if any(re.search(pattern, text) for pattern in refund_patterns):
        return INTENT_REFUND_STATUS

    # 2. Payment Issue: payment deducted, transaction failure, card decline, etc.
    payment_patterns = [
        r"\bpayment\b",
        r"\bdeducted\b",
        r"\bdebited\b",
        r"\bcharged\b",
        r"\btransaction\b",
        r"\bpaid\b",
        r"\bcard declined\b",
        r"\bupi\b",
        r"\bgateway\b",
        r"\bfailed payment\b",
        r"\bpayment failed\b",
        r"\bdouble charge\b",
        r"\bovercharge\b",
    ]
    if any(re.search(pattern, text) for pattern in payment_patterns):
        return INTENT_PAYMENT_ISSUE

    # 3. Cancellation: order or item cancellation
    cancellation_patterns = [
        r"\bcancel\b",
        r"\bcancellation\b",
        r"\bcanceling\b",
        r"\bcancelling\b",
        r"\babort\b",
        r"\bstop delivery\b",
    ]
    if any(re.search(pattern, text) for pattern in cancellation_patterns):
        return INTENT_CANCELLATION

    # 4. Return or Replacement: damage, defect, return, replacement, wrong item
    return_patterns = [
        r"\breturn\b",
        r"\breplace(ment)?\b",
        r"\bdamaged\b",
        r"\bbroken\b",
        r"\bdefective\b",
        r"\bfaulty\b",
        r"\bwrong (item|product|size|color)\b",
        r"\bexchange\b",
    ]
    if any(re.search(pattern, text) for pattern in return_patterns):
        return INTENT_RETURN_OR_REPLACEMENT

    # 5. Order Tracking: location, arrival time, delivery status
    tracking_patterns = [
        r"\bwhere(?:\s+is|'s)\s+(?:(?:my|the)\s+)?(?:order|package|item|delivery|parcel)\b",
        r"\btrack(ing)?\b",
        r"\bstatus\b",
        r"\bwhen will (it|my order) (arrive|reach|deliver)\b",
        r"\bdispatch(ed)?\b",
        r"\bshipment\b",
        r"\bshipped\b",
        r"\bdelayed\b",
        r"\bdelivery\b",
        r"\bcourier\b",
        r"\bexpected arrival\b",
    ]
    if any(re.search(pattern, text) for pattern in tracking_patterns):
        return INTENT_ORDER_TRACKING

    # 6. Account Issue: authentication, login, credentials
    account_patterns = [
        r"\blog ?in\b",
        r"\bsign ?in\b",
        r"\bpassword\b",
        r"\botp\b",
        r"\baccount\b",
        r"\bprofile\b",
        r"\bunable to log\b",
        r"\bcannot log\b",
        r"\breset password\b",
        r"\blocked out\b",
    ]
    if any(re.search(pattern, text) for pattern in account_patterns):
        return INTENT_ACCOUNT_ISSUE

    # 7. Product Inquiry: availability, specifications, pricing
    product_patterns = [
        r"\b(in )?stock\b",
        r"\bavailab(le|ility)\b",
        r"\bspecs?\b",
        r"\bspecification(s)?\b",
        r"\bfeature(s)?\b",
        r"\bprice\b",
        r"\bcost\b",
        r"\bwarranty\b",
        r"\bcompatible\b",
        r"\bcompatibility\b",
        r"\bproduct detail(s)?\b",
    ]
    if any(re.search(pattern, text) for pattern in product_patterns):
        return INTENT_PRODUCT_INQUIRY

    # 8. General Inquiry: default fallback
    return INTENT_GENERAL_INQUIRY
