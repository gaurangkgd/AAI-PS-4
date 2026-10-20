"""Customer Context Agent.

The second specialized agent in the Agentic Customer Support System (PS-04).
Responsible for safely resolving and structuring customer context from incoming
messages, order references, and mock database records while strictly preserving
privacy boundaries and read-only access guarantees.
"""

import copy
import logging
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

try:
    from backend.mock_data import ORDERS
    from backend.ticket_service import list_tickets
except ImportError:
    from mock_data import ORDERS
    from ticket_service import list_tickets

logger = logging.getLogger(__name__)

CUSTOMER_ID_PATTERN = re.compile(r"\b(CUST\d{3,})\b", re.IGNORECASE)
ORDER_ID_PATTERN = re.compile(r"\b(ORD\d{4,})\b", re.IGNORECASE)


class CustomerContextResult(BaseModel):
    """Structured, validated customer context metadata."""

    customer_id: Optional[str] = Field(
        default=None,
        description="Identified customer ID (e.g. 'CUST001') or None if unidentified/ambiguous",
    )
    is_authenticated: bool = Field(
        default=False,
        description="Explicitly False: current application lacks authenticated session management",
    )
    verification_status: str = Field(
        default="unidentified",
        description="Status: 'unidentified', 'unverified_self_reported', 'inferred_from_order', 'unknown_customer', or 'ambiguous'",
    )
    identified_from: str = Field(
        default="none",
        description="Source of identification: 'none', 'order_lookup', 'customer_id_mention', or 'workflow_state'",
    )
    is_ambiguous: bool = Field(
        default=False,
        description="True if multiple conflicting customer IDs or cross-account order mismatches occur",
    )
    needs_clarification: bool = Field(
        default=False,
        description="True if identity cannot be determined with certainty without customer clarification",
    )
    order_ids: List[str] = Field(
        default_factory=list,
        description="List of order IDs belonging exclusively to this identified customer",
    )
    orders: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Sanitized summary details of orders belonging exclusively to this customer",
    )
    tickets: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Sanitized support tickets belonging exclusively to this customer",
    )
    active_order_id: Optional[str] = Field(
        default=None,
        description="Specific order ID referenced in the current turn, if any",
    )
    summary: str = Field(
        ...,
        description="Concise factual explanation of found context and missing or unavailable details",
    )


class CustomerContextAgent:
    """Specialized agent for safely retrieving and structuring customer context."""

    def __init__(self):
        pass

    def extract_customer_ids(self, text: str) -> List[str]:
        """Extract all unique customer IDs from text in uppercase order."""
        if not text or not isinstance(text, str):
            return []
        matches = CUSTOMER_ID_PATTERN.findall(text)
        return list(dict.fromkeys(m.upper() for m in matches))

    def extract_order_ids(self, text: str) -> List[str]:
        """Extract all unique order IDs from text in uppercase order."""
        if not text or not isinstance(text, str):
            return []
        matches = ORDER_ID_PATTERN.findall(text)
        return list(dict.fromkeys(m.upper() for m in matches))

    def resolve_context(
        self,
        message: str,
        order_id: Optional[str] = None,
        state: Optional[Dict[str, Any]] = None,
    ) -> CustomerContextResult:
        """Resolve customer context safely from message, order references, and database.

        Guarantees:
        1. Read-only operation: never modifies ORDERS or creates tickets.
        2. No cross-customer exposure: only returns records matching the resolved customer.
        3. Ambiguity handling: flags conflicting customer IDs or order mismatches without guessing.
        4. Authentication honesty: marks is_authenticated=False and distinguishes confirmed from missing.
        """
        raw_message = message or ""
        mentioned_customer_ids = self.extract_customer_ids(raw_message)
        mentioned_order_ids = self.extract_order_ids(raw_message)

        # Merge in any explicit order_id or state order_id if present
        if order_id and order_id.upper() not in mentioned_order_ids:
            mentioned_order_ids.append(order_id.upper())

        if state and isinstance(state, dict):
            inv = state.get("investigation") or {}
            st_order_id = inv.get("order_id")
            if st_order_id and st_order_id.upper() not in mentioned_order_ids:
                mentioned_order_ids.append(st_order_id.upper())

        # Check 1: Multiple conflicting customer IDs mentioned directly
        if len(mentioned_customer_ids) > 1:
            return CustomerContextResult(
                customer_id=None,
                is_authenticated=False,
                verification_status="ambiguous",
                identified_from="none",
                is_ambiguous=True,
                needs_clarification=True,
                order_ids=[],
                orders=[],
                tickets=[],
                active_order_id=None,
                summary=(
                    f"Multiple conflicting customer IDs detected ({', '.join(mentioned_customer_ids)}). "
                    "Customer identity is ambiguous and requires clarification before accessing account records."
                ),
            )

        # Map order IDs to customer IDs in mock database
        order_to_customer: Dict[str, Optional[str]] = {}
        for ord_id in mentioned_order_ids:
            matching_order = next((o for o in ORDERS if o.get("id", "").upper() == ord_id), None)
            order_to_customer[ord_id] = matching_order.get("customer_id") if matching_order else None

        # Check 2: Multiple order IDs belonging to different customers
        known_customers_from_orders = {
            cust for cust in order_to_customer.values() if cust is not None
        }
        if len(known_customers_from_orders) > 1:
            return CustomerContextResult(
                customer_id=None,
                is_authenticated=False,
                verification_status="ambiguous",
                identified_from="none",
                is_ambiguous=True,
                needs_clarification=True,
                order_ids=[],
                orders=[],
                tickets=[],
                active_order_id=None,
                summary=(
                    f"Multiple orders referencing different customer accounts ({', '.join(known_customers_from_orders)}) "
                    "were mentioned. Access to records is restricted to avoid cross-account exposure."
                ),
            )

        # Check 3: Customer ID mentioned conflicts with customer ID of mentioned order
        resolved_customer_id = mentioned_customer_ids[0] if mentioned_customer_ids else None
        order_inferred_customer = next(iter(known_customers_from_orders)) if known_customers_from_orders else None

        if resolved_customer_id and order_inferred_customer:
            if resolved_customer_id != order_inferred_customer:
                return CustomerContextResult(
                    customer_id=None,
                    is_authenticated=False,
                    verification_status="ambiguous",
                    identified_from="none",
                    is_ambiguous=True,
                    needs_clarification=True,
                    order_ids=[],
                    orders=[],
                    tickets=[],
                    active_order_id=mentioned_order_ids[0] if mentioned_order_ids else None,
                    summary=(
                        f"Conflicting identity detected: Order {mentioned_order_ids[0]} belongs to "
                        f"customer {order_inferred_customer}, but message explicitly specified {resolved_customer_id}. "
                        "Customer identity cannot be verified without clarification."
                    ),
                )

        # Determine identification source and verification status
        active_order_id = mentioned_order_ids[0] if mentioned_order_ids else None
        identified_from = "none"
        verification_status = "unidentified"

        if resolved_customer_id:
            identified_from = "customer_id_mention"
            verification_status = "unverified_self_reported"
        elif order_inferred_customer:
            resolved_customer_id = order_inferred_customer
            identified_from = "order_lookup"
            verification_status = "inferred_from_order"

        # Case 4: No customer identified
        if not resolved_customer_id:
            return CustomerContextResult(
                customer_id=None,
                is_authenticated=False,
                verification_status="unidentified",
                identified_from="none",
                is_ambiguous=False,
                needs_clarification=False,
                order_ids=[],
                orders=[],
                tickets=[],
                active_order_id=active_order_id,
                summary=(
                    "No customer identification or valid order reference was found in the conversation. "
                    "Session is unauthenticated. Customer account records remain unavailable."
                ),
            )

        # Case 5: Customer identified - retrieve customer orders and tickets
        # Strict Isolation: Read-only copy of orders matching ONLY this customer
        customer_orders_raw = [
            copy.deepcopy(o) for o in ORDERS if o.get("customer_id", "").upper() == resolved_customer_id
        ]

        # Extract sanitized order summaries
        sanitized_orders: List[Dict[str, Any]] = []
        customer_order_ids: List[str] = []
        for o in customer_orders_raw:
            oid = o.get("id", "")
            customer_order_ids.append(oid)
            items = o.get("items", [])
            sanitized_orders.append({
                "order_id": oid,
                "status": o.get("status", "unknown"),
                "total_amount": float(o.get("total_amount", 0.0)),
                "created_at": o.get("created_at", "N/A"),
                "items_count": len(items),
                "item_names": [it.get("name", "") for it in items],
            })

        # Retrieve existing tickets matching ONLY this customer
        all_tickets = list_tickets()
        customer_tickets_raw = [
            t for t in all_tickets if (t.get("customer_id") or "").upper() == resolved_customer_id
        ]
        sanitized_tickets: List[Dict[str, Any]] = []
        for t in customer_tickets_raw:
            sanitized_tickets.append({
                "ticket_id": t.get("ticket_id"),
                "category": t.get("category"),
                "priority": t.get("priority"),
                "status": t.get("status"),
                "created_at": t.get("created_at"),
                "escalation_reason": t.get("escalation_reason"),
            })

        # Handle Unknown Customer ID (ID provided, but 0 orders and 0 tickets)
        if not sanitized_orders and not sanitized_tickets:
            verification_status = "unknown_customer"
            return CustomerContextResult(
                customer_id=resolved_customer_id,
                is_authenticated=False,
                verification_status=verification_status,
                identified_from=identified_from,
                is_ambiguous=False,
                needs_clarification=False,
                order_ids=[],
                orders=[],
                tickets=[],
                active_order_id=active_order_id,
                summary=(
                    f"Customer ID '{resolved_customer_id}' was self-reported, but has no matching order or ticket "
                    "records in the database. Session is unauthenticated."
                ),
            )

        # Valid customer records found
        orders_desc = (
            f"{len(sanitized_orders)} order(s) on file ({', '.join(customer_order_ids)})"
            if sanitized_orders
            else "no orders on file"
        )
        tickets_desc = (
            f"{len(sanitized_tickets)} active/past ticket(s)"
            if sanitized_tickets
            else "no prior support tickets"
        )
        active_desc = f", referencing order {active_order_id}" if active_order_id else ""

        summary = (
            f"Customer context resolved for {resolved_customer_id} ({verification_status}, unauthenticated){active_desc}. "
            f"Found {orders_desc} and {tickets_desc}. Payment records are not exposed at context level."
        )

        return CustomerContextResult(
            customer_id=resolved_customer_id,
            is_authenticated=False,
            verification_status=verification_status,
            identified_from=identified_from,
            is_ambiguous=False,
            needs_clarification=False,
            order_ids=customer_order_ids,
            orders=sanitized_orders,
            tickets=sanitized_tickets,
            active_order_id=active_order_id,
            summary=summary,
        )


_default_context_agent = CustomerContextAgent()


def resolve_customer_context(
    message: str,
    order_id: Optional[str] = None,
    state: Optional[Dict[str, Any]] = None,
    agent: Optional[CustomerContextAgent] = None,
) -> CustomerContextResult:
    """Convenience functional interface for resolving customer context."""
    active_agent = agent or _default_context_agent
    return active_agent.resolve_context(message=message, order_id=order_id, state=state)
