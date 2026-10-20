"""Safe simulated support action service for cancellation and return/replacement requests."""

import copy
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from backend.mock_data import ORDERS, reset_mock_data
except ImportError:
    from mock_data import ORDERS, reset_mock_data

# In-memory collection for return and replacement requests
RETURN_REQUESTS: Dict[str, Dict[str, Any]] = {}


def cancel_order(
    order_id: str,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Safely cancel an order if its status permits.

    Rule: Only 'processing' orders can be cancelled.
    Shipped, delivered, already cancelled, or unknown orders cannot be cancelled.

    Args:
        order_id: The ID of the order to cancel.
        reason: Optional cancellation reason.

    Returns:
        Structured result indicating success, action, order_id, message, and updated order.
    """
    if not order_id:
        return {
            "success": False,
            "action": "cancellation",
            "order_id": "",
            "message": "Order ID is required to cancel an order.",
            "order": None,
        }

    normalized_id = order_id.strip().upper()
    target_order = None

    for order in ORDERS:
        if order.get("id", "").upper() == normalized_id:
            target_order = order
            break

    if not target_order:
        return {
            "success": False,
            "action": "cancellation",
            "order_id": normalized_id,
            "message": f"Order '{normalized_id}' was not found in the system.",
            "order": None,
        }

    current_status = target_order.get("status", "").lower()

    if current_status == "cancelled":
        return {
            "success": False,
            "action": "cancellation",
            "order_id": normalized_id,
            "message": f"Order '{normalized_id}' is already cancelled.",
            "order": copy.deepcopy(target_order),
        }

    if current_status == "shipped":
        return {
            "success": False,
            "action": "cancellation",
            "order_id": normalized_id,
            "message": (
                f"Order '{normalized_id}' cannot be cancelled because it has already shipped. "
                "You may refuse delivery upon arrival or request a return once delivered."
            ),
            "order": copy.deepcopy(target_order),
        }

    if current_status == "delivered":
        return {
            "success": False,
            "action": "cancellation",
            "order_id": normalized_id,
            "message": (
                f"Order '{normalized_id}' cannot be cancelled because it has already been delivered. "
                "You may submit a return request instead."
            ),
            "order": copy.deepcopy(target_order),
        }

    if current_status != "processing":
        return {
            "success": False,
            "action": "cancellation",
            "order_id": normalized_id,
            "message": (
                f"Order '{normalized_id}' cannot be cancelled because its current status is '{current_status}'. "
                "Only orders in 'processing' status are eligible for cancellation."
            ),
            "order": copy.deepcopy(target_order),
        }

    # Action is permitted: update status in-place
    target_order["status"] = "cancelled"
    if reason:
        target_order["cancellation_reason"] = reason

    return {
        "success": True,
        "action": "cancellation",
        "order_id": normalized_id,
        "message": f"Order '{normalized_id}' has been successfully cancelled.",
        "order": copy.deepcopy(target_order),
    }


def request_return(
    order_id: str,
    request_type: str = "return",
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Safely record a return or replacement request for a delivered order.

    Rule: Only 'delivered' orders can be returned/replaced.
    Prevents duplicate active return requests for the same order.

    Args:
        order_id: The ID of the order.
        request_type: 'return' or 'replacement'.
        reason: Customer reason (e.g., damaged, defective, wrong item).

    Returns:
        Structured result indicating success, action, order_id, message, order, and return_request.
    """
    if not order_id:
        return {
            "success": False,
            "action": "return_or_replacement",
            "order_id": "",
            "message": "Order ID is required to request a return or replacement.",
            "order": None,
            "return_request": None,
        }

    normalized_id = order_id.strip().upper()
    valid_types = {"return", "replacement"}
    norm_type = request_type.lower() if request_type and request_type.lower() in valid_types else "return"

    target_order = None
    for order in ORDERS:
        if order.get("id", "").upper() == normalized_id:
            target_order = order
            break

    if not target_order:
        return {
            "success": False,
            "action": "return_or_replacement",
            "order_id": normalized_id,
            "message": f"Order '{normalized_id}' was not found in the system.",
            "order": None,
            "return_request": None,
        }

    current_status = target_order.get("status", "").lower()

    if current_status != "delivered":
        return {
            "success": False,
            "action": "return_or_replacement",
            "order_id": normalized_id,
            "message": (
                f"Return or replacement requests are only permitted for 'delivered' orders. "
                f"Order '{normalized_id}' is currently '{current_status}'."
            ),
            "order": copy.deepcopy(target_order),
            "return_request": None,
        }

    # Prevent duplicate active requests for the same order
    for req in RETURN_REQUESTS.values():
        if req.get("order_id") == normalized_id and req.get("status") in {"pending", "approved"}:
            return {
                "success": False,
                "action": "return_or_replacement",
                "order_id": normalized_id,
                "message": (
                    f"An active {req.get('request_type')} request ({req.get('request_id')}) "
                    f"already exists for order '{normalized_id}'."
                ),
                "order": copy.deepcopy(target_order),
                "return_request": copy.deepcopy(req),
            }

    # Action is permitted: record new request in separate collection
    request_id = f"RET-{uuid.uuid4().hex[:8].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()

    new_request = {
        "request_id": request_id,
        "order_id": normalized_id,
        "request_type": norm_type,
        "status": "pending",
        "reason": reason or "Customer requested return/replacement",
        "created_at": created_at,
    }

    RETURN_REQUESTS[request_id] = new_request

    return {
        "success": True,
        "action": "return_or_replacement",
        "order_id": normalized_id,
        "message": (
            f"{norm_type.capitalize()} request '{request_id}' for order '{normalized_id}' "
            "has been successfully recorded and is pending return inspection review."
        ),
        "order": copy.deepcopy(target_order),
        "return_request": copy.deepcopy(new_request),
    }


def get_return_request(request_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a return request by its ID."""
    if not request_id:
        return None
    normalized_id = request_id.strip().upper()
    for rid, req in RETURN_REQUESTS.items():
        if rid.upper() == normalized_id:
            return copy.deepcopy(req)
    return None


def list_return_requests(order_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List return requests, optionally filtered by order ID."""
    results = list(RETURN_REQUESTS.values())
    if order_id:
        norm_order = order_id.strip().upper()
        results = [r for r in results if r.get("order_id", "").upper() == norm_order]
    return copy.deepcopy(results)


def clear_action_data() -> None:
    """Reset both return requests and mock data to initial baseline."""
    RETURN_REQUESTS.clear()
    reset_mock_data()
