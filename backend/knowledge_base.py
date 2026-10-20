"""Local demo support knowledge base with fictional policies and troubleshooting articles."""

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
]
