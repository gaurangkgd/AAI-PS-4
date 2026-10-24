"""Read-only factual investigation and context retrieval tools."""

import json
import re
from typing import Optional
from langchain_core.tools import tool

try:
    from backend.mock_data import CUSTOMERS, ORDERS, PAYMENTS, RETURN_REQUESTS, TICKETS
    from backend.knowledge_base import KNOWLEDGE_BASE
except ImportError:
    from mock_data import CUSTOMERS, ORDERS, PAYMENTS, RETURN_REQUESTS, TICKETS
    from knowledge_base import KNOWLEDGE_BASE


@tool
def lookup_order(order_id: str) -> str:
    """Look up verified order details by order ID (e.g., 'ORD1001').

    Returns a JSON string containing the order status, total amount,
    customer ID, list of ordered items, and order timestamp.
    If not found, returns an explanatory error message.
    """
    if not order_id or not isinstance(order_id, str):
        return json.dumps({"error": "A valid order_id string is required."})

    norm_id = order_id.strip().upper()
    for o in ORDERS:
        if o.get("id", "").upper() == norm_id:
            return json.dumps({
                "found": True,
                "order_id": o["id"],
                "customer_id": o.get("customer_id"),
                "status": o.get("status"),
                "total_amount": o.get("total_amount"),
                "created_at": o.get("created_at"),
                "items": o.get("items", []),
            })

    return json.dumps({
        "found": False,
        "order_id": norm_id,
        "message": f"Order '{norm_id}' was not found in the verified orders database."
    })


@tool
def lookup_payment(order_id: str) -> str:
    """Look up verified payment transaction records associated with an order ID.

    Returns a JSON string containing all transaction references, amounts,
    payment methods, and gateway statuses (successful, failed, pending).
    """
    if not order_id or not isinstance(order_id, str):
        return json.dumps({"error": "A valid order_id string is required."})

    norm_id = order_id.strip().upper()
    matched_payments = [
        p for p in PAYMENTS if p.get("order_id", "").upper() == norm_id
    ]

    if not matched_payments:
        return json.dumps({
            "order_id": norm_id,
            "has_payments": False,
            "message": f"No payment transaction records found for order '{norm_id}'."
        })

    return json.dumps({
        "order_id": norm_id,
        "has_payments": True,
        "count": len(matched_payments),
        "payments": matched_payments,
    })


@tool
def lookup_customer(customer_id: str) -> str:
    """Look up customer account profile, subscription status, loyalty tier, and prior history.

    Returns a JSON string with customer name, email, tier (premium, vip, standard),
    subscription state, account status, total orders placed, and past support tickets.
    """
    if not customer_id or not isinstance(customer_id, str):
        return json.dumps({"error": "A valid customer_id string is required."})

    norm_id = customer_id.strip().upper()
    cust = next((c for c in CUSTOMERS if c.get("id", "").upper() == norm_id), None)

    if not cust:
        return json.dumps({
            "found": False,
            "customer_id": norm_id,
            "message": f"Customer '{norm_id}' not found in customer registry."
        })

    cust_orders = [o["id"] for o in ORDERS if o.get("customer_id", "").upper() == norm_id]
    cust_tickets = [
        {
            "ticket_id": t["ticket_id"],
            "title": t.get("title"),
            "status": t.get("status"),
            "priority": t.get("priority"),
            "category": t.get("category"),
        }
        for t in TICKETS
        if t.get("customer_id", "").upper() == norm_id
    ]

    return json.dumps({
        "found": True,
        "customer_id": cust["id"],
        "name": cust.get("name"),
        "email": cust.get("email"),
        "tier": cust.get("tier"),
        "subscription": cust.get("subscription"),
        "account_status": cust.get("account_status"),
        "order_ids": cust_orders,
        "order_count": len(cust_orders),
        "prior_tickets": cust_tickets,
        "prior_ticket_count": len(cust_tickets),
    })


@tool
def search_knowledge_base(query: str, category: Optional[str] = None) -> str:
    """Search official support policies, troubleshooting guides, return conditions, and FAQs.

    Args:
        query: Search keywords or question describing the customer issue.
        category: Optional category filter (e.g. 'cancellation', 'return_or_replacement',
                  'payment_issue', 'order_tracking', 'refund_status', 'account_issue').

    Returns a JSON string with the most relevant policy guidance articles.
    """
    if not query or not isinstance(query, str):
        return json.dumps({"error": "A search query string is required."})

    clean_q = query.lower().strip()
    words = set(re.findall(r"\b[a-z]{3,}\b", clean_q))

    scored = []
    for entry in KNOWLEDGE_BASE:
        score = 0
        intent = entry.get("intent", "").lower()
        if category and category.lower() in intent:
            score += 10

        keywords = entry.get("keywords", [])
        for kw in keywords:
            if kw.lower() in clean_q:
                score += 4

        for w in words:
            if w in entry.get("title", "").lower():
                score += 2
            if w in entry.get("guidance", "").lower():
                score += 1

        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: -x[0])
    top_entries = [
        {
            "id": item[1].get("id"),
            "title": item[1].get("title"),
            "intent": item[1].get("intent"),
            "guidance": item[1].get("guidance"),
        }
        for item in scored[:3]
    ]

    return json.dumps({
        "query": query,
        "matched_count": len(top_entries),
        "articles": top_entries,
    })


@tool
def check_return_eligibility(order_id: str) -> str:
    """Check if an order is currently eligible for a return or replacement.

    Rules:
    - Order status must be strictly 'delivered'.
    - Rejects if an active pending or approved return request already exists.
    Returns JSON with eligibility boolean, reason, and any existing return request details.
    """
    if not order_id or not isinstance(order_id, str):
        return json.dumps({"error": "A valid order_id string is required."})

    norm_id = order_id.strip().upper()
    order = next((o for o in ORDERS if o.get("id", "").upper() == norm_id), None)

    if not order:
        return json.dumps({
            "order_id": norm_id,
            "is_eligible": False,
            "reason": f"Order '{norm_id}' not found."
        })

    status = order.get("status", "").lower()
    if status != "delivered":
        return json.dumps({
            "order_id": norm_id,
            "current_status": status,
            "is_eligible": False,
            "reason": (
                f"Order '{norm_id}' is currently in '{status}' status. "
                "Only orders in 'delivered' status are eligible for return or replacement."
            )
        })

    # Check for existing return requests
    existing = [
        r for r in RETURN_REQUESTS
        if r.get("order_id", "").upper() == norm_id and r.get("status") in {"pending", "approved"}
    ]
    if existing:
        return json.dumps({
            "order_id": norm_id,
            "current_status": status,
            "is_eligible": False,
            "has_active_return": True,
            "existing_return_id": existing[0].get("request_id"),
            "reason": (
                f"An active return or replacement request ({existing[0].get('request_id')}) "
                f"already exists for order '{norm_id}'."
            )
        })

    return json.dumps({
        "order_id": norm_id,
        "current_status": "delivered",
        "is_eligible": True,
        "reason": f"Order '{norm_id}' is delivered and has no active returns. Eligible for return or replacement.",
        "return_window_days": 14,
    })
