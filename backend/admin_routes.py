"""Supervisor and administrative analytics routes for customer support operations."""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

try:
    from backend.tools.metrics import get_resolution_metrics, record_csat_rating
    from backend.tools.tickets import update_ticket_status, search_tickets
    from backend.mock_data import TICKETS, CSAT_RATINGS, reset_mock_data
    from backend.knowledge_base import KNOWLEDGE_BASE
except ImportError:
    from tools.metrics import get_resolution_metrics, record_csat_rating
    from tools.tickets import update_ticket_status, search_tickets
    from mock_data import TICKETS, CSAT_RATINGS, reset_mock_data
    from knowledge_base import KNOWLEDGE_BASE

router = APIRouter(prefix="/admin", tags=["Supervisor Dashboard"])


@router.post("/reset", summary="Reset all mock databases to their initial state")
def reset_database() -> Dict[str, Any]:
    reset_mock_data()
    return {
        "success": True,
        "message": "All mock data (orders, tickets, return requests, and CSAT scores) have been restored to their clean baseline state."
    }



class TicketStatusUpdateRequest(BaseModel):
    new_status: str = Field(..., description="Target status: 'open', 'assigned', 'in_progress', 'pending_customer', 'resolved', 'closed'")
    notes: Optional[str] = Field(default="", description="Supervisor / agent resolution notes")
    assigned_to: Optional[str] = Field(default="", description="Assigned specialist name (e.g. agent_sarah)")


class CSATSubmissionRequest(BaseModel):
    ticket_id: Optional[str] = Field(default="general", description="Associated Ticket ID or 'general'")
    customer_id: Optional[str] = Field(default="CUST001", description="Customer ID")
    rating: int = Field(..., ge=1, le=5, description="Satisfaction score from 1 to 5")
    feedback: Optional[str] = Field(default="", description="Qualitative feedback comments")


@router.get("/metrics", summary="Get comprehensive supervisor analytics, SLA health, and outage alerts")
def get_dashboard_metrics() -> Dict[str, Any]:
    raw = get_resolution_metrics.invoke({})
    return json.loads(raw)


@router.get("/tickets", summary="List all tickets with lifecycle history for supervisor review")
def list_admin_tickets(
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
) -> List[Dict[str, Any]]:
    results = list(TICKETS)
    if status:
        norm_s = status.strip().lower()
        results = [t for t in results if (t.get("status") or "").lower() == norm_s]
    if category:
        norm_c = category.strip().lower()
        results = [t for t in results if (t.get("category") or "").lower() == norm_c]
    return results


@router.patch("/tickets/{ticket_id}/status", summary="Update ticket lifecycle status")
def update_ticket_lifecycle(ticket_id: str, payload: TicketStatusUpdateRequest) -> Dict[str, Any]:
    raw = update_ticket_status.invoke({
        "ticket_id": ticket_id,
        "new_status": payload.new_status,
        "notes": payload.notes or "",
        "assigned_to": payload.assigned_to or "",
    })
    res = json.loads(raw)
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("message", "Failed to update ticket status.")
        )
    return res


@router.post("/csat", summary="Submit a customer satisfaction (CSAT) rating")
def submit_csat(payload: CSATSubmissionRequest) -> Dict[str, Any]:
    raw = record_csat_rating.invoke({
        "ticket_id": payload.ticket_id,
        "customer_id": payload.customer_id,
        "rating": payload.rating,
        "feedback": payload.feedback or "",
    })
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Policy Governance & AI Knowledge Base Endpoints
# ---------------------------------------------------------------------------

class PolicyUpdateRequest(BaseModel):
    title: Optional[str] = None
    intent: Optional[str] = None
    guidance: str = Field(..., description="The policy guidance text referenced by the AI")
    keywords: Optional[List[str]] = None


class PolicyCreateRequest(BaseModel):
    id: Optional[str] = None
    intent: str
    title: str
    guidance: str
    keywords: Optional[List[str]] = None


@router.get("/policies", summary="List all knowledge base support policies referenced by AI")
def list_policies(
    category: Optional[str] = Query(None, description="Filter by category or intent"),
    search: Optional[str] = Query(None, description="Search keyword in title, keywords, or guidance"),
) -> List[Dict[str, Any]]:
    results = list(KNOWLEDGE_BASE)
    if category and category.strip() and category.lower() != "all":
        norm_cat = category.strip().lower()
        results = [p for p in results if norm_cat in (p.get("intent") or "").lower()]
    if search and search.strip():
        s = search.strip().lower()
        results = [
            p for p in results
            if s in (p.get("title") or "").lower()
            or s in (p.get("guidance") or "").lower()
            or s in (p.get("id") or "").lower()
            or any(s in kw.lower() for kw in p.get("keywords", []))
        ]
    return results


@router.get("/policies/{policy_id}", summary="Get a single policy entry")
def get_policy(policy_id: str) -> Dict[str, Any]:
    policy = next((p for p in KNOWLEDGE_BASE if p.get("id", "").upper() == policy_id.strip().upper()), None)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID '{policy_id}' not found."
        )
    return policy


@router.put("/policies/{policy_id}", summary="Update a support policy referenced by AI")
def update_policy(policy_id: str, payload: PolicyUpdateRequest) -> Dict[str, Any]:
    norm_id = policy_id.strip().upper()
    for policy in KNOWLEDGE_BASE:
        if policy.get("id", "").upper() == norm_id:
            if payload.title is not None and payload.title.strip():
                policy["title"] = payload.title.strip()
            if payload.intent is not None and payload.intent.strip():
                policy["intent"] = payload.intent.strip()
            if payload.guidance is not None and payload.guidance.strip():
                policy["guidance"] = payload.guidance.strip()
            if payload.keywords is not None:
                policy["keywords"] = [k.strip() for k in payload.keywords if k.strip()]
            return {
                "success": True,
                "message": f"Policy '{norm_id}' successfully updated. The AI will immediately apply this guidance.",
                "policy": policy,
            }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Policy with ID '{policy_id}' not found."
    )


@router.post("/policies", summary="Create a new support policy entry")
def create_policy(payload: PolicyCreateRequest) -> Dict[str, Any]:
    new_id = (
        payload.id.strip().upper()
        if payload.id and payload.id.strip()
        else f"KB-{payload.intent[:3].upper()}-{len(KNOWLEDGE_BASE) + 1:03d}"
    )
    if any(p.get("id", "").upper() == new_id for p in KNOWLEDGE_BASE):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Policy with ID '{new_id}' already exists."
        )

    new_policy = {
        "id": new_id,
        "intent": payload.intent.strip(),
        "title": payload.title.strip(),
        "guidance": payload.guidance.strip(),
        "keywords": [k.strip() for k in payload.keywords if k.strip()] if payload.keywords else [],
    }
    KNOWLEDGE_BASE.append(new_policy)
    return {
        "success": True,
        "message": f"New policy '{new_id}' successfully added. The AI now references this article.",
        "policy": new_policy,
    }
