from typing import List
from fastapi import APIRouter, HTTPException

try:
    from backend.mock_data import PRODUCTS, ORDERS, PAYMENTS
    from backend.schemas import Product, Order, Payment
except ImportError:
    from mock_data import PRODUCTS, ORDERS, PAYMENTS
    from schemas import Product, Order, Payment

router = APIRouter()


@router.get("/products", response_model=List[Product], tags=["Products"])
def list_products() -> List[Product]:
    return PRODUCTS


@router.get("/products/{product_id}", response_model=Product, tags=["Products"])
def get_product(product_id: str) -> Product:
    for product in PRODUCTS:
        if product["id"].lower() == product_id.strip().lower():
            return product
    raise HTTPException(
        status_code=404, detail=f"Product with ID '{product_id}' not found."
    )


@router.get("/orders/{order_id}", response_model=Order, tags=["Orders"])
def get_order(order_id: str) -> Order:
    for order in ORDERS:
        if order["id"].lower() == order_id.strip().lower():
            return order
    raise HTTPException(
        status_code=404, detail=f"Order with ID '{order_id}' not found."
    )


@router.get(
    "/customers/{customer_id}/orders",
    response_model=List[Order],
    tags=["Customers"],
)
def get_customer_orders(customer_id: str) -> List[Order]:
    matched_orders = [
        order
        for order in ORDERS
        if order["customer_id"].lower() == customer_id.strip().lower()
    ]
    return matched_orders


@router.get("/payments/{order_id}", response_model=List[Payment], tags=["Payments"])
def get_order_payments(order_id: str) -> List[Payment]:
    matched_payments = [
        payment
        for payment in PAYMENTS
        if payment["order_id"].lower() == order_id.strip().lower()
    ]
    return matched_payments
