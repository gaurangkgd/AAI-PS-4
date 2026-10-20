"""Read-only order and payment investigation service for customer support."""

import copy
import re
from typing import Any, Dict, Optional

try:
    from backend.mock_data import ORDERS, PAYMENTS
except ImportError:
    from mock_data import ORDERS, PAYMENTS

ORDER_ID_PATTERN = re.compile(r"\b(ORD\d{4,})\b", re.IGNORECASE)


def extract_order_id(message: str) -> Optional[str]:
    """Extract and normalize an order ID from the user's message.

    Returns the normalized uppercase order ID (e.g. 'ORD1001') if found,
    or None if no matching pattern is present.
    """
    if not message or not isinstance(message, str):
        return None
    match = ORDER_ID_PATTERN.search(message)
    if match:
        return match.group(1).upper()
    return None


def investigate_order_context(message: str, order_id: Optional[str] = None) -> Dict[str, Any]:
    """Perform a read-only investigation on order and payment records.

    Inspects in-memory mock data without issuing HTTP requests or mutating data.

    Returns:
        Dict representing InvestigationResult:
        - attempted: bool
        - order_id: Optional[str]
        - status: "order_id_required" | "order_not_found" | "found"
        - order: Optional[Dict]
        - payments: Optional[List[Dict]]
        - summary: Optional[str]
    """
    target_order_id = extract_order_id(message) or (
        order_id.strip().upper() if order_id and isinstance(order_id, str) and order_id.strip() else None
    )

    if not target_order_id:
        return {
            "attempted": False,
            "order_id": None,
            "status": "order_id_required",
            "order": None,
            "payments": None,
            "summary": "An order ID (e.g., ORD1001) is required to investigate order status and payment history.",
        }

    # Search for matching order (read-only, deepcopy to prevent accidental mutation)
    matched_order = None
    for o in ORDERS:
        if o.get("id", "").upper() == target_order_id:
            matched_order = copy.deepcopy(o)
            break

    if not matched_order:
        return {
            "attempted": True,
            "order_id": target_order_id,
            "status": "order_not_found",
            "order": None,
            "payments": None,
            "summary": f"No order records found for order ID '{target_order_id}'.",
        }

    # Retrieve associated payment records
    matched_payments = [
        copy.deepcopy(p)
        for p in PAYMENTS
        if p.get("order_id", "").upper() == target_order_id
    ]

    # Generate factual summary strictly based on retrieved data
    customer_id = matched_order.get("customer_id", "Unknown")
    order_status = matched_order.get("status", "Unknown")
    total_amount = matched_order.get("total_amount", 0.0)

    if matched_payments:
        pay_summaries = [
            f"{p.get('status', 'unknown')} (Ref: {p.get('transaction_ref', 'N/A')})"
            for p in matched_payments
        ]
        payment_text = f"Payment records ({len(matched_payments)}): " + ", ".join(pay_summaries)
    else:
        payment_text = "No associated payment records found."

    summary = (
        f"Order {target_order_id} for customer {customer_id} is currently '{order_status}' "
        f"(Total: ${total_amount:.2f}). {payment_text}"
    )

    return {
        "attempted": True,
        "order_id": target_order_id,
        "status": "found",
        "order": matched_order,
        "payments": matched_payments,
        "summary": summary,
    }
