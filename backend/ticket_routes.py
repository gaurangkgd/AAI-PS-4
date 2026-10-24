"""FastAPI endpoints for customer support tickets."""

import copy
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

try:
    from backend.schemas import TicketCreate, TicketResponse
    from backend.tools.tickets import create_support_ticket, update_ticket_status
    from backend.mock_data import TICKETS
except ImportError:
    from schemas import TicketCreate, TicketResponse
    from tools.tickets import create_support_ticket, update_ticket_status
    from mock_data import TICKETS

router = APIRouter(prefix="/tickets", tags=["Tickets"])


class TicketPatchRequest(BaseModel):
    status: Optional[str] = Field(None, description="New status")
    notes: Optional[str] = Field(None, description="Update notes")
    assigned_to: Optional[str] = Field(None, description="Assigned specialist")


def get_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
    norm_id = ticket_id.strip().upper() if ticket_id else ""
    for t in TICKETS:
        if t.get("ticket_id", "").upper() == norm_id:
            return copy.deepcopy(t)
    return None


def list_tickets(status: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
    results = list(TICKETS)
    if status:
        norm_s = status.strip().lower()
        results = [t for t in results if (t.get("status") or "").lower() == norm_s]
    if category:
        norm_c = category.strip().lower()
        results = [t for t in results if (t.get("category") or "").lower() == norm_c]
    return copy.deepcopy(results)


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new support ticket",
)
def create_new_ticket(ticket_req: TicketCreate) -> TicketResponse:
    raw = create_support_ticket.invoke({
        "title": f"Support Request [{ticket_req.category}]",
        "category": ticket_req.category,
        "priority": ticket_req.priority or "medium",
        "escalation_reason": ticket_req.reason,
        "customer_id": ticket_req.customer_id or "",
        "internal_notes": ticket_req.investigation_summary or "",
    })
    res = json.loads(raw)
    tkt = get_ticket(res["ticket_id"])
    if not tkt:
        raise HTTPException(status_code=500, detail="Failed to retrieve created ticket.")
    return TicketResponse(**tkt)


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
    summary="Get a ticket by ID",
)
def retrieve_ticket(ticket_id: str) -> TicketResponse:
    ticket = get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found.",
        )
    return TicketResponse(**ticket)


@router.patch(
    "/{ticket_id}",
    response_model=TicketResponse,
    summary="Update ticket status or notes",
)
def patch_ticket(ticket_id: str, payload: TicketPatchRequest) -> TicketResponse:
    if payload.status:
        raw = update_ticket_status.invoke({
            "ticket_id": ticket_id,
            "new_status": payload.status,
            "notes": payload.notes or "",
            "assigned_to": payload.assigned_to or "",
        })
        res = json.loads(raw)
        if not res.get("success"):
            raise HTTPException(status_code=400, detail=res.get("message"))

    ticket = get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
    return TicketResponse(**ticket)


@router.get(
    "",
    response_model=List[TicketResponse],
    summary="List support tickets with optional filtering",
)
def get_all_tickets(
    status: Optional[str] = Query(None, description="Filter by status (open, in_progress, resolved)"),
    category: Optional[str] = Query(None, description="Filter by category/intent"),
) -> List[TicketResponse]:
    raw_list = list_tickets(status=status, category=category)
    return [TicketResponse(**t) for t in raw_list]
