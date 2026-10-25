"""Demo checkout: turns a cart into an order with a simulated payment. No real money moves."""

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

try:
    from backend.mock_data import CUSTOMERS, PRODUCTS, ORDERS, PAYMENTS, add_notification
except ImportError:
    from mock_data import CUSTOMERS, PRODUCTS, ORDERS, PAYMENTS, add_notification

router = APIRouter(tags=["Checkout"])


class CheckoutItem(BaseModel):
    product_id: str
    quantity: int = Field(..., ge=1, le=10)


class CheckoutRequest(BaseModel):
    customer_id: str
    items: List[CheckoutItem] = Field(..., min_length=1)
    payment_method: Literal["credit_card", "upi", "net_banking"] = "credit_card"
    shipping_address: Optional[str] = ""
    simulate_failure: bool = Field(default=False, description="Demo switch: make the gateway decline the payment")


def _next_numeric_id(prefix: str, existing: List[Dict[str, Any]], base: int) -> str:
    highest = base
    for row in existing:
        match = re.fullmatch(rf"{prefix}(\d+)", row.get("id", ""))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}{highest + 1}"


@router.post("/checkout", status_code=status.HTTP_201_CREATED, summary="Place an order and run the demo payment")
def checkout(payload: CheckoutRequest) -> Dict[str, Any]:
    customer = next((c for c in CUSTOMERS if c["id"].upper() == payload.customer_id.strip().upper()), None)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Customer '{payload.customer_id}' not found.")

    # Merge duplicate lines, then validate product and stock for every line before touching anything.
    wanted: Dict[str, int] = {}
    for item in payload.items:
        key = item.product_id.strip().upper()
        wanted[key] = wanted.get(key, 0) + item.quantity

    order_items = []
    total = 0.0
    for product_id, qty in wanted.items():
        product = next((p for p in PRODUCTS if p["id"].upper() == product_id), None)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product '{product_id}' not found.")
        if product["stock"] < qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {product['stock']} unit(s) of '{product['name']}' are in stock.",
            )
        order_items.append({
            "product_id": product["id"],
            "name": product["name"],
            "quantity": qty,
            "unit_price": product["price"],
        })
        total += product["price"] * qty
    total = round(total, 2)

    now = datetime.now(timezone.utc).isoformat()
    order_id = _next_numeric_id("ORD", ORDERS, 1000)
    payment_id = _next_numeric_id("PAY", PAYMENTS, 2000)
    paid = not payload.simulate_failure
    txn_suffix = "SUCCESS" if paid else "FAILED"

    order = {
        "id": order_id,
        "customer_id": customer["id"],
        "items": order_items,
        "total_amount": total,
        "status": "processing" if paid else "payment_failed",
        "created_at": now,
        "shipping_address": (payload.shipping_address or "").strip(),
    }
    payment = {
        "id": payment_id,
        "order_id": order_id,
        "amount": total,
        "status": "successful" if paid else "failed",
        "payment_method": payload.payment_method,
        "transaction_ref": f"TXN-{uuid.uuid4().int % 1000000:06d}-{txn_suffix}",
        "timestamp": now,
    }
    ORDERS.append(order)
    PAYMENTS.append(payment)

    if paid:
        for line in order_items:
            product = next(p for p in PRODUCTS if p["id"] == line["product_id"])
            product["stock"] -= line["quantity"]
        add_notification(
            customer["id"],
            "order_update",
            f"Order {order_id} confirmed",
            f"Thanks for your purchase! Payment of ${total:.2f} was received and order {order_id} is being prepared.",
            order_id=order_id,
        )
        message = f"Payment of ${total:.2f} processed. Order {order_id} is confirmed."
    else:
        add_notification(
            customer["id"],
            "order_update",
            f"Payment failed for order {order_id}",
            f"Your payment of ${total:.2f} could not be completed. If money left your account, ask our AI Support "
            "Concierge and we will route it to a billing specialist.",
            order_id=order_id,
        )
        message = f"The payment gateway declined the payment for order {order_id}."

    return {
        "success": paid,
        "message": message,
        "order": order,
        "payment": payment,
    }
