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
    from backend.ticket_service import create_ticket, list_tickets
    from backend.action_service import cancel_order, request_return
    from backend.agents.conversation_understanding_agent import (
        understand_conversation,
    )
    from backend.agents.customer_context_agent import resolve_customer_context
    from backend.agents.knowledge_retrieval_agent import retrieve_knowledge_context
    from backend.agents.troubleshooting_agent import diagnose_support_issue
    from backend.agents.action_execution_agent import execute_support_action
    from backend.agents.multi_turn_memory_agent import (
        resolve_session_memory,
        update_session_memory,
        get_session_summary,
    )
    from backend.agents.escalation_decision_agent import (
        decide_escalation,
        EscalationDecisionResult,
    )
    from backend.agents.ticket_generation_agent import (
        generate_support_ticket,
        TicketGenerationResult,
    )
except ImportError:
    from intent_classifier import classify_intent
    from knowledge_retriever import retrieve_knowledge
    from support_investigator import (
        extract_order_id,
        investigate_order_context,
    )
    from ticket_service import create_ticket, list_tickets
    from action_service import cancel_order, request_return
    from agents.conversation_understanding_agent import understand_conversation
    from agents.customer_context_agent import resolve_customer_context
    from agents.knowledge_retrieval_agent import retrieve_knowledge_context
    from agents.troubleshooting_agent import diagnose_support_issue
    from agents.action_execution_agent import execute_support_action
    from agents.multi_turn_memory_agent import (
        resolve_session_memory,
        update_session_memory,
        get_session_summary,
    )
    from agents.escalation_decision_agent import (
        decide_escalation,
        EscalationDecisionResult,
    )
    from agents.ticket_generation_agent import (
        generate_support_ticket,
        TicketGenerationResult,
    )

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
    understanding: Optional[Dict[str, Any]]
    customer_context: Optional[Dict[str, Any]]
    knowledge_retrieval: Optional[Dict[str, Any]]
    troubleshooting: Optional[Dict[str, Any]]
    action_execution: Optional[Dict[str, Any]]
    memory_resolution: Optional[Dict[str, Any]]
    resolved_order_id: Optional[str]
    confirmed_action: Optional[str]
    confirmed_order_id: Optional[str]
    clarification_needed: Optional[bool]
    clarification_prompt: Optional[str]
    memory: Optional[Dict[str, Any]]
    escalation: Optional[Dict[str, Any]]
    ticket_generation: Optional[Dict[str, Any]]


def classify_intent_node(state: SupportState) -> Dict[str, Any]:
    """Classify intent and extract structured understanding using Conversation Understanding Agent (with rule-based fallback)."""
    message = state.get("message", "")
    confirmed_action = state.get("confirmed_action")
    if confirmed_action:
        return {
            "intent": confirmed_action,
            "priority": "high",
            "understanding": {
                "intent": confirmed_action,
                "confidence": 1.0,
                "priority": "high",
                "is_urgent": False,
                "sentiment": "neutral",
                "extracted_entities": {
                    "order_ids": [state.get("confirmed_order_id")] if state.get("confirmed_order_id") else []
                },
                "classification_mode": "memory_confirmed_action",
            },
        }
    understanding_result = understand_conversation(message)
    return {
        "intent": understanding_result.intent,
        "priority": understanding_result.priority,
        "understanding": understanding_result.model_dump(),
    }


def resolve_customer_context_node(state: SupportState) -> Dict[str, Any]:
    """Resolve structured customer identity, order history, and prior ticket context."""
    message = state.get("message", "")
    inv = state.get("investigation") or {}
    order_id = inv.get("order_id") or state.get("resolved_order_id")
    context_result = resolve_customer_context(message=message, order_id=order_id, state=state)
    return {"customer_context": context_result.model_dump()}


def retrieve_knowledge_node(state: SupportState) -> Dict[str, Any]:
    """Retrieve relevant support guidance policies using Knowledge Retrieval Agent."""
    message = state.get("message", "")
    intent = state.get("intent", "general_inquiry")
    retrieval_result = retrieve_knowledge_context(message=message, intent=intent, top_k=3)
    return {
        "knowledge_results": retrieval_result.entries,
        "knowledge_retrieval": retrieval_result.model_dump(),
    }


def investigate_order_node(state: SupportState) -> Dict[str, Any]:
    """Investigate order details and payment records from mock data."""
    message = state.get("message", "")
    resolved_order_id = state.get("resolved_order_id")
    investigation = investigate_order_context(message, order_id=resolved_order_id)
    return {"investigation": investigation}


def troubleshoot_node(state: SupportState) -> Dict[str, Any]:
    """Diagnose customer issue using factual investigation, context, and policy knowledge."""
    message = state.get("message", "")
    intent = state.get("intent", "general_inquiry")
    investigation = state.get("investigation")
    customer_context = state.get("customer_context")
    knowledge_retrieval = state.get("knowledge_retrieval")
    knowledge_results = state.get("knowledge_results")

    troubleshooting_res = diagnose_support_issue(
        message=message,
        intent=intent,
        investigation=investigation,
        customer_context=customer_context,
        knowledge_retrieval=knowledge_retrieval,
        knowledge_results=knowledge_results,
    )
    return {"troubleshooting": troubleshooting_res.model_dump()}


def route_after_knowledge(state: SupportState) -> str:
    """Conditional router: route to order investigation if relevant, else to troubleshooting."""
    message = state.get("message", "")
    intent = state.get("intent", "general_inquiry")
    resolved_order_id = state.get("resolved_order_id")
    if extract_order_id(message) or resolved_order_id or intent in ORDER_DEPENDENT_INTENTS:
        return "investigate_order_node"
    return "troubleshoot_node"


def decide_next_step_node(state: SupportState) -> Dict[str, Any]:
    """Make a deterministic decision based on collected evidence, routing to actions or escalation."""
    # Check if memory resolution flagged ambiguity or missing reference requiring clarification
    if state.get("clarification_needed"):
        return {
            "decision": "memory_clarification_required",
            "investigation": state.get("investigation") or {},
            "escalation_reason": None,
            "priority": "low",
            "action_name": None,
        }

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

    # Check for actionable intents when order is verified (never let escalation bypass valid action execution)
    confirmed_action = state.get("confirmed_action")
    if (intent in {"cancellation", "return_or_replacement"} or confirmed_action) and inv_status == "found":
        action_name = confirmed_action or intent
        decision = "execute_action"
        return {
            "decision": decision,
            "investigation": investigation,
            "action_name": action_name,
            "escalation_reason": None,
            "priority": "medium",
        }

    # Evaluate escalation via Escalation Decision Agent (Component 7)
    escalation_res = decide_escalation(
        message=state.get("message", ""),
        intent=intent,
        understanding=state.get("understanding"),
        customer_context=state.get("customer_context"),
        investigation=investigation,
        knowledge_retrieval=state.get("knowledge_retrieval"),
        knowledge_results=knowledge,
        troubleshooting=state.get("troubleshooting"),
        action_execution=state.get("action_execution"),
        memory=state.get("memory"),
        session_id=state.get("session_id"),
    )

    if escalation_res.should_escalate:
        return {
            "decision": "escalate",
            "investigation": investigation,
            "escalation_reason": escalation_res.escalation_reason,
            "priority": escalation_res.priority,
            "action_name": None,
            "escalation": escalation_res.model_dump(),
        }

    # General state routing if not escalated
    if inv_status == "found":
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
        "escalation_reason": None,
        "priority": escalation_res.priority,
        "action_name": None,
        "escalation": escalation_res.model_dump(),
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
    """Execute cancellation or return/replacement action safely via ActionExecutionAgent."""
    # Prevent duplicate action execution for the same workflow invocation
    if state.get("action_result"):
        return {}

    action_name = state.get("action_name") or state.get("confirmed_action") or ""
    investigation = state.get("investigation") or {}
    order_id = state.get("confirmed_order_id") or investigation.get("order_id", "")
    message = state.get("message", "")
    customer_context = state.get("customer_context")

    # Determine requested return type (return vs replacement)
    req_type = "replacement" if any(w in message.lower() for w in ["replace", "replacement", "exchange"]) else "return"

    exec_result = execute_support_action(
        action=action_name,
        order_id=order_id,
        message=message,
        customer_context=customer_context,
        request_type=req_type,
    )

    action_result = exec_result.details or {
        "success": exec_result.status == "executed",
        "action": exec_result.action,
        "order_id": order_id,
        "message": exec_result.message,
    }

    if exec_result.status == "executed":
        decision = "action_completed"
    elif exec_result.status == "confirmation_required":
        decision = "confirmation_required"
    else:
        decision = "action_rejected"

    # Refresh investigation order status if mutated
    if exec_result.mutation_performed and action_result.get("order"):
        investigation["order"] = action_result["order"]
        investigation["summary"] = f"Order {order_id} has been cancelled."

    return {
        "action_result": action_result,
        "action_execution": exec_result.model_dump(),
        "decision": decision,
        "investigation": investigation,
    }


def escalate_node(state: SupportState) -> Dict[str, Any]:
    """Generate or reuse support ticket via TicketGenerationAgent (Component 8)."""
    if state.get("ticket"):
        return {}

    message = state.get("message", "")
    session_id = state.get("session_id", "")
    intent = state.get("intent", "general_inquiry")
    escalation_reason = state.get("escalation_reason") or "Customer issue requires human review."
    priority = state.get("priority", "medium")

    investigation = state.get("investigation") or {}
    customer_context = state.get("customer_context")
    knowledge_retrieval = state.get("knowledge_retrieval")
    knowledge_results = state.get("knowledge_results")
    troubleshooting = state.get("troubleshooting")
    action_execution = state.get("action_execution")
    escalation = state.get("escalation")
    target_team = escalation.get("target_team") if escalation else None

    # Call Ticket Generation Agent
    ticket_gen_res = generate_support_ticket(
        message=message,
        session_id=session_id,
        intent=intent,
        escalation=escalation,
        escalation_reason=escalation_reason,
        priority=priority,
        target_team=target_team,
        customer_context=customer_context,
        investigation=investigation,
        knowledge_retrieval=knowledge_retrieval,
        knowledge_results=knowledge_results,
        troubleshooting=troubleshooting,
        action_execution=action_execution,
        force_create=True,
    )

    if ticket_gen_res and ticket_gen_res.ticket:
        return {
            "ticket": ticket_gen_res.ticket,
            "ticket_generation": ticket_gen_res.model_dump(),
            "decision": "escalated",
        }
    else:
        return {
            "ticket": None,
            "ticket_generation": ticket_gen_res.model_dump() if ticket_gen_res else None,
            "decision": "escalation_failed",
        }


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

    if decision == "memory_clarification_required":
        prompt = state.get("clarification_prompt") or "Could you please clarify your request?"
        response = prompt
        if guidance_snippet:
            response += f"\n\nRelevant policy guidance:\n{guidance_snippet}"

    elif decision == "confirmation_required" and action_result:
        msg = action_result.get("message", "Please confirm if you would like to proceed with this request.")
        response = msg
        if guidance_snippet:
            response += f"\n\nRelevant policy guidance:\n{guidance_snippet}"

    elif decision == "action_completed" and action_result:
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
    workflow.add_node("resolve_customer_context_node", resolve_customer_context_node)
    workflow.add_node("retrieve_knowledge_node", retrieve_knowledge_node)
    workflow.add_node("investigate_order_node", investigate_order_node)
    workflow.add_node("troubleshoot_node", troubleshoot_node)
    workflow.add_node("decide_next_step_node", decide_next_step_node)
    workflow.add_node("execute_action_node", execute_action_node)
    workflow.add_node("escalate_node", escalate_node)
    workflow.add_node("compose_response_node", compose_response_node)

    # 2. Add edges & conditional routing
    workflow.add_edge(START, "classify_intent_node")
    workflow.add_edge("classify_intent_node", "resolve_customer_context_node")
    workflow.add_edge("resolve_customer_context_node", "retrieve_knowledge_node")
    workflow.add_conditional_edges(
        "retrieve_knowledge_node",
        route_after_knowledge,
        {
            "investigate_order_node": "investigate_order_node",
            "troubleshoot_node": "troubleshoot_node",
        },
    )
    workflow.add_edge("investigate_order_node", "troubleshoot_node")
    workflow.add_edge("troubleshoot_node", "decide_next_step_node")
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

    # 1. Resolve multi-turn conversational memory before downstream nodes
    mem_res = resolve_session_memory(resolved_session_id, message)

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
        "customer_context": None,
        "knowledge_retrieval": None,
        "troubleshooting": None,
        "action_execution": None,
        "memory_resolution": mem_res.model_dump(),
        "resolved_order_id": mem_res.resolved_order_id,
        "confirmed_action": mem_res.confirmed_action,
        "confirmed_order_id": mem_res.confirmed_order_id,
        "clarification_needed": mem_res.clarification_needed,
        "clarification_prompt": mem_res.clarification_prompt,
        "memory": None,
        "escalation": None,
        "ticket_generation": None,
    }

    final_state = support_graph.invoke(initial_state)

    # 2. Update session memory with verified outputs from the completed workflow
    updated_session = update_session_memory(resolved_session_id, message, final_state)
    mem_summary = get_session_summary(resolved_session_id)

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
        "understanding": final_state.get("understanding"),
        "customer_context": final_state.get("customer_context"),
        "knowledge_retrieval": final_state.get("knowledge_retrieval"),
        "troubleshooting": final_state.get("troubleshooting"),
        "action_execution": final_state.get("action_execution"),
        "memory": mem_summary,
        "escalation": final_state.get("escalation"),
        "ticket_generation": final_state.get("ticket_generation"),
    }
