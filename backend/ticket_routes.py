"""FastAPI endpoints for customer support tickets."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

try:
    from backend.schemas import TicketCreate, TicketResponse
    from backend.ticket_service import create_ticket, get_ticket, list_tickets
except ImportError:
    from schemas import TicketCreate, TicketResponse
    from ticket_service import create_ticket, get_ticket, list_tickets

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new support ticket",
)
def create_new_ticket(ticket_req: TicketCreate) -> TicketResponse:
    ticket = create_ticket(
        session_id=ticket_req.session_id,
        original_message=ticket_req.original_message,
        category=ticket_req.category,
        escalation_reason=ticket_req.reason,
        customer_id=ticket_req.customer_id,
        priority=ticket_req.priority or "medium",
        investigation_summary=ticket_req.investigation_summary,
    )
    return ticket


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
    return ticket


@router.get(
    "",
    response_model=List[TicketResponse],
    summary="List support tickets with optional filtering",
)
def get_all_tickets(
    status: Optional[str] = Query(None, description="Filter by status (open, in_progress, resolved)"),
    category: Optional[str] = Query(None, description="Filter by category/intent"),
) -> List[TicketResponse]:
    return list_tickets(status=status, category=category)
