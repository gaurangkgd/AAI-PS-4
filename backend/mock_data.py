"""Fictional in-memory mock data for e-commerce store."""

PRODUCTS = [
    {
        "id": "PROD001",
        "name": "Wireless Noise-Canceling Headphones",
        "category": "Electronics",
        "price": 129.99,
        "stock": 45,
    },
    {
        "id": "PROD002",
        "name": "Ergonomic Mechanical Keyboard",
        "category": "Electronics",
        "price": 89.50,
        "stock": 20,
    },
    {
        "id": "PROD003",
        "name": "Ultra-Light Running Shoes",
        "category": "Apparel",
        "price": 74.99,
        "stock": 15,
    },
    {
        "id": "PROD004",
        "name": "Stainless Steel Thermal Water Bottle",
        "category": "Home & Kitchen",
        "price": 24.95,
        "stock": 100,
    },
    {
        "id": "PROD005",
        "name": "USB-C Multi-Port Hub",
        "category": "Electronics",
        "price": 39.99,
        "stock": 0,
    },
    {
        "id": "PROD006",
        "name": "Organic Cotton Hoodie",
        "category": "Apparel",
        "price": 54.00,
        "stock": 30,
    },
]

ORDERS = [
    {
        "id": "ORD1001",
        "customer_id": "CUST001",
        "items": [
            {
                "product_id": "PROD001",
                "name": "Wireless Noise-Canceling Headphones",
                "quantity": 1,
                "unit_price": 129.99,
            }
        ],
        "total_amount": 129.99,
        "status": "delivered",
        "created_at": "2026-10-10T09:30:00Z",
    },
    {
        "id": "ORD1002",
        "customer_id": "CUST001",
        "items": [
            {
                "product_id": "PROD004",
                "name": "Stainless Steel Thermal Water Bottle",
                "quantity": 2,
                "unit_price": 24.95,
            }
        ],
        "total_amount": 49.90,
        "status": "processing",
        "created_at": "2026-10-18T14:15:00Z",
    },
    {
        "id": "ORD1003",
        "customer_id": "CUST002",
        "items": [
            {
                "product_id": "PROD002",
                "name": "Ergonomic Mechanical Keyboard",
                "quantity": 1,
                "unit_price": 89.50,
            }
        ],
        "total_amount": 89.50,
        "status": "shipped",
        "created_at": "2026-10-15T11:00:00Z",
    },
    {
        "id": "ORD1004",
        "customer_id": "CUST003",
        "items": [
            {
                "product_id": "PROD005",
                "name": "USB-C Multi-Port Hub",
                "quantity": 1,
                "unit_price": 39.99,
            }
        ],
        "total_amount": 39.99,
        "status": "payment_failed",
        "created_at": "2026-10-19T08:20:00Z",
    },
    {
        "id": "ORD1005",
        "customer_id": "CUST004",
        "items": [
            {
                "product_id": "PROD003",
                "name": "Ultra-Light Running Shoes",
                "quantity": 1,
                "unit_price": 74.99,
            }
        ],
        "total_amount": 74.99,
        "status": "pending_payment",
        "created_at": "2026-10-19T10:00:00Z",
    },
]

PAYMENTS = [
    {
        "id": "PAY2001",
        "order_id": "ORD1001",
        "amount": 129.99,
        "status": "successful",
        "payment_method": "credit_card",
        "transaction_ref": "TXN-908123-SUCCESS",
        "timestamp": "2026-10-10T09:32:15Z",
    },
    {
        "id": "PAY2002",
        "order_id": "ORD1002",
        "amount": 49.90,
        "status": "successful",
        "payment_method": "upi",
        "transaction_ref": "TXN-908456-SUCCESS",
        "timestamp": "2026-10-18T14:16:02Z",
    },
    {
        "id": "PAY2003",
        "order_id": "ORD1003",
        "amount": 89.50,
        "status": "successful",
        "payment_method": "debit_card",
        "transaction_ref": "TXN-908789-SUCCESS",
        "timestamp": "2026-10-15T11:02:40Z",
    },
    {
        "id": "PAY2004",
        "order_id": "ORD1004",
        "amount": 39.99,
        "status": "failed",
        "payment_method": "credit_card",
        "transaction_ref": "TXN-909012-FAILED",
        "timestamp": "2026-10-19T08:21:10Z",
    },
    {
        "id": "PAY2005",
        "order_id": "ORD1005",
        "amount": 74.99,
        "status": "pending",
        "payment_method": "net_banking",
        "transaction_ref": "TXN-909345-PENDING",
        "timestamp": "2026-10-19T10:01:05Z",
    },
]

import copy

INITIAL_ORDERS = copy.deepcopy(ORDERS)
INITIAL_PAYMENTS = copy.deepcopy(PAYMENTS)


def reset_mock_data():
    """Reset ORDERS and PAYMENTS in-memory lists back to their initial state."""
    global ORDERS, PAYMENTS
    ORDERS.clear()
    ORDERS.extend(copy.deepcopy(INITIAL_ORDERS))
    PAYMENTS.clear()
    PAYMENTS.extend(copy.deepcopy(INITIAL_PAYMENTS))

