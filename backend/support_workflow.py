"""Deterministic LangGraph support workflow coordinating classification, retrieval, investigation, actions, and escalation."""

import uuid
from typing import Any, Dict, List, Optional, TypedDict
from langgraph.graph import StateGraph, START, END

try:
    from backend.intent_classifier import classify_intent
    from backend.knowledge_retriever import retrieve_knowledge
    from backend.support_investigator import (
        extract_order_id,
        investigate_order_context,
    )
    from backend.ticket_service import create_ticket
    from backend.action_service import cancel_order, request_return
except ImportError:
    from intent_classifier import classify_intent
    from knowledge_retriever import retrieve_knowledge
    from support_investigator import (
        extract_order_id,
        investigate_order_context,
    )
    from ticket_service import create_ticket
    from action_service import cancel_order, request_return

ORDER_DEPENDENT_INTENTS = {
    "order_tracking",
    "payment_issue",
    "cancellation",
    "refund_status",
    "return_or_replacement",
}


class SupportState(TypedDict, total=False):
    message: str
    session_id: str
    intent: str
    knowledge_results: List[Dict[str, Any]]
    investigation: Dict[str, Any]
    decision: str
    assistant_message: str
    escalation_reason: Optional[str]
    priority: Optional[str]
    ticket: Optional[Dict[str, Any]]
    action_name: Optional[str]
    action_result: Optional[Dict[str, Any]]


def classify_intent_node(state: SupportState) -> Dict[str, Any]:
    """Classify the primary support intent of the customer message."""
    message = state.get("message", "")
    intent = classify_intent(message)
    return {"intent": intent}


def retrieve_knowledge_node(state: SupportState) -> Dict[str, Any]:
    """Retrieve relevant support guidance policies from knowledge base."""
    message = state.get("message", "")
    intent = state.get("intent", "general_inquiry")
    knowledge_results = retrieve_knowledge(message, intent, top_k=3)
    return {"knowledge_results": knowledge_results}


def investigate_order_node(state: SupportState) -> Dict[str, Any]:
    """Investigate order details and payment records from mock data."""
    message = state.get("message", "")
    investigation = investigate_order_context(message)
    return {"investigation": investigation}


def route_after_knowledge(state: SupportState) -> str:
    """Conditional router: route to order investigation if relevant, else to decision."""
    message = state.get("message", "")
    intent = state.get("intent", "general_inquiry")
    if extract_order_id(message) or intent in ORDER_DEPENDENT_INTENTS:
        return "investigate_order_node"
    return "decide_next_step_node"


def decide_next_step_node(state: SupportState) -> Dict[str, Any]:
    """Make a deterministic decision based on collected evidence, routing to actions or escalation."""
    intent = state.get("intent", "general_inquiry")
    investigation = state.get("investigation") or {
        "attempted": False,
        "order_id": None,
        "status": "order_id_required",
        "order": None,
        "payments": None,
        "summary": "An order ID (e.g., ORD1001) is required to investigate order status and payment history.",
    }
    knowledge = state.get("knowledge_results", [])
    inv_status = investigation.get("status")
    order = investigation.get("order")
    payments = investigation.get("payments") or []

    escalate = False
    escalation_reason = ""
    priority = "medium"
    action_name = None

    # Check for actionable intents when order is verified
    if intent in {"cancellation", "return_or_replacement"} and inv_status == "found":
        action_name = intent
        decision = "execute_action"
        return {
            "decision": decision,
            "investigation": investigation,
            "action_name": action_name,
            "escalation_reason": None,
            "priority": priority,
        }

    # Escalation Rule: Payment issues with failed/pending records or unrecognized order IDs
    if intent == "payment_issue":
        if inv_status == "found":
            has_failed_payment = any(p.get("status") in {"failed", "pending"} for p in payments)
            is_order_failed = order and order.get("status") in {"payment_failed", "pending_payment"}
            if has_failed_payment or is_order_failed:
                escalate = True
                priority = "urgent" if has_failed_payment else "high"
                escalation_reason = "Unresolved payment failure or transaction discrepancy requires billing team review."
        elif inv_status == "order_not_found":
            escalate = True
            priority = "high"
            escalation_reason = f"Customer reported payment deduction for unrecognized order ID '{investigation.get('order_id')}'."

    # General state routing
    if escalate:
        decision = "escalate"
    elif inv_status == "found":
        decision = "order_found"
    elif inv_status == "order_not_found":
        decision = "order_not_found"
    elif inv_status == "order_id_required" and intent in ORDER_DEPENDENT_INTENTS:
        decision = "order_id_required"
    elif knowledge:
        decision = "knowledge_guidance"
    else:
        decision = "insufficient_evidence"

    return {
        "decision": decision,
        "investigation": investigation,
        "escalation_reason": escalation_reason,
        "priority": priority,
        "action_name": None,
    }


def route_after_decision(state: SupportState) -> str:
    """Conditional router: route to action, escalation, or direct response composition."""
    decision = state.get("decision")
    if decision == "execute_action":
        return "execute_action_node"
    if decision == "escalate":
        return "escalate_node"
    return "compose_response_node"


def execute_action_node(state: SupportState) -> Dict[str, Any]:
    """Execute cancellation or return/replacement action safely."""
    # Prevent duplicate action execution for the same workflow invocation
    if state.get("action_result"):
        return {}

    action_name = state.get("action_name")
    investigation = state.get("investigation") or {}
    order_id = investigation.get("order_id", "")
    message = state.get("message", "")

    if action_name == "cancellation":
        result = cancel_order(order_id, reason="Customer requested cancellation via chat")
        decision = "action_completed" if result["success"] else "action_rejected"
        # Refresh investigation order status if mutated
        if result["success"] and result.get("order"):
            investigation["order"] = result["order"]
            investigation["summary"] = f"Order {order_id} has been cancelled."
        return {
            "action_result": result,
            "decision": decision,
            "investigation": investigation,
        }

    elif action_name == "return_or_replacement":
        # Check if customer specified replacement
        req_type = "replacement" if any(w in message.lower() for w in ["replace", "replacement", "exchange"]) else "return"
        result = request_return(order_id, request_type=req_type, reason="Customer requested via chat")
        decision = "action_completed" if result["success"] else "action_rejected"
        return {
            "action_result": result,
            "decision": decision,
        }

    return {"decision": "insufficient_evidence"}


def escalate_node(state: SupportState) -> Dict[str, Any]:
    """Create exactly one ticket through ticket_service when escalation is triggered."""
    if state.get("ticket"):
        return {}

    message = state.get("message", "")
    session_id = state.get("session_id", "")
    intent = state.get("intent", "general_inquiry")
    escalation_reason = state.get("escalation_reason") or "Customer issue requires human review."
    priority = state.get("priority", "medium")

    investigation = state.get("investigation") or {}
    order = investigation.get("order")
    customer_id = order.get("customer_id") if order else None
    investigation_summary = investigation.get("summary")

    try:
        ticket = create_ticket(
            session_id=session_id,
            original_message=message,
            category=intent,
            escalation_reason=escalation_reason,
            customer_id=customer_id,
            priority=priority,
            investigation_summary=investigation_summary,
        )
        return {"ticket": ticket, "decision": "escalated"}
    except Exception:
        return {"ticket": None, "decision": "escalation_failed"}


def compose_response_node(state: SupportState) -> Dict[str, Any]:
    """Compose a factual response based strictly on verified evidence and policy guidance."""
    decision = state.get("decision", "insufficient_evidence")
    investigation = state.get("investigation", {})
    knowledge = state.get("knowledge_results", [])
    intent = state.get("intent", "general_inquiry")
    ticket = state.get("ticket")
    action_result = state.get("action_result")

    guidance_snippet = ""
    if knowledge:
        top_kb = knowledge[0]
        guidance_snippet = (
            f"Policy note ({top_kb.get('title')}): {top_kb.get('guidance')}"
        )

    if decision == "action_completed" and action_result:
        msg = action_result.get("message", "Action completed successfully.")
        response = f"Your request has been processed:\n{msg}"
        if guidance_snippet:
            response += f"\n\nRelevant policy guidance:\n{guidance_snippet}"

    elif decision == "action_rejected" and action_result:
        msg = action_result.get("message", "The requested action cannot be performed.")
        response = f"Unable to process request:\n{msg}"
        if guidance_snippet:
            response += f"\n\nRelevant policy guidance:\n{guidance_snippet}"

    elif decision == "escalated" and ticket:
        ticket_id = ticket.get("ticket_id")
        response = (
            f"Your issue has been referred for human support review (Ticket ID: {ticket_id}). "
            "A customer support specialist will review your case details and follow up with you."
        )
        if investigation.get("summary"):
            response += f"\n\nVerified records attached to ticket:\n{investigation['summary']}"
        if guidance_snippet:
            response += f"\n\nRelevant policy guidance:\n{guidance_snippet}"

    elif decision == "escalation_failed":
        response = (
            "We were unable to automatically generate an escalation ticket for your request. "
            "Please contact our customer support helpdesk directly."
        )

    elif decision == "order_id_required":
        response = (
            "To assist you with your request, could you please provide your Order ID "
            "(for example, ORD1001)? Once provided, I can look up the live status and payment records."
        )
        if guidance_snippet:
            response += f"\n\nIn the meantime:\n{guidance_snippet}"

    elif decision == "order_not_found":
        order_id = investigation.get("order_id", "specified")
        response = (
            f"I could not find any records for order ID '{order_id}' in our system. "
            "Please verify the number and try again, or reach out to our support team."
        )
        if guidance_snippet:
            response += f"\n\nGeneral guidance:\n{guidance_snippet}"

    elif decision == "order_found":
        summary = investigation.get("summary", "")
        response = f"Here is the verified status for your order:\n{summary}"
        if guidance_snippet:
            response += f"\n\nRelevant policy guidance:\n{guidance_snippet}"

    elif decision == "knowledge_guidance":
        top_kb = knowledge[0]
        response = (
            f"Regarding your inquiry ({intent.replace('_', ' ')}):\n"
            f"{top_kb.get('guidance')}"
        )

    else:
        response = (
            "Thank you for contacting customer support. I could not find specific information "
            "matching your request. Please provide more details or an Order ID so I can assist you."
        )

    return {"assistant_message": response}


def build_support_graph():
    """Build and compile the LangGraph support workflow."""
    workflow = StateGraph(SupportState)

    # 1. Add nodes
    workflow.add_node("classify_intent_node", classify_intent_node)
    workflow.add_node("retrieve_knowledge_node", retrieve_knowledge_node)
    workflow.add_node("investigate_order_node", investigate_order_node)
    workflow.add_node("decide_next_step_node", decide_next_step_node)
    workflow.add_node("execute_action_node", execute_action_node)
    workflow.add_node("escalate_node", escalate_node)
    workflow.add_node("compose_response_node", compose_response_node)

    # 2. Add edges & conditional routing
    workflow.add_edge(START, "classify_intent_node")
    workflow.add_edge("classify_intent_node", "retrieve_knowledge_node")
    workflow.add_conditional_edges(
        "retrieve_knowledge_node",
        route_after_knowledge,
        {
            "investigate_order_node": "investigate_order_node",
            "decide_next_step_node": "decide_next_step_node",
        },
    )
    workflow.add_edge("investigate_order_node", "decide_next_step_node")
    workflow.add_conditional_edges(
        "decide_next_step_node",
        route_after_decision,
        {
            "execute_action_node": "execute_action_node",
            "escalate_node": "escalate_node",
            "compose_response_node": "compose_response_node",
        },
    )
    workflow.add_edge("execute_action_node", "compose_response_node")
    workflow.add_edge("escalate_node", "compose_response_node")
    workflow.add_edge("compose_response_node", END)

    return workflow.compile()


support_graph = build_support_graph()


def run_support_workflow(
    message: str,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute the compiled LangGraph support workflow."""
    resolved_session_id = (
        session_id.strip()
        if session_id and session_id.strip()
        else str(uuid.uuid4())
    )

    initial_state: SupportState = {
        "message": message,
        "session_id": resolved_session_id,
        "intent": "",
        "knowledge_results": [],
        "investigation": {},
        "decision": "",
        "assistant_message": "",
        "ticket": None,
        "action_name": None,
        "action_result": None,
    }

    final_state = support_graph.invoke(initial_state)

    return {
        "session_id": resolved_session_id,
        "user_message": message,
        "assistant_message": final_state.get("assistant_message", ""),
        "intent": final_state.get("intent", "general_inquiry"),
        "status": "received",
        "knowledge_results": final_state.get("knowledge_results", []),
        "investigation": final_state.get("investigation"),
        "decision": final_state.get("decision"),
        "ticket": final_state.get("ticket"),
        "action_result": final_state.get("action_result"),
    }
