"""In-memory ticket service for customer support escalation."""

import copy
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# In-memory storage for support tickets
_TICKETS: Dict[str, Dict[str, Any]] = {}


def generate_ticket_id() -> str:
    """Generate a unique ticket ID formatted as TKT-<hex>."""
    return f"TKT-{uuid.uuid4().hex[:8].upper()}"


def create_ticket(
    session_id: str,
    original_message: str,
    category: str,
    escalation_reason: str,
    customer_id: Optional[str] = None,
    priority: str = "medium",
    status: str = "open",
    investigation_summary: Optional[str] = None,
) -> Dict[str, Any]:
    """Create and store a new support escalation ticket.

    Args:
        session_id: The conversation session ID.
        original_message: Customer's message triggering escalation.
        category: Support category or detected intent.
        escalation_reason: Factual reason for escalating to human review.
        customer_id: Customer ID if verified from order records; otherwise None.
        priority: 'low', 'medium', 'high', or 'urgent'.
        status: 'open', 'in_progress', or 'resolved'.
        investigation_summary: Summary of verified order/payment investigation.

    Returns:
        The newly created ticket dictionary.
    """
    valid_priorities = {"low", "medium", "high", "urgent"}
    valid_statuses = {"open", "in_progress", "resolved"}

    normalized_priority = priority.lower() if priority else "medium"
    if normalized_priority not in valid_priorities:
        normalized_priority = "medium"

    normalized_status = status.lower() if status else "open"
    if normalized_status not in valid_statuses:
        normalized_status = "open"

    ticket_id = generate_ticket_id()
    created_at = datetime.now(timezone.utc).isoformat()

    ticket_data = {
        "ticket_id": ticket_id,
        "customer_id": customer_id if customer_id else None,
        "session_id": session_id,
        "category": category,
        "priority": normalized_priority,
        "status": normalized_status,
        "original_message": original_message,
        "escalation_reason": escalation_reason,
        "investigation_summary": investigation_summary,
        "created_at": created_at,
    }

    _TICKETS[ticket_id] = ticket_data
    return copy.deepcopy(ticket_data)


def get_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a ticket by its ID (case-insensitive lookup)."""
    if not ticket_id:
        return None
    normalized_id = ticket_id.strip().upper()
    for tid, ticket in _TICKETS.items():
        if tid.upper() == normalized_id:
            return copy.deepcopy(ticket)
    return None


def list_tickets(
    status: Optional[str] = None,
    category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List tickets with optional filtering by status and/or category."""
    results = list(_TICKETS.values())

    if status:
        target_status = status.strip().lower()
        results = [t for t in results if t.get("status", "").lower() == target_status]

    if category:
        target_category = category.strip().lower()
        results = [t for t in results if t.get("category", "").lower() == target_category]

    return copy.deepcopy(results)


def clear_tickets() -> None:
    """Clear all tickets from in-memory storage (used for test isolation)."""
    _TICKETS.clear()
