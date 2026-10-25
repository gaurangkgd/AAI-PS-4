"""Local demo support knowledge base with fictional policies and troubleshooting articles."""

import copy

KNOWLEDGE_BASE = [
    # 1. Payment Issue
    {
        "id": "KB-PAY-001",
        "intent": "payment_issue",
        "title": "Failed or Pending Payment Troubleshooting",
        "guidance": (
            "If funds were deducted from your bank account or card but your order status "
            "displays failed or pending, payment gateways typically auto-reconcile or "
            "reverse the amount within 3 to 5 business days. Please keep your transaction ID "
            "or UPI reference number handy when contacting our support team."
        ),
        "keywords": [
            "payment",
            "deducted",
            "debited",
            "failed",
            "gateway",
            "transaction",
            "charged",
            "upi",
            "card",
        ],
    },
    {
        "id": "KB-PAY-002",
        "intent": "payment_issue",
        "title": "Double Deduction on Card or UPI",
        "guidance": (
            "If your bank statement reflects duplicate charges for a single order, "
            "the duplicate transaction is normally released automatically by your card-issuing bank. "
            "Our billing department can verify payment settlement against your order ID."
        ),
        "keywords": [
            "double",
            "charge",
            "twice",
            "duplicate",
            "overcharge",
            "payment",
            "card",
            "deducted",
        ],
    },
    # 2. Order Tracking
    {
        "id": "KB-TRK-001",
        "intent": "order_tracking",
        "title": "Tracking Your Order and Delivery Status",
        "guidance": (
            "Once an order is handed over to the courier partner, an active tracking link is generated. "
            "Standard deliveries typically arrive within the estimated delivery window shown at checkout. "
            "Courier tracking links may take up to 24 hours from dispatch to reflect live location scans."
        ),
        "keywords": [
            "track",
            "tracking",
            "status",
            "delivery",
            "courier",
            "dispatch",
            "shipment",
            "shipped",
            "where is my order",
        ],
    },
    {
        "id": "KB-TRK-002",
        "intent": "order_tracking",
        "title": "Delayed Delivery and Rescheduling",
        "guidance": (
            "If your shipment encounters transit delays due to weather or regional logistics, "
            "the courier will make another delivery attempt on the next business day. "
            "Customers may also request delivery rescheduling directly via the carrier's tracking page."
        ),
        "keywords": [
            "delayed",
            "delay",
            "late",
            "reschedule",
            "arrival",
            "courier",
            "delivery",
            "transit",
        ],
    },
    # 3. Cancellation
    {
        "id": "KB-CAN-001",
        "intent": "cancellation",
        "title": "Order Cancellation Policy",
        "guidance": (
            "Orders can be cancelled before they enter the packaging or shipping phase. "
            "Once dispatched, cancellation is no longer possible in-transit, but you may refuse "
            "delivery upon arrival or initiate a standard return once received."
        ),
        "keywords": [
            "cancel",
            "cancellation",
            "cancelling",
            "stop order",
            "abort",
            "order",
        ],
    },
    # 4. Return or Replacement
    {
        "id": "KB-RET-001",
        "intent": "return_or_replacement",
        "title": "Damaged, Defective, or Incorrect Product Policy",
        "guidance": (
            "If your product arrives damaged, broken, defective, or incorrect, please submit a return "
            "or replacement request within the inspection window. Photographs of the damaged package "
            "and item are required to speed up processing and doorstep replacement pickup."
        ),
        "keywords": [
            "damaged",
            "broken",
            "defective",
            "faulty",
            "replacement",
            "replace",
            "wrong",
            "exchange",
            "product",
        ],
    },
    {
        "id": "KB-RET-002",
        "intent": "return_or_replacement",
        "title": "General Return Conditions and Pickup",
        "guidance": (
            "Returned items must be unused, in their original condition, and packed with original "
            "labels, accessories, and warranty cards. Courier pickups are scheduled once the return "
            "request is approved."
        ),
        "keywords": [
            "return",
            "condition",
            "pickup",
            "packaging",
            "tags",
            "inspection",
        ],
    },
    # 5. Refund Status
    {
        "id": "KB-REF-001",
        "intent": "refund_status",
        "title": "Refund Processing Timelines and Payment Methods",
        "guidance": (
            "Once an authorized return is inspected or a cancellation confirmed, refunds are issued "
            "to the original payment method. Card and net banking refunds typically take 5 to 7 "
            "business days depending on your bank's clearance policies."
        ),
        "keywords": [
            "refund",
            "status",
            "timeline",
            "money back",
            "reimbursement",
            "credit",
            "bank",
        ],
    },
    {
        "id": "KB-REF-002",
        "intent": "refund_status",
        "title": "Missing or Delayed Refund Inquiries",
        "guidance": (
            "If your refund status shows completed but does not appear on your statement after 7 business days, "
            "please check with your bank providing the Acquirer Reference Number (ARN) issued in your refund email."
        ),
        "keywords": [
            "missing refund",
            "refund delay",
            "arn",
            "statement",
            "not received",
            "refund",
        ],
    },
    # 6. Account Issue
    {
        "id": "KB-ACC-001",
        "intent": "account_issue",
        "title": "Account Login and Password Recovery Troubleshooting",
        "guidance": (
            "If you cannot log in to your account, click 'Forgot Password' on the sign-in screen to receive a "
            "password reset link or one-time verification code (OTP). Verify your email spam folder if the email "
            "is not received immediately."
        ),
        "keywords": [
            "login",
            "sign in",
            "password",
            "reset",
            "otp",
            "account",
            "locked",
            "credentials",
        ],
    },
    # 7. Product Inquiry
    {
        "id": "KB-PRD-001",
        "intent": "product_inquiry",
        "title": "Product Stock, Specifications, and Warranty Details",
        "guidance": (
            "Item availability, technical specs, dimensions, and warranty coverage are listed on each product's "
            "detail page. For items currently marked out-of-stock, select 'Notify Me' to receive an alert when "
            "inventory is restocked."
        ),
        "keywords": [
            "stock",
            "available",
            "availability",
            "specs",
            "specifications",
            "features",
            "warranty",
            "price",
        ],
    },
    # 8. General Inquiry
    {
        "id": "KB-GEN-001",
        "intent": "general_inquiry",
        "title": "General Customer Support and Operating Information",
        "guidance": (
            "Our automated customer support system is available 24/7 to provide order tracking, answers to "
            "frequently asked questions, and general guidance. Live customer support agents are available "
            "during standard business operating hours for specialized assistance."
        ),
        "keywords": [
            "support",
            "hours",
            "help",
            "contact",
            "agent",
            "general",
            "store",
            "information",
        ],
    },
    # 9. Return window (editable from the Supervisor Desk; the AI reads the day count from here)
    {
        "id": "KB-RET-003",
        "intent": "return_or_replacement",
        "title": "Return Window Policy",
        "guidance": (
            "Unused items in their original packaging can be returned within 30 days of delivery. "
            "A pre-paid return label is issued automatically once the return is approved, and the refund "
            "goes back to your original payment method after inspection. Returns requested after the "
            "window need a specialist's exception approval."
        ),
        "keywords": [
            "return policy",
            "return window",
            "refund policy",
            "how many days",
            "days to return",
            "return period",
        ],
    },
    # 10. Human-in-the-loop (HITL) policies: cases the AI must hand to a human specialist
    {
        "id": "KB-HR-001",
        "intent": "human_review",
        "title": "Human Review: Payment Failure or Deduction",
        "guidance": (
            "When a customer reports money deducted but the order shows payment_failed or pending_payment, "
            "the AI must not promise a refund or retry. Verify the order and payment records, then open a "
            "high-priority ticket for Billing Support, who reconcile the gateway trace and reply to the customer."
        ),
        "keywords": ["deducted but", "money deducted", "payment failed", "pending payment", "gateway timeout"],
    },
    {
        "id": "KB-HR-002",
        "intent": "human_review",
        "title": "Human Review: Duplicate or Double Charge",
        "guidance": (
            "Any report of being charged twice for one order goes to Billing Support. The AI cannot verify "
            "settlement with the bank, so a human must confirm the duplicate and approve the reversal."
        ),
        "keywords": ["charged twice", "double charge", "duplicate charge", "deducted twice", "paid twice"],
    },
    {
        "id": "KB-HR-003",
        "intent": "human_review",
        "title": "Human Review: Suspected Fraud or Unauthorized Transaction",
        "guidance": (
            "If a customer says a purchase or charge was not authorized, or mentions fraud, a hacked account, "
            "or a stolen card, the AI must stop self-service actions and escalate immediately as urgent to "
            "Senior Support. Do not cancel, refund, or discuss account details further."
        ),
        "keywords": ["fraud", "unauthorized", "unauthorised", "did not authorize", "hacked", "stolen card", "not me"],
    },
    {
        "id": "KB-HR-004",
        "intent": "human_review",
        "title": "Human Review: Delivered but Not Received / Lost Package",
        "guidance": (
            "When tracking says delivered but the customer never received the package, or a parcel is reported "
            "lost or missing, the AI cannot decide between reship and refund. Escalate to Logistics Support, "
            "who investigate with the courier and give the final decision."
        ),
        "keywords": ["never received", "not received", "lost package", "missing package", "marked delivered"],
    },
    {
        "id": "KB-HR-005",
        "intent": "human_review",
        "title": "Human Review: High-Value Orders Need Manager Approval",
        "guidance": (
            "Cancellations and returns for any order totalling $200 or more are never auto-approved. The AI "
            "must collect the details and open a ticket for Senior Support, who approve or decline."
        ),
        "keywords": ["high value", "high-value", "large order", "manager approval"],
    },
    {
        "id": "KB-HR-006",
        "intent": "human_review",
        "title": "Human Review: Return Outside the Return Window",
        "guidance": (
            "If a customer asks to return an item after the return window in the Return Window Policy has "
            "passed, the AI must not approve or flatly refuse it. Open an exception-review ticket for Senior "
            "Support, who may approve a goodwill return."
        ),
        "keywords": ["return exception", "past return window", "too late to return", "outside return window"],
    },
    {
        "id": "KB-HR-007",
        "intent": "human_review",
        "title": "Human Review: Safety Hazard or Legal Complaint",
        "guidance": (
            "Reports of overheating, smoke, fire, electric shock, or injury, and any mention of lawyers, legal "
            "action or consumer court, are escalated immediately as urgent to Senior Support. The AI should "
            "advise the customer to stop using the product and not argue liability."
        ),
        "keywords": ["fire", "smoke", "overheating", "injury", "lawyer", "legal action", "consumer court"],
    },
    {
        "id": "KB-HR-008",
        "intent": "human_review",
        "title": "Human Review: Missing or Delayed Refund",
        "guidance": (
            "If a refund has not reached the customer after the timelines in the Refund Processing policy, "
            "Billing Support must trace it with the bank. The AI should open a ticket and not quote new dates."
        ),
        "keywords": ["refund not received", "refund missing", "where is my refund", "refund delayed", "still waiting for refund"],
    },
    {
        "id": "KB-HR-009",
        "intent": "human_review",
        "title": "Human Review: No Matching Policy (Final Decision by a Human)",
        "guidance": (
            "When the AI cannot find a relevant policy or verified record for a request, it must not guess. "
            "It hands the case to a human specialist, who gives the final decision and replies to the customer's inbox."
        ),
        "keywords": ["no matching policy", "out of policy", "special request", "exception request"],
    },
]


# Pristine copy used by the Supervisor Desk "Reset Demo DB" button.
INITIAL_KNOWLEDGE_BASE = copy.deepcopy(KNOWLEDGE_BASE)


def reset_knowledge_base():
    """Restore every policy (including supervisor edits and additions) to the demo baseline."""
    KNOWLEDGE_BASE.clear()
    KNOWLEDGE_BASE.extend(copy.deepcopy(INITIAL_KNOWLEDGE_BASE))
