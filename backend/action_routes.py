"""FastAPI routes for simulated e-commerce support actions."""

import json
from typing import Optional
from fastapi import APIRouter, HTTPException, status

try:
    from backend.schemas import ActionResponse, CancelOrderRequest, ReturnRequestCreate
    from backend.tools.actions import cancel_order, request_return
    from backend.mock_data import ORDERS, RETURN_REQUESTS
except ImportError:
    from schemas import ActionResponse, CancelOrderRequest, ReturnRequestCreate
    from tools.actions import cancel_order, request_return
    from mock_data import ORDERS, RETURN_REQUESTS

router = APIRouter(prefix="/orders", tags=["Actions"])


@router.post(
    "/{order_id}/cancel",
    response_model=ActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel an order in processing status",
)
def cancel_order_endpoint(
    order_id: str,
    payload: Optional[CancelOrderRequest] = None,
) -> ActionResponse:
    reason = payload.reason if payload else None
    raw = cancel_order.invoke({"order_id": order_id, "reason": reason or ""})
    res = json.loads(raw)

    if not res.get("success"):
        if "was not found" in res.get("message", ""):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=res.get("message"),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("message"),
        )

    matched_order = next((o for o in ORDERS if o.get("id", "").upper() == order_id.strip().upper()), None)

    return ActionResponse(
        success=True,
        action="cancellation",
        order_id=order_id.strip().upper(),
        message=res.get("message", "Order cancelled successfully."),
        order=matched_order,
    )


@router.post(
    "/{order_id}/return",
    response_model=ActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a return or replacement request for a delivered order",
)
def return_order_endpoint(
    order_id: str,
    payload: Optional[ReturnRequestCreate] = None,
) -> ActionResponse:
    req_type = payload.request_type if payload and payload.request_type else "return"
    reason = payload.reason if payload else None

    raw = request_return.invoke({"order_id": order_id, "request_type": req_type, "reason": reason or ""})
    res = json.loads(raw)

    if not res.get("success"):
        if "was not found" in res.get("message", ""):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=res.get("message"),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("message"),
        )

    matched_order = next((o for o in ORDERS if o.get("id", "").upper() == order_id.strip().upper()), None)
    ret_req = next((r for r in RETURN_REQUESTS if r.get("request_id") == res.get("request_id")), None)

    return ActionResponse(
        success=True,
        action="return_or_replacement",
        order_id=order_id.strip().upper(),
        message=res.get("message", "Return request recorded."),
        order=matched_order,
        return_request=ret_req,
    )
