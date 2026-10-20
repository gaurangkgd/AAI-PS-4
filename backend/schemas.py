from typing import Any, Dict, List, Optional
from pydantic import BaseModel, field_validator


class KnowledgeEntry(BaseModel):
    id: str
    intent: str
    title: str
    guidance: str
    keywords: Optional[List[str]] = None


class Product(BaseModel):
    id: str
    name: str
    category: str
    price: float
    stock: int


class OrderItem(BaseModel):
    product_id: str
    name: str
    quantity: int
    unit_price: float


class Order(BaseModel):
    id: str
    customer_id: str
    items: List[OrderItem]
    total_amount: float
    status: str
    created_at: str


class Payment(BaseModel):
    id: str
    order_id: str
    amount: float
    status: str
    payment_method: str
    transaction_ref: str
    timestamp: str


class InvestigationResult(BaseModel):
    attempted: bool
    order_id: Optional[str] = None
    status: str  # "order_id_required", "order_not_found", "found"
    order: Optional[Order] = None
    payments: Optional[List[Payment]] = None
    summary: Optional[str] = None


class CancelOrderRequest(BaseModel):
    reason: Optional[str] = None


class ReturnRequestCreate(BaseModel):
    request_type: Optional[str] = "return"
    reason: Optional[str] = None

    @field_validator("request_type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> str:
        if v and v.lower() not in {"return", "replacement"}:
            raise ValueError("request_type must be 'return' or 'replacement'")
        return v.lower() if v else "return"


class ReturnRequestResponse(BaseModel):
    request_id: str
    order_id: str
    request_type: str
    status: str
    reason: Optional[str] = None
    created_at: str


class ActionResponse(BaseModel):
    success: bool
    action: str
    order_id: str
    message: str
    order: Optional[Order] = None
    return_request: Optional[ReturnRequestResponse] = None


class TicketCreate(BaseModel):
    session_id: str
    original_message: str
    category: str
    reason: str
    customer_id: Optional[str] = None
    priority: Optional[str] = "medium"
    investigation_summary: Optional[str] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> str:
        if v and v.lower() not in {"low", "medium", "high", "urgent"}:
            raise ValueError("Priority must be one of: low, medium, high, urgent")
        return v.lower() if v else "medium"


class TicketResponse(BaseModel):
    ticket_id: str
    customer_id: Optional[str] = None
    session_id: str
    category: str
    priority: str
    status: str
    original_message: str
    escalation_reason: str
    investigation_summary: Optional[str] = None
    created_at: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message cannot be empty or whitespace-only.")
        return v


class ChatResponse(BaseModel):
    session_id: str
    user_message: str
    assistant_message: str
    intent: str
    status: str
    knowledge_results: Optional[List[KnowledgeEntry]] = None
    investigation: Optional[InvestigationResult] = None
    decision: Optional[str] = None
    ticket: Optional[TicketResponse] = None
    action_result: Optional[ActionResponse] = None
    understanding: Optional[Dict[str, Any]] = None
    customer_context: Optional[Dict[str, Any]] = None
    knowledge_retrieval: Optional[Dict[str, Any]] = None
    troubleshooting: Optional[Dict[str, Any]] = None
    action_execution: Optional[Dict[str, Any]] = None
    memory: Optional[Dict[str, Any]] = None
    escalation: Optional[Dict[str, Any]] = None
