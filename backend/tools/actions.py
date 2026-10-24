"""Guarded mutation action tools for e-commerce customer support."""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from langchain_core.tools import tool

try:
    from backend.mock_data import ORDERS, RETURN_REQUESTS
except ImportError:
    from mock_data import ORDERS, RETURN_REQUESTS


@tool
def cancel_order(order_id: str, reason: Optional[str] = "") -> str:
    """Safely cancel an order if eligible.

    Eligibility Rules:
    - Order status must be strictly 'processing'.
    - Shipped, delivered, or already cancelled orders cannot be cancelled.

    Args:
        order_id: The order ID to cancel (e.g., 'ORD1002').
        reason: Optional customer-specified cancellation reason.

    Returns:
        JSON string indicating success or failure, with explanatory message.
    """
    if not order_id or not isinstance(order_id, str):
        return json.dumps({"success": False, "message": "Order ID is required to cancel an order."})

    norm_id = order_id.strip().upper()
    target_order = next((o for o in ORDERS if o.get("id", "").upper() == norm_id), None)

    if not target_order:
        return json.dumps({
            "success": False,
            "order_id": norm_id,
            "message": f"Order '{norm_id}' was not found in the system."
        })

    current_status = target_order.get("status", "").lower()

    if current_status == "cancelled":
        return json.dumps({
            "success": False,
            "order_id": norm_id,
            "message": f"Order '{norm_id}' is already cancelled."
        })

    if current_status == "shipped":
        return json.dumps({
            "success": False,
            "order_id": norm_id,
            "message": (
                f"Order '{norm_id}' cannot be cancelled because it has already shipped. "
                "You may refuse delivery upon arrival or submit a return request once delivered."
            )
        })

    if current_status == "delivered":
        return json.dumps({
            "success": False,
            "order_id": norm_id,
            "message": (
                f"Order '{norm_id}' cannot be cancelled because it has already been delivered. "
                "You may submit a return or replacement request instead."
            )
        })

    if current_status != "processing":
        return json.dumps({
            "success": False,
            "order_id": norm_id,
            "message": f"Order '{norm_id}' is currently in '{current_status}' status. Only orders in 'processing' status can be cancelled."
        })

    # Permitted: mutate in-memory status
    target_order["status"] = "cancelled"
    target_order["cancellation_reason"] = reason or "Customer requested cancellation"
    target_order["cancelled_at"] = datetime.now(timezone.utc).isoformat()

    return json.dumps({
        "success": True,
        "action": "cancel_order",
        "order_id": norm_id,
        "new_status": "cancelled",
        "message": f"Order '{norm_id}' has been successfully cancelled. Any temporary authorization hold will release within 3-5 business days."
    })


@tool
def request_return(order_id: str, request_type: str = "return", reason: Optional[str] = "") -> str:
    """Record a return or replacement request for a delivered order and generate a return shipping label.

    Eligibility Rules:
    - Order status must be strictly 'delivered'.
    - An active return or replacement cannot already exist.

    Args:
        order_id: The delivered order ID (e.g., 'ORD1001').
        request_type: 'return' or 'replacement' (default: 'return').
        reason: Specific problem description (e.g., defective, damaged, wrong item received).

    Returns:
        JSON string with confirmation, return authorization ID (RET-xxxx), and simulated return label details.
    """
    if not order_id or not isinstance(order_id, str):
        return json.dumps({"success": False, "message": "Order ID is required to request a return or replacement."})

    norm_id = order_id.strip().upper()
    norm_type = "replacement" if "replace" in str(request_type).lower() else "return"

    target_order = next((o for o in ORDERS if o.get("id", "").upper() == norm_id), None)
    if not target_order:
        return json.dumps({
            "success": False,
            "order_id": norm_id,
            "message": f"Order '{norm_id}' was not found in the system."
        })

    current_status = target_order.get("status", "").lower()
    if current_status != "delivered":
        return json.dumps({
            "success": False,
            "order_id": norm_id,
            "message": (
                f"Return or replacement requests are only permitted for 'delivered' orders. "
                f"Order '{norm_id}' is currently '{current_status}'."
            )
        })

    # Prevent duplicate active returns
    for req in RETURN_REQUESTS:
        if req.get("order_id", "").upper() == norm_id and req.get("status") in {"pending", "approved"}:
            return json.dumps({
                "success": False,
                "order_id": norm_id,
                "message": (
                    f"An active {req.get('request_type')} request ({req.get('request_id')}) "
                    f"already exists for order '{norm_id}'."
                )
            })

    # Generate return authorization and pre-paid shipping label
    request_id = f"RET-{uuid.uuid4().hex[:8].upper()}"
    tracking_no = f"1Z999AA10{uuid.uuid4().hex[:8].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()

    new_return = {
        "request_id": request_id,
        "order_id": norm_id,
        "request_type": norm_type,
        "status": "approved",
        "reason": reason or f"Customer requested {norm_type}",
        "return_label": {
            "carrier": "UPS Ground Return",
            "tracking_number": tracking_no,
            "download_url": f"https://nextstore.demo/labels/{request_id}.pdf",
            "instructions": "Attach pre-paid shipping label to outer box and drop off at any authorized courier location.",
        },
        "created_at": created_at,
    }

    RETURN_REQUESTS.append(new_return)

    return json.dumps({
        "success": True,
        "action": "request_return",
        "order_id": norm_id,
        "request_id": request_id,
        "request_type": norm_type,
        "status": "approved",
        "return_label": new_return["return_label"],
        "message": (
            f"{norm_type.capitalize()} request '{request_id}' for order '{norm_id}' has been approved. "
            f"Pre-paid return label tracking number: {tracking_no}."
        )
    })


@tool
def initiate_refund(order_id: str, reason: Optional[str] = "") -> str:
    """Initiate a simulated refund authorization for an eligible cancelled or returned order.

    Rules:
    - Order must be in 'cancelled' status or have an approved return request.
    - Simulates payment gateway credit reversal without moving real financial funds.

    Args:
        order_id: Target order ID (e.g., 'ORD1002').
        reason: Explanation for refund (e.g. 'Order cancelled before dispatch').

    Returns:
        JSON string with refund authorization ID, amount, and settlement timeline.
    """
    if not order_id or not isinstance(order_id, str):
        return json.dumps({"success": False, "message": "Order ID is required to initiate a refund."})

    norm_id = order_id.strip().upper()
    target_order = next((o for o in ORDERS if o.get("id", "").upper() == norm_id), None)

    if not target_order:
        return json.dumps({
            "success": False,
            "order_id": norm_id,
            "message": f"Order '{norm_id}' was not found in the system."
        })

    status = target_order.get("status", "").lower()
    has_approved_return = any(
        r.get("order_id", "").upper() == norm_id and r.get("status") in {"approved", "completed"}
        for r in RETURN_REQUESTS
    )

    if status != "cancelled" and not has_approved_return:
        return json.dumps({
            "success": False,
            "order_id": norm_id,
            "message": (
                f"Refund cannot be initiated for order '{norm_id}'. "
                "Refunds are only authorized after an order has been cancelled or an approved return is logged."
            )
        })

    refund_id = f"RFD-{uuid.uuid4().hex[:8].upper()}"
    amount = target_order.get("total_amount", 0.0)

    return json.dumps({
        "success": True,
        "action": "initiate_refund",
        "order_id": norm_id,
        "refund_id": refund_id,
        "amount": amount,
        "settlement_timeline": "3 to 5 business days",
        "message": f"Refund of ${amount:.2f} initiated (Auth ID: {refund_id}). Funds will credit back to original payment method in 3-5 business days."
    })
