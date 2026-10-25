"""Fictional in-memory mock data for e-commerce store."""

import copy
import uuid
from datetime import datetime, timedelta, timezone

try:
    from backend.knowledge_base import reset_knowledge_base
except ImportError:
    from knowledge_base import reset_knowledge_base


def _ago(days=0, hours=0, minutes=0):
    """ISO timestamp relative to server start so demo order ages stay realistic on any date."""
    moment = datetime.now(timezone.utc) - timedelta(days=days, hours=hours, minutes=minutes)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


CUSTOMERS = [
    {
        "id": "CUST001",
        "name": "Alice Johnson",
        "email": "alice.johnson@example.com",
        "tier": "premium",
        "subscription": "active",
        "phone": "+1-555-0101",
        "account_status": "active",
        "joined_date": "2024-03-15T08:00:00Z",
    },
    {
        "id": "CUST002",
        "name": "Bob Smith",
        "email": "bob.smith@example.com",
        "tier": "standard",
        "subscription": "none",
        "phone": "+1-555-0102",
        "account_status": "active",
        "joined_date": "2024-06-20T10:30:00Z",
    },
    {
        "id": "CUST003",
        "name": "Charlie Davis",
        "email": "charlie.davis@example.com",
        "tier": "standard",
        "subscription": "expired",
        "phone": "+1-555-0103",
        "account_status": "active",
        "joined_date": "2024-09-01T12:00:00Z",
    },
    {
        "id": "CUST004",
        "name": "Diana Lee",
        "email": "diana.lee@example.com",
        "tier": "vip",
        "subscription": "active",
        "phone": "+1-555-0104",
        "account_status": "active",
        "joined_date": "2023-11-10T14:45:00Z",
    },
    {
        "id": "CUST999",
        "name": "Evan Wright",
        "email": "evan.wright@example.com",
        "tier": "standard",
        "subscription": "none",
        "phone": "+1-555-0199",
        "account_status": "active",
        "joined_date": "2025-01-05T09:15:00Z",
    },
]

PRODUCTS = [
    {
        "id": "PROD001",
        "name": "Wireless Noise-Canceling Headphones",
        "category": "Electronics",
        "price": 129.99,
        "stock": 45,
    },
    {
        "id": "PROD002",
        "name": "Ergonomic Mechanical Keyboard",
        "category": "Electronics",
        "price": 89.50,
        "stock": 20,
    },
    {
        "id": "PROD003",
        "name": "Ultra-Light Running Shoes",
        "category": "Apparel",
        "price": 74.99,
        "stock": 15,
    },
    {
        "id": "PROD004",
        "name": "Stainless Steel Thermal Water Bottle",
        "category": "Home & Kitchen",
        "price": 24.95,
        "stock": 100,
    },
    {
        "id": "PROD005",
        "name": "USB-C Multi-Port Hub",
        "category": "Electronics",
        "price": 39.99,
        "stock": 0,
    },
    {
        "id": "PROD006",
        "name": "Organic Cotton Hoodie",
        "category": "Apparel",
        "price": 54.00,
        "stock": 30,
    },
]

ORDERS = [
    {
        "id": "ORD1001",
        "customer_id": "CUST001",
        "items": [
            {
                "product_id": "PROD001",
                "name": "Wireless Noise-Canceling Headphones",
                "quantity": 1,
                "unit_price": 129.99,
            }
        ],
        "total_amount": 129.99,
        "status": "delivered",
        "created_at": _ago(days=14),
        "delivered_at": _ago(days=9),
    },
    {
        "id": "ORD1002",
        "customer_id": "CUST001",
        "items": [
            {
                "product_id": "PROD004",
                "name": "Stainless Steel Thermal Water Bottle",
                "quantity": 2,
                "unit_price": 24.95,
            }
        ],
        "total_amount": 49.90,
        "status": "processing",
        "created_at": _ago(days=2),
    },
    {
        "id": "ORD1003",
        "customer_id": "CUST002",
        "items": [
            {
                "product_id": "PROD002",
                "name": "Ergonomic Mechanical Keyboard",
                "quantity": 1,
                "unit_price": 89.50,
            }
        ],
        "total_amount": 89.50,
        "status": "shipped",
        "created_at": _ago(days=5),
    },
    {
        "id": "ORD1004",
        "customer_id": "CUST003",
        "items": [
            {
                "product_id": "PROD005",
                "name": "USB-C Multi-Port Hub",
                "quantity": 1,
                "unit_price": 39.99,
            }
        ],
        "total_amount": 39.99,
        "status": "payment_failed",
        "created_at": _ago(days=1, hours=3),
    },
    {
        "id": "ORD1005",
        "customer_id": "CUST004",
        "items": [
            {
                "product_id": "PROD003",
                "name": "Ultra-Light Running Shoes",
                "quantity": 1,
                "unit_price": 74.99,
            }
        ],
        "total_amount": 74.99,
        "status": "pending_payment",
        "created_at": _ago(days=1, hours=1),
    },
    {
        "id": "ORD1006",
        "customer_id": "CUST002",
        "items": [
            {
                "product_id": "PROD006",
                "name": "Organic Cotton Hoodie",
                "quantity": 1,
                "unit_price": 54.00,
            }
        ],
        "total_amount": 54.00,
        "status": "delivered",
        "created_at": _ago(days=50),
        "delivered_at": _ago(days=45),
    },
]

PAYMENTS = [
    {
        "id": "PAY2001",
        "order_id": "ORD1001",
        "amount": 129.99,
        "status": "successful",
        "payment_method": "credit_card",
        "transaction_ref": "TXN-908123-SUCCESS",
        "timestamp": _ago(days=14, minutes=-2),
    },
    {
        "id": "PAY2002",
        "order_id": "ORD1002",
        "amount": 49.90,
        "status": "successful",
        "payment_method": "upi",
        "transaction_ref": "TXN-908456-SUCCESS",
        "timestamp": _ago(days=2, minutes=-1),
    },
    {
        "id": "PAY2003",
        "order_id": "ORD1003",
        "amount": 89.50,
        "status": "successful",
        "payment_method": "debit_card",
        "transaction_ref": "TXN-908789-SUCCESS",
        "timestamp": _ago(days=5, minutes=-2),
    },
    {
        "id": "PAY2004",
        "order_id": "ORD1004",
        "amount": 39.99,
        "status": "failed",
        "payment_method": "credit_card",
        "transaction_ref": "TXN-909012-FAILED",
        "timestamp": _ago(days=1, hours=3, minutes=-1),
    },
    {
        "id": "PAY2005",
        "order_id": "ORD1005",
        "amount": 74.99,
        "status": "pending",
        "payment_method": "net_banking",
        "transaction_ref": "TXN-909345-PENDING",
        "timestamp": _ago(days=1, hours=1, minutes=-1),
    },
    {
        "id": "PAY2006",
        "order_id": "ORD1006",
        "amount": 54.00,
        "status": "successful",
        "payment_method": "credit_card",
        "transaction_ref": "TXN-907555-SUCCESS",
        "timestamp": _ago(days=50, minutes=-2),
    },
]

# Baseline support tickets for live supervisor metrics demonstration
INITIAL_TICKETS = [
    {
        "ticket_id": "TKT-B401A912",
        "customer_id": "CUST003",
        "session_id": "demo-seed-session-1",
        "category": "payment_issue",
        "priority": "high",
        "status": "open",
        "original_message": "Money deducted for ORD1004 but order shows payment failed.",
        "escalation_reason": "Verified payment failure requiring gateway reconciliation.",
        "investigation_summary": "Order ORD1004 status payment_failed, transaction TXN-909012-FAILED.",
        "title": "Payment Deducted but Order Failed - ORD1004",
        "target_team": "billing_support",
        "order_id": "ORD1004",
        "customer_safe_summary": "Your payment case has been referred to our Billing Support team.",
        "is_reused": False,
        "created_at": "2026-10-20T10:00:00Z",
        "assigned_to": "agent_sarah",
        "sla_deadline": "2026-10-20T14:00:00Z",
    },
    {
        "ticket_id": "TKT-C712E340",
        "customer_id": "CUST002",
        "session_id": "demo-seed-session-2",
        "category": "order_tracking",
        "priority": "medium",
        "status": "in_progress",
        "original_message": "Courier tracking link has not updated in 48 hours for ORD1003.",
        "escalation_reason": "Courier delivery milestone investigation requested.",
        "investigation_summary": "Order ORD1003 shipped on Oct 15.",
        "title": "Courier Tracking Inactive - ORD1003",
        "target_team": "logistics_support",
        "order_id": "ORD1003",
        "customer_safe_summary": "Logistics team is actively coordinating with courier partner.",
        "is_reused": False,
        "created_at": "2026-10-21T11:30:00Z",
        "assigned_to": "agent_dave",
        "sla_deadline": "2026-10-21T17:30:00Z",
    },
    {
        "ticket_id": "TKT-D983F112",
        "customer_id": "CUST001",
        "session_id": "demo-seed-session-3",
        "category": "return_or_replacement",
        "priority": "low",
        "status": "resolved",
        "original_message": "Ear cushions missing from headphones in ORD1001.",
        "escalation_reason": "Replacement accessory dispatch confirmed.",
        "investigation_summary": "Return authorization RET-AA01 created.",
        "title": "Missing Accessory Claim - ORD1001",
        "target_team": "logistics_support",
        "order_id": "ORD1001",
        "customer_safe_summary": "Replacement accessories were dispatched.",
        "is_reused": False,
        "created_at": "2026-10-22T09:15:00Z",
        "assigned_to": "agent_maya",
        "sla_deadline": "2026-10-22T15:15:00Z",
    },
]

INITIAL_RETURNS = [
    {
        "request_id": "RET-AA01B890",
        "order_id": "ORD1001",
        "request_type": "replacement",
        "status": "completed",
        "reason": "Missing ear cushions",
        "created_at": "2026-10-22T09:20:00Z",
    }
]

INITIAL_CSAT = [
    {
        "ticket_id": "TKT-D983F112",
        "customer_id": "CUST001",
        "rating": 5,
        "feedback": "Quick resolution and courteous support!",
        "timestamp": "2026-10-22T16:00:00Z",
    }
]

INITIAL_NOTIFICATIONS = [
    {
        "id": "NTF-SEED0001",
        "customer_id": "CUST001",
        "type": "ticket_resolved",
        "title": "Case TKT-D983F112 resolved",
        "message": "Replacement ear cushions for ORD1001 have been dispatched and should arrive in 2-3 business days. Sorry for the inconvenience!",
        "ticket_id": "TKT-D983F112",
        "order_id": "ORD1001",
        "from_agent": "agent_maya",
        "created_at": "2026-10-22T15:00:00Z",
        "read": True,
    },
    {
        "id": "NTF-SEED0002",
        "customer_id": "CUST002",
        "type": "ticket_assigned",
        "title": "A specialist is working on case TKT-C712E340",
        "message": "Our logistics specialist agent_dave is coordinating with the courier about the stalled tracking for ORD1003.",
        "ticket_id": "TKT-C712E340",
        "order_id": "ORD1003",
        "from_agent": "agent_dave",
        "created_at": "2026-10-21T12:00:00Z",
        "read": False,
    },
    {
        "id": "NTF-SEED0003",
        "customer_id": "CUST003",
        "type": "ticket_opened",
        "title": "Case TKT-B401A912 opened",
        "message": "Your payment issue for ORD1004 was referred to Billing Support. We will reply here as soon as a specialist reviews it.",
        "ticket_id": "TKT-B401A912",
        "order_id": "ORD1004",
        "from_agent": None,
        "created_at": "2026-10-20T10:01:00Z",
        "read": False,
    },
]

# Live working collections
TICKETS = copy.deepcopy(INITIAL_TICKETS)
RETURN_REQUESTS = copy.deepcopy(INITIAL_RETURNS)
CSAT_RATINGS = copy.deepcopy(INITIAL_CSAT)
NOTIFICATIONS = copy.deepcopy(INITIAL_NOTIFICATIONS)

INITIAL_CUSTOMERS = copy.deepcopy(CUSTOMERS)
INITIAL_PRODUCTS = copy.deepcopy(PRODUCTS)
INITIAL_ORDERS = copy.deepcopy(ORDERS)
INITIAL_PAYMENTS = copy.deepcopy(PAYMENTS)


def add_notification(customer_id, notif_type, title, message, ticket_id=None, order_id=None, from_agent=None):
    """Append an inbox notification for a customer. Silently skips guests (no customer_id)."""
    if not customer_id:
        return None
    entry = {
        "id": f"NTF-{uuid.uuid4().hex[:8].upper()}",
        "customer_id": customer_id.strip().upper(),
        "type": notif_type,
        "title": title,
        "message": message,
        "ticket_id": ticket_id,
        "order_id": order_id,
        "from_agent": from_agent,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read": False,
    }
    NOTIFICATIONS.append(entry)
    return entry


def reset_mock_data():
    """Reset all in-memory collections (including AI policies) to the initial demo baseline."""
    CUSTOMERS.clear()
    CUSTOMERS.extend(copy.deepcopy(INITIAL_CUSTOMERS))
    PRODUCTS.clear()
    PRODUCTS.extend(copy.deepcopy(INITIAL_PRODUCTS))
    ORDERS.clear()
    ORDERS.extend(copy.deepcopy(INITIAL_ORDERS))
    PAYMENTS.clear()
    PAYMENTS.extend(copy.deepcopy(INITIAL_PAYMENTS))
    TICKETS.clear()
    TICKETS.extend(copy.deepcopy(INITIAL_TICKETS))
    RETURN_REQUESTS.clear()
    RETURN_REQUESTS.extend(copy.deepcopy(INITIAL_RETURNS))
    CSAT_RATINGS.clear()
    CSAT_RATINGS.extend(copy.deepcopy(INITIAL_CSAT))
    NOTIFICATIONS.clear()
    NOTIFICATIONS.extend(copy.deepcopy(INITIAL_NOTIFICATIONS))
    reset_knowledge_base()
