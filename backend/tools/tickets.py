"""Ticket lifecycle management and human specialist escalation tools."""

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from langchain_core.tools import tool

try:
    from backend.mock_data import TICKETS, CUSTOMERS
except ImportError:
    from mock_data import TICKETS, CUSTOMERS

VALID_STATUSES = {"open", "assigned", "in_progress", "pending_customer", "resolved", "closed"}
VALID_PRIORITIES = {"low", "medium", "high", "urgent"}
VALID_TEAMS = {"billing_support", "logistics_support", "technical_support", "senior_support", "general_support"}


def _calculate_sla_deadline(priority: str, customer_tier: Optional[str] = None) -> str:
    now = datetime.now(timezone.utc)
    norm_tier = (customer_tier or "standard").lower()
    norm_prio = (priority or "medium").lower()

    if norm_tier in {"vip", "premium"} or norm_prio == "urgent":
        delta = timedelta(hours=2)
    elif norm_prio == "high":
        delta = timedelta(hours=4)
    elif norm_prio == "medium":
        delta = timedelta(hours=8)
    else:
        delta = timedelta(hours=24)

    return (now + delta).isoformat()


@tool
def create_support_ticket(
    title: str,
    category: str,
    priority: str,
    escalation_reason: str,
    customer_id: Optional[str] = "",
    order_id: Optional[str] = "",
    target_team: Optional[str] = "general_support",
    internal_notes: Optional[str] = "",
) -> str:
    """Create a structured support ticket for human specialist handoff.

    Args:
        title: Concise descriptive title of the case (e.g. 'Payment Deducted but Order Failed - ORD1004').
        category: Support category (e.g. 'payment_issue', 'order_tracking', 'cancellation', 'return_or_replacement').
        priority: Priority level: 'low', 'medium', 'high', or 'urgent'.
        escalation_reason: Specific factual justification for escalating to a human specialist.
        customer_id: Customer ID if identified (e.g. 'CUST001').
        order_id: Associated order ID if applicable.
        target_team: Specialist team ('billing_support', 'logistics_support', 'technical_support', 'senior_support', 'general_support').
        internal_notes: Technical summary of investigated facts, attempted self-service steps, and evidence.

    Returns:
        JSON string containing the created ticket ID, status, SLA deadline, and team routing.
    """
    norm_prio = priority.lower() if priority and priority.lower() in VALID_PRIORITIES else "medium"
    norm_team = target_team.lower() if target_team and target_team.lower() in VALID_TEAMS else "general_support"

    cust_tier = None
    if customer_id:
        cust = next((c for c in CUSTOMERS if c.get("id", "").upper() == customer_id.strip().upper()), None)
        if cust:
            cust_tier = cust.get("tier")

    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()
    sla_deadline = _calculate_sla_deadline(norm_prio, cust_tier)

    ticket_record = {
        "ticket_id": ticket_id,
        "title": title or f"Support Request [{category}]",
        "category": category or "general_inquiry",
        "priority": norm_prio,
        "status": "open",
        "escalation_reason": escalation_reason,
        "customer_id": customer_id.strip().upper() if customer_id else None,
        "order_id": order_id.strip().upper() if order_id else None,
        "target_team": norm_team,
        "assigned_to": None,
        "internal_notes": internal_notes or escalation_reason,
        "customer_safe_summary": f"Your case has been routed to our {norm_team.replace('_', ' ').title()} department.",
        "created_at": created_at,
        "sla_deadline": sla_deadline,
        "history": [
            {
                "timestamp": created_at,
                "event": "ticket_opened",
                "notes": "Ticket generated automatically by AI Support Escalation Agent.",
            }
        ],
    }

    TICKETS.append(ticket_record)

    return json.dumps({
        "success": True,
        "ticket_id": ticket_id,
        "status": "open",
        "priority": norm_prio,
        "target_team": norm_team,
        "sla_deadline": sla_deadline,
        "message": f"Support ticket '{ticket_id}' has been opened and assigned to {norm_team.replace('_', ' ').title()}."
    })


@tool
def update_ticket_status(ticket_id: str, new_status: str, notes: Optional[str] = "", assigned_to: Optional[str] = "") -> str:
    """Update ticket resolution lifecycle state.

    Lifecycle stages:
    'open' -> 'assigned' -> 'in_progress' -> 'pending_customer' -> 'resolved' -> 'closed'

    Args:
        ticket_id: Target ticket ID (e.g. 'TKT-B401A912').
        new_status: One of: 'open', 'assigned', 'in_progress', 'pending_customer', 'resolved', 'closed'.
        notes: Reason or outcome explanation for the status change.
        assigned_to: Specialist agent name (e.g. 'agent_sarah').

    Returns:
        JSON string indicating transition success and updated ticket summary.
    """
    if not ticket_id:
        return json.dumps({"success": False, "message": "ticket_id is required."})

    norm_status = new_status.strip().lower()
    if norm_status not in VALID_STATUSES:
        return json.dumps({
            "success": False,
            "message": f"Invalid status '{new_status}'. Allowed statuses: {', '.join(sorted(VALID_STATUSES))}."
        })

    norm_tid = ticket_id.strip().upper()
    target_ticket = next((t for t in TICKETS if t.get("ticket_id", "").upper() == norm_tid), None)

    if not target_ticket:
        return json.dumps({
            "success": False,
            "ticket_id": norm_tid,
            "message": f"Ticket '{norm_tid}' was not found in the ticketing system."
        })

    old_status = target_ticket.get("status", "open")
    now_str = datetime.now(timezone.utc).isoformat()

    target_ticket["status"] = norm_status
    if assigned_to:
        target_ticket["assigned_to"] = assigned_to

    if "history" not in target_ticket:
        target_ticket["history"] = []

    target_ticket["history"].append({
        "timestamp": now_str,
        "from_status": old_status,
        "to_status": norm_status,
        "assigned_to": target_ticket.get("assigned_to"),
        "notes": notes or f"Status transitioned from {old_status} to {norm_status}",
    })

    return json.dumps({
        "success": True,
        "ticket_id": norm_tid,
        "previous_status": old_status,
        "new_status": norm_status,
        "assigned_to": target_ticket.get("assigned_to"),
        "message": f"Ticket '{norm_tid}' status transitioned to '{norm_status}'."
    })


@tool
def search_tickets(customer_id: Optional[str] = "", order_id: Optional[str] = "", status: Optional[str] = "") -> str:
    """Search existing support tickets by customer ID, order ID, or status.

    Use this to identify existing open tickets before creating duplicates or to check ticket progress.
    """
    results = list(TICKETS)

    if customer_id:
        norm_cid = customer_id.strip().upper()
        results = [t for t in results if (t.get("customer_id") or "").upper() == norm_cid]

    if order_id:
        norm_oid = order_id.strip().upper()
        results = [t for t in results if (t.get("order_id") or "").upper() == norm_oid]

    if status:
        norm_st = status.strip().lower()
        results = [t for t in results if (t.get("status") or "").lower() == norm_st]

    summaries = [
        {
            "ticket_id": t["ticket_id"],
            "title": t.get("title"),
            "category": t.get("category"),
            "priority": t.get("priority"),
            "status": t.get("status"),
            "target_team": t.get("target_team"),
            "order_id": t.get("order_id"),
            "created_at": t.get("created_at"),
            "sla_deadline": t.get("sla_deadline"),
        }
        for t in results
    ]

    return json.dumps({
        "match_count": len(summaries),
        "tickets": summaries,
    })
