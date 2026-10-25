"""Customer inbox: notifications about orders and human-support cases."""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status

try:
    from backend.mock_data import NOTIFICATIONS, TICKETS
except ImportError:
    from mock_data import NOTIFICATIONS, TICKETS

router = APIRouter(tags=["Inbox"])


def _customer_notifications(customer_id: str) -> List[Dict[str, Any]]:
    norm = customer_id.strip().upper()
    items = [n for n in NOTIFICATIONS if n.get("customer_id", "").upper() == norm]
    return sorted(items, key=lambda n: n.get("created_at", ""), reverse=True)


@router.get("/customers/{customer_id}/notifications", summary="Inbox messages for a customer, newest first")
def list_notifications(customer_id: str) -> Dict[str, Any]:
    items = _customer_notifications(customer_id)
    return {
        "unread_count": sum(1 for n in items if not n.get("read")),
        "notifications": items,
    }


@router.post("/customers/{customer_id}/notifications/read-all", summary="Mark every inbox message as read")
def mark_all_read(customer_id: str) -> Dict[str, Any]:
    changed = 0
    for n in _customer_notifications(customer_id):
        if not n.get("read"):
            n["read"] = True
            changed += 1
    return {"success": True, "marked_read": changed}


@router.post("/notifications/{notification_id}/read", summary="Mark one inbox message as read")
def mark_read(notification_id: str) -> Dict[str, Any]:
    norm = notification_id.strip().upper()
    for n in NOTIFICATIONS:
        if n.get("id", "").upper() == norm:
            n["read"] = True
            return {"success": True, "notification": n}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Notification '{notification_id}' not found.")


@router.get("/customers/{customer_id}/tickets", summary="Support cases opened for a customer")
def list_customer_tickets(customer_id: str) -> List[Dict[str, Any]]:
    norm = customer_id.strip().upper()
    mine = [t for t in TICKETS if (t.get("customer_id") or "").upper() == norm]
    return sorted(mine, key=lambda t: t.get("created_at", ""), reverse=True)
