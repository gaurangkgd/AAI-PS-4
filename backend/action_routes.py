"""FastAPI routes for simulated e-commerce support actions."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status

try:
    from backend.schemas import ActionResponse, CancelOrderRequest, ReturnRequestCreate
    from backend.action_service import cancel_order, request_return
except ImportError:
    from schemas import ActionResponse, CancelOrderRequest, ReturnRequestCreate
    from action_service import cancel_order, request_return

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
    result = cancel_order(order_id, reason=reason)

    if not result["success"]:
        if "was not found" in result["message"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"],
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"],
        )

    return result


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

    result = request_return(order_id, request_type=req_type, reason=reason)

    if not result["success"]:
        if "was not found" in result["message"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"],
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"],
        )

    return result
