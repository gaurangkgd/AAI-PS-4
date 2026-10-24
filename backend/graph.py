"""Autonomous Customer Support System - LangGraph Multi-Agent Architecture.

Implements the revised 4-agent hierarchical supervisor architecture:
1. Master Supervisor Agent (Orchestration & Routing)
2. Support Triage Agent (Read-only Investigation & Knowledge Base Policy Search)
3. Action Execution Agent (Guarded Order Cancellations, Returns, & Refunds)
4. Escalation & Ticket Agent (Human Handoff, SLA Deadline Assignment, & CSAT Lifecycle)

Leverages LangGraph's native MemorySaver for session checkpointing and thread memory.
Operates seamlessly in full agentic mode when GEMINI_API_KEY is available, and provides
a deterministic LangGraph supervisor fallback when offline.
"""

import copy
import json
import logging
import os
import re
import uuid
from typing import Annotated, Any, Dict, List, Optional, TypedDict
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded regardless of how module is imported
_backend_env = Path(__file__).resolve().parent / ".env"
_root_env = Path(__file__).resolve().parent.parent / ".env"
if _backend_env.exists():
    load_dotenv(_backend_env)
elif _root_env.exists():
    load_dotenv(_root_env)
else:
    load_dotenv()

from langchain_core.messages import (

    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

try:
    from backend.tools.investigation import (
        lookup_order,
        lookup_payment,
        lookup_customer,
        search_knowledge_base,
        check_return_eligibility,
    )
    from backend.tools.actions import (
        cancel_order,
        request_return,
        initiate_refund,
    )
    from backend.tools.tickets import (
        create_support_ticket,
        update_ticket_status,
        search_tickets,
    )
    from backend.tools.metrics import (
        record_csat_rating,
        get_resolution_metrics,
    )
    from backend.prompts import (
        SUPERVISOR_PROMPT,
        TRIAGE_PROMPT,
        ACTION_PROMPT,
        ESCALATION_PROMPT,
    )
    from backend.mock_data import CUSTOMERS, ORDERS, PAYMENTS, TICKETS
except ImportError:
    from tools.investigation import (
        lookup_order,
        lookup_payment,
        lookup_customer,
        search_knowledge_base,
        check_return_eligibility,
    )
    from tools.actions import (
        cancel_order,
        request_return,
        initiate_refund,
    )
    from tools.tickets import (
        create_support_ticket,
        update_ticket_status,
        search_tickets,
    )
    from tools.metrics import (
        record_csat_rating,
        get_resolution_metrics,
    )
    from prompts import (
        SUPERVISOR_PROMPT,
        TRIAGE_PROMPT,
        ACTION_PROMPT,
        ESCALATION_PROMPT,
    )
    from mock_data import CUSTOMERS, ORDERS, PAYMENTS, TICKETS

logger = logging.getLogger(__name__)

ORDER_ID_RE = re.compile(r"\b(ORD\d{4,})\b", re.IGNORECASE)
CUSTOMER_ID_RE = re.compile(r"\b(CUST\d{3,})\b", re.IGNORECASE)
AFFIRMATIVE_RE = re.compile(r"\b(yes|yeah|yep|sure|proceed|confirm|go\s+ahead|do\s+it|please\s+do|affirmative)\b", re.IGNORECASE)
NEGATIVE_RE = re.compile(r"\b(no|nope|don't|do\s+not|cancel\s+that|stop|abort|nevermind|never\s+mind)\b", re.IGNORECASE)
HUMAN_AGENT_RE = re.compile(r"\b(human|agent|person|representative|supervisor|manager|specialist|operator)\b", re.IGNORECASE)
PAYMENT_ISSUE_RE = re.compile(r"\b(payment|deducted|debited|charged|failed|gateway|transaction|double\s+charge|overcharge)\b", re.IGNORECASE)
CANCEL_RE = re.compile(r"\b(cancel|cancellation|canceling|cancelling|abort\s+order)\b", re.IGNORECASE)
RETURN_RE = re.compile(r"\b(return|replace|replacement|exchange|damaged|broken|defective|wrong\s+item)\b", re.IGNORECASE)
TRACK_RE = re.compile(r"\b(track|tracking|where\s+is|status|shipped|delivery|courier|dispatch)\b", re.IGNORECASE)


class SupportAgentState(TypedDict, total=False):
    messages: Annotated[List[BaseMessage], add_messages]
    session_id: str
    user_message: str
    active_agent: Optional[str]
    intent: Optional[str]
    sentiment: Optional[str]
    priority: Optional[str]
    order_id: Optional[str]
    customer_id: Optional[str]
    pending_confirmation: Optional[Dict[str, Any]]
    investigation: Optional[Dict[str, Any]]
    knowledge_results: Optional[List[Dict[str, Any]]]
    ticket: Optional[Dict[str, Any]]
    action_result: Optional[Dict[str, Any]]
    decision: Optional[str]
    assistant_message: str


# ---------------------------------------------------------------------------
# Deterministic Supervisor Graph Nodes (Standard LangGraph)
# ---------------------------------------------------------------------------

def extract_entities(text: str) -> tuple[Optional[str], Optional[str]]:
    order_m = ORDER_ID_RE.search(text)
    cust_m = CUSTOMER_ID_RE.search(text)
    order_id = order_m.group(1).upper() if order_m else None
    cust_id = cust_m.group(1).upper() if cust_m else None
    return order_id, cust_id


GREETING_WORDS = {
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
    "howdy", "greetings", "help", "who are you", "what can you do", "yo",
}

def detect_intent(text: str) -> str:
    lower = text.lower().strip()
    words = lower.split()
    
    # Check for greeting
    if lower in GREETING_WORDS or (len(words) <= 3 and any(w in GREETING_WORDS for w in words) and not any(w in lower for w in ["order", "cancel", "return", "payment", "track", "delivery", "courier"])):
        return "greeting"

    if "reschedule" in lower or "change delivery" in lower:
        return "delivery_reschedule"
    if any(w in lower for w in ["when will", "eta", "estimated delivery", "arrival date", "how long will it take", "when can i expect"]):
        return "delivery_eta"
    if PAYMENT_ISSUE_RE.search(lower):
        return "payment_issue"
    if CANCEL_RE.search(lower):
        return "cancellation"
    if RETURN_RE.search(lower):
        return "return_or_replacement"
    if TRACK_RE.search(lower):
        return "order_tracking"
    if any(w in lower for w in ["warranty", "guarantee"]):
        return "warranty_inquiry"
    if any(w in lower for w in ["login", "password", "account", "profile"]):
        return "account_issue"
    if any(w in lower for w in ["price", "specs", "stock", "feature"]):
        return "product_inquiry"
    return "general_inquiry"


def detect_sentiment(text: str) -> str:
    lower = text.lower()
    frustrated_markers = ["ridiculous", "unacceptable", "furious", "stolen", "scam", "fraud", "terrible", "worst", "angry"]
    if any(m in lower for m in frustrated_markers):
        return "frustrated"
    if any(m in lower for m in ["fail", "error", "broken", "issue", "problem", "wrong"]):
        return "negative"
    if any(m in lower for m in ["thanks", "thank you", "great", "awesome", "perfect", "good"]):
        return "positive"
    return "neutral"


def supervisor_node(state: SupportAgentState) -> Dict[str, Any]:
    """Supervisor router node: inspects context, memory, and delegates to specialist."""
    message = state.get("user_message", "")
    session_id = state.get("session_id", "")
    
    # Check memory for existing active order ID or extract from current message
    order_id, cust_id = extract_entities(message)
    active_order_id = order_id or state.get("order_id")
    active_cust_id = cust_id or state.get("customer_id")

    # If active order exists but customer_id missing, infer from order
    if active_order_id and not active_cust_id:
        matching_order = next((o for o in ORDERS if o["id"].upper() == active_order_id), None)
        if matching_order:
            active_cust_id = matching_order.get("customer_id")

    intent = detect_intent(message)
    sentiment = detect_sentiment(message)
    priority = "high" if sentiment == "frustrated" or intent == "payment_issue" else "medium"

    # Only infer active_order_id if the user is ACTUALLY inquiring about an order/package!
    order_inquiry_intents = {"order_tracking", "cancellation", "return_or_replacement", "payment_issue", "delivery_reschedule", "delivery_eta"}
    mentions_order = any(w in message.lower() for w in ["order", "package", "parcel", "item", "shipment", "delivery", "purchase", "courier", "track"])

    if active_cust_id and not active_order_id and (intent in order_inquiry_intents or mentions_order) and intent != "greeting":
        cust_orders = [o for o in ORDERS if o.get("customer_id", "").upper() == active_cust_id.upper()]
        if cust_orders:
            cust_orders_sorted = sorted(cust_orders, key=lambda x: x.get("created_at", ""), reverse=True)
            lower_msg = message.lower()
            if any(w in lower_msg for w in ["cancel", "cancellation", "abort"]):
                cancellable = next((o for o in cust_orders_sorted if o.get("status") in ["processing", "pending_payment"]), None)
                active_order_id = cancellable["id"] if cancellable else cust_orders_sorted[0]["id"]
            elif any(w in lower_msg for w in ["return", "replacement", "replace", "exchange"]):
                returnable = next((o for o in cust_orders_sorted if o.get("status") == "delivered"), None)
                active_order_id = returnable["id"] if returnable else cust_orders_sorted[0]["id"]
            elif any(w in lower_msg for w in ["payment", "failed", "deducted", "debited"]):
                pay_issue = next((o for o in cust_orders_sorted if o.get("status") in ["payment_failed", "pending_payment"]), None)
                active_order_id = pay_issue["id"] if pay_issue else cust_orders_sorted[0]["id"]
            else:
                active_order_id = cust_orders_sorted[0]["id"]

    # Natural, friendly greeting response
    if intent == "greeting":
        cust_name = "there"
        recent_order_note = ""
        if active_cust_id:
            cust = next((c for c in CUSTOMERS if c.get("id", "").upper() == active_cust_id.upper()), None)
            if cust:
                cust_name = cust.get("name", "there")
            cust_orders = [o for o in ORDERS if o.get("customer_id", "").upper() == active_cust_id.upper()]
            if cust_orders:
                recent_id = cust_orders[-1]["id"]
                recent_st = cust_orders[-1]["status"]
                recent_order_note = f" I see your recent order {recent_id} is currently '{recent_st}'."

        return {
            "active_agent": "supervisor",
            "intent": "greeting",
            "order_id": None,
            "customer_id": active_cust_id,
            "assistant_message": f"Hello {cust_name}! Welcome to NextStore Support.{recent_order_note} How may I assist you today? You can ask me to track your package, manage returns or cancellations, or answer any policy questions.",
            "decision": "greeting",
            "investigation": {"attempted": False, "status": "not_requested"},
        }

    # Check for pending confirmation response in multi-turn memory
    pending_conf = state.get("pending_confirmation")
    if pending_conf and pending_conf.get("is_pending"):
        if AFFIRMATIVE_RE.search(message):
            return {
                "active_agent": "action_agent",
                "intent": pending_conf.get("action", intent),
                "order_id": pending_conf.get("order_id", active_order_id),
                "customer_id": active_cust_id,
                "sentiment": sentiment,
                "priority": priority,
                "decision": "confirmed_action_execution",
            }
        elif NEGATIVE_RE.search(message):
            return {
                "active_agent": "supervisor",
                "pending_confirmation": None,
                "assistant_message": f"Understood. The action for order {pending_conf.get('order_id')} has been cancelled. How else may I assist you today?",
                "decision": "action_cancelled_by_user",
            }

    # Explicit human agent / supervisor request -> immediate escalation
    if HUMAN_AGENT_RE.search(message) and any(w in message.lower() for w in ["speak", "talk", "transfer", "connect", "human", "manager", "supervisor"]):
        return {
            "active_agent": "escalation_agent",
            "intent": intent,
            "order_id": active_order_id,
            "customer_id": active_cust_id,
            "sentiment": sentiment,
            "priority": "urgent" if sentiment == "frustrated" else "high",
            "decision": "direct_human_escalation",
        }

    # Actionable requests vs Policy inquiries
    is_policy_inquiry = any(w in message.lower() for w in ["policy", "how to", "what is", "rules", "faq", "terms", "condition", "can i", "tell me about"])
    if intent in {"cancellation", "return_or_replacement"} and not is_policy_inquiry:
        return {
            "active_agent": "action_agent",
            "intent": intent,
            "order_id": active_order_id,
            "customer_id": active_cust_id,
            "sentiment": sentiment,
            "priority": priority,
            "decision": "route_to_action",
        }

    # Default: Route to Triage Agent for fact checking, tracking, or diagnosis
    return {
        "active_agent": "triage_agent",
        "intent": intent,
        "order_id": active_order_id,
        "customer_id": active_cust_id,
        "sentiment": sentiment,
        "priority": priority,
        "decision": "route_to_triage",
    }


def supervisor_router(state: SupportAgentState) -> str:
    """Conditional router based on supervisor's delegation decision."""
    agent = state.get("active_agent")
    if agent == "action_agent":
        return "action_agent_node"
    if agent == "escalation_agent":
        return "escalation_agent_node"
    if agent == "supervisor":
        return END
    return "triage_agent_node"


def triage_agent_node(state: SupportAgentState) -> Dict[str, Any]:
    """Triage Agent: invokes investigation tools, searches policies, diagnoses root cause."""
    order_id = state.get("order_id")
    customer_id = state.get("customer_id")
    intent = state.get("intent", "general_inquiry")
    message = state.get("user_message", "")

    investigation_data: Dict[str, Any] = {"attempted": False, "status": "order_id_required"}
    knowledge_list: List[Dict[str, Any]] = []

    # 1. Look up policy guidance
    kb_res_raw = search_knowledge_base.invoke({"query": message, "category": intent})
    try:
        kb_parsed = json.loads(kb_res_raw)
        knowledge_list = kb_parsed.get("articles", [])
    except Exception:
        knowledge_list = []

    # 2. Look up customer context if known
    customer_profile = None
    if customer_id:
        cust_raw = lookup_customer.invoke({"customer_id": customer_id})
        try:
            customer_profile = json.loads(cust_raw)
        except Exception:
            customer_profile = None

    # 3. Investigate order & payment if order_id is present
    if order_id:
        order_raw = lookup_order.invoke({"order_id": order_id})
        order_data = json.loads(order_raw)
        
        pay_raw = lookup_payment.invoke({"order_id": order_id})
        pay_data = json.loads(pay_raw)

        if order_data.get("found"):
            investigation_data = {
                "attempted": True,
                "order_id": order_id,
                "status": "found",
                "order": {
                    "id": order_data["order_id"],
                    "customer_id": order_data.get("customer_id"),
                    "status": order_data.get("status"),
                    "total_amount": order_data.get("total_amount"),
                    "created_at": order_data.get("created_at"),
                    "items": order_data.get("items", []),
                },
                "payments": pay_data.get("payments", []),
                "summary": (
                    f"Order {order_id} is currently '{order_data.get('status')}' "
                    f"(Total: ${order_data.get('total_amount', 0.0):.2f}). "
                    f"Payment status: {pay_data.get('payments', [{}])[0].get('status', 'none') if pay_data.get('has_payments') else 'no payments'}."
                ),
            }
        else:
            investigation_data = {
                "attempted": True,
                "order_id": order_id,
                "status": "order_not_found",
                "summary": f"Order '{order_id}' was not found in our records.",
            }

    # Evaluate whether triage should escalate to human specialist
    should_escalate = False
    escalation_reason = None
    target_team = "general_support"

    # Case A: Payment deduction claimed on failed order
    if intent == "payment_issue" and investigation_data.get("status") == "found":
        order_st = investigation_data.get("order", {}).get("status")
        payments = investigation_data.get("payments", [])
        has_failed_pay = any(p.get("status") == "failed" for p in payments)
        if order_st in {"payment_failed", "pending_payment"} or has_failed_pay:
            should_escalate = True
            escalation_reason = (
                f"Verified payment failure for order {order_id}. Customer reports funds deducted while order status is '{order_st}'."
            )
            target_team = "billing_support"

    if should_escalate:
        return {
            "investigation": investigation_data,
            "knowledge_results": knowledge_list,
            "active_agent": "escalation_agent",
            "decision": "escalate",
            "priority": "high",
            "escalation_reason": escalation_reason,
            "target_team": target_team,
        }

    # Otherwise synthesize resolution response
    kb_guidance = knowledge_list[0].get("guidance", "") if knowledge_list else ""
    # Synthesize responsive, intelligent agent resolution
    order_data = investigation_data.get("order") or {}
    order_st = order_data.get("status", "")
    items_list = order_data.get("items", [])
    item_names = ", ".join(i.get("name", "item") for i in items_list) if items_list else "items"
    cust_name = customer_profile.get("name") if customer_profile else (customer_id or "Valued Customer")

    # 1. Delivery Rescheduling Inquiry
    if "reschedule" in message.lower() or intent == "delivery_reschedule":
        if investigation_data.get("status") == "found":
            asst_msg = (
                f"Yes, you can reschedule your delivery! For order {order_id} ({item_names}, status: '{order_st}'), "
                "you can select an alternate delivery date or time window directly through the courier's tracking link once active scans appear. "
                "If a courier delivery attempt is ever missed, the carrier automatically re-attempts delivery on the next business day."
            )
        else:
            asst_msg = (
                "Yes, our logistics courier partners allow delivery rescheduling! "
                "Once your shipment is in transit, you can click the tracking link provided in your shipping confirmation to select a new delivery window. "
                "If an attempt is missed, the driver will automatically attempt delivery on the following business day."
            )
        decision = "delivery_reschedule"

    # 2. Delivery ETA & Timeline
    elif any(w in message.lower() for w in ["when will", "eta", "arrive", "arrival", "delivery time"]) or intent == "delivery_eta":
        if investigation_data.get("status") == "found":
            if order_st == "delivered":
                asst_msg = f"Order {order_id} ({item_names}) was delivered on {order_data.get('created_at', '')[:10]}. If you have any delivery discrepancies, please let me know."
            elif order_st == "shipped":
                asst_msg = (
                    f"Order {order_id} ({item_names}) is currently dispatched and in transit with our courier partner. "
                    "Standard domestic delivery typically completes within 2 to 3 business days from the dispatch date. "
                    "Live milestone scans will appear directly on your carrier tracking link."
                )
            elif order_st == "processing":
                asst_msg = (
                    f"Order {order_id} ({item_names}) is currently being prepared at our fulfillment center. "
                    "It will ship shortly. Standard transit time is 2-3 business days once handed over to the courier."
                )
            else:
                asst_msg = f"Order {order_id} is currently in '{order_st}' status."
        else:
            asst_msg = (
                "Standard deliveries typically arrive within 2 to 3 business days after order dispatch. "
                "If you have an active order number, please share it so I can provide live GPS tracking details."
            )
        decision = "delivery_eta"

    # 3. Warranty & Quality Guarantee Inquiry
    elif any(w in message.lower() for w in ["warranty", "guarantee"]) or intent == "warranty_inquiry":
        asst_msg = (
            "All NextStore electronic goods are backed by a 2-Year Comprehensive Manufacturer Warranty covering hardware defects and technical anomalies. "
            "Apparel, footwear, and lifestyle goods include a 1-Year Quality Assurance Guarantee. "
            "If an item experiences defects during regular use, we provide complimentary repairs or direct replacements."
        )
        decision = "warranty_inquiry"

    # 4. Return & Refund Policy Inquiry
    elif any(w in message.lower() for w in ["return policy", "refund policy", "how to return"]) or (intent == "return_or_replacement" and any(w in message.lower() for w in ["policy", "how", "what", "can i"])):
        asst_msg = (
            "Our Return Policy provides a 30-day risk-free return window for all unused items in their original packaging. "
            "Pre-paid shipping labels are provided automatically. Once inspected at our returns depot, refunds are credited back to your original payment method within 3 to 5 business days."
        )
        if order_st == "delivered":
            asst_msg += f"\n\nYour delivered order {order_id} ({item_names}) is currently eligible for return! Would you like me to initiate a return authorization?"
        decision = "return_policy"

    # 5. Order Tracking / Status Inquiry
    elif investigation_data.get("status") == "found":
        total_amt = order_data.get("total_amount", 0.0)
        pay_st = pay_data.get("payments", [{}])[0].get("status", "verified") if pay_data.get("has_payments") else "verified"
        asst_msg = (
            f"Here is the verified status for order {order_id} ({item_names}):\n"
            f"- Current Status: '{order_st.upper()}'\n"
            f"- Total Amount: ${total_amt:.2f}\n"
            f"- Payment Status: {pay_st.title()}\n\n"
        )
        if order_st == "shipped":
            asst_msg += "Your order has been handed over to our logistics partner and is actively in transit. Standard delivery is expected within 2-3 business days."
        elif order_st == "processing":
            asst_msg += "Your order is confirmed and currently being packed at our warehouse. It will dispatch soon."
        elif order_st == "delivered":
            asst_msg += "Your order was successfully delivered. Let me know if you would like to initiate a return or exchange."
        else:
            asst_msg += f"Current order state: {order_st}."
        decision = "order_found"

    # 6. Order Not Found
    elif investigation_data.get("status") == "order_not_found":
        asst_msg = (
            f"I checked our verified database but could not find any records for order '{order_id}'. "
            "Please double-check the order number or provide additional details so I can assist you."
        )
        decision = "order_not_found"

    # 7. Customer with No Orders
    elif not order_id and customer_profile and intent in {"order_tracking", "payment_issue", "cancellation", "return_or_replacement"}:
        asst_msg = (
            f"Hello {cust_name}! I reviewed your account ({customer_id}), but there are no active or past orders on file. "
            "If your order was placed under a guest checkout or different email, please provide the Order ID (e.g. ORD1001)."
        )
        decision = "customer_no_orders"

    # 8. Order ID required
    elif not order_id and intent in {"order_tracking", "payment_issue", "cancellation", "return_or_replacement"}:
        asst_msg = (
            "To assist you with your order, could you please provide your Order ID "
            "(for example, ORD1001)? Once provided, I can pull up the verified tracking and payment status."
        )
        if kb_guidance:
            asst_msg += f"\n\nIn the meantime:\n{kb_guidance}"
        decision = "order_id_required"

    elif kb_guidance:
        asst_msg = f"Regarding your inquiry ({intent.replace('_', ' ')}):\n{kb_guidance}"
        decision = "knowledge_guidance"
    else:
        asst_msg = (
            f"Hello {cust_name}! Welcome to NextStore customer support. I am here to help you with order tracking, "
            "cancellations, returns, shipping estimates, and product questions. Please let me know how I can assist you today."
        )
        decision = "general_inquiry"

    return {
        "investigation": investigation_data,
        "knowledge_results": knowledge_list,
        "assistant_message": asst_msg,
        "decision": decision,
    }


def triage_router(state: SupportAgentState) -> str:
    """Route from triage to escalation if dispute detected, else finish."""
    if state.get("active_agent") == "escalation_agent":
        return "escalation_agent_node"
    return END


def action_agent_node(state: SupportAgentState) -> Dict[str, Any]:
    """Action Agent: checks eligibility, enforces confirmation guards, and executes actions."""
    order_id = state.get("order_id")
    intent = state.get("intent", "cancellation")
    message = state.get("user_message", "")
    decision = state.get("decision")
    pending_conf = state.get("pending_confirmation")

    if not order_id:
        return {
            "assistant_message": "An Order ID (such as ORD1001) is required to process cancellations, returns, or replacements.",
            "decision": "order_id_required",
        }

    # Verify order state first
    order_raw = lookup_order.invoke({"order_id": order_id})
    order_data = json.loads(order_raw)

    if not order_data.get("found"):
        return {
            "assistant_message": f"I could not locate order '{order_id}' to execute this action. Please verify the order number.",
            "decision": "order_not_found",
        }

    curr_status = order_data.get("status", "").lower()

    # Cancellation Action
    if "cancel" in intent:
        if curr_status != "processing":
            asst_msg = (
                f"Unable to cancel order {order_id}. "
                f"Its current status is '{curr_status}'. Only orders in 'processing' status can be cancelled."
            )
            if curr_status == "delivered":
                asst_msg += " Since your order is delivered, you may request a return or replacement instead."
            elif curr_status == "shipped":
                asst_msg += " Because the order has already shipped, you may refuse delivery upon arrival."
            return {
                "assistant_message": asst_msg,
                "decision": "action_rejected",
                "action_result": {
                    "success": False,
                    "action": "cancellation",
                    "order_id": order_id,
                    "message": asst_msg,
                },
                "pending_confirmation": None,
            }

        # Check if user has confirmed
        is_confirmed = (
            decision == "confirmed_action_execution"
            or AFFIRMATIVE_RE.search(message)
            or any(w in message.lower() for w in ["yes", "proceed", "cancel it now", "confirm cancellation"])
        )

        if not is_confirmed:
            # Require explicit confirmation
            item_name = order_data.get("items", [{}])[0].get("name", "items")
            return {
                "assistant_message": (
                    f"Order {order_id} is currently processing ({item_name}, Total: ${order_data.get('total_amount', 0):.2f}). "
                    "Are you sure you would like to proceed with cancelling this order? Please reply 'yes' to confirm."
                ),
                "decision": "confirmation_required",
                "pending_confirmation": {
                    "is_pending": True,
                    "action": "cancellation",
                    "order_id": order_id,
                },
                "action_result": {
                    "success": False,
                    "action": "cancellation",
                    "order_id": order_id,
                    "message": "Awaiting customer confirmation to cancel processing order.",
                },
            }

        # Confirmed: Execute cancellation tool
        exec_raw = cancel_order.invoke({"order_id": order_id, "reason": "Customer confirmed cancellation"})
        exec_res = json.loads(exec_raw)
        return {
            "assistant_message": f"Your request has been processed:\n{exec_res.get('message')}",
            "decision": "action_completed",
            "action_result": {
                "success": exec_res.get("success", False),
                "action": "cancellation",
                "order_id": order_id,
                "message": exec_res.get("message"),
                "order": {
                    "id": order_id,
                    "customer_id": order_data.get("customer_id"),
                    "status": "cancelled",
                    "total_amount": order_data.get("total_amount"),
                    "created_at": order_data.get("created_at"),
                    "items": order_data.get("items", []),
                },
            },
            "pending_confirmation": None,
        }

    # Return or Replacement Action
    if "return" in intent or "replace" in intent:
        req_type = "replacement" if "replace" in intent or "replace" in message.lower() else "return"
        elig_raw = check_return_eligibility.invoke({"order_id": order_id})
        elig_data = json.loads(elig_raw)

        if not elig_data.get("is_eligible"):
            asst_msg = f"Unable to process {req_type} for order {order_id}: {elig_data.get('reason')}"
            return {
                "assistant_message": asst_msg,
                "decision": "action_rejected",
                "action_result": {
                    "success": False,
                    "action": "return_or_replacement",
                    "order_id": order_id,
                    "message": asst_msg,
                },
                "pending_confirmation": None,
            }

        # Execute return tool
        ret_raw = request_return.invoke({"order_id": order_id, "request_type": req_type, "reason": message})
        ret_res = json.loads(ret_raw)
        return {
            "assistant_message": (
                f"Your request has been processed:\n{ret_res.get('message')}\n"
                f"Return Authorization ID: {ret_res.get('request_id')}. Pre-paid UPS label generated."
            ),
            "decision": "action_completed",
            "action_result": {
                "success": True,
                "action": "return_or_replacement",
                "order_id": order_id,
                "message": ret_res.get("message"),
                "return_request": {
                    "request_id": ret_res.get("request_id"),
                    "order_id": order_id,
                    "request_type": req_type,
                    "status": "approved",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            },
            "pending_confirmation": None,
        }

    return {
        "assistant_message": f"Action for intent '{intent}' could not be processed automatically.",
        "decision": "action_unsupported",
    }


def escalation_agent_node(state: SupportAgentState) -> Dict[str, Any]:
    """Escalation & Ticket Agent: generates deduplicated support ticket with SLA and department routing."""
    session_id = state.get("session_id", "")
    customer_id = state.get("customer_id")
    order_id = state.get("order_id")
    intent = state.get("intent", "general_inquiry")
    message = state.get("user_message", "")
    priority = state.get("priority", "medium")
    reason = state.get("escalation_reason") or "Issue requires human customer support specialist review."
    team = state.get("target_team") or ("billing_support" if intent == "payment_issue" else "general_support")

    # Search for existing open ticket for this session or order
    existing_raw = search_tickets.invoke({"customer_id": customer_id or "", "order_id": order_id or "", "status": "open"})
    try:
        existing_data = json.loads(existing_raw)
        matching_tickets = existing_data.get("tickets", [])
    except Exception:
        matching_tickets = []

    if matching_tickets:
        existing_tkt = matching_tickets[0]
        ticket_id = existing_tkt["ticket_id"]
        asst_msg = (
            f"Your issue is already actively tracked under Ticket ID: {ticket_id} ({existing_tkt.get('target_team')}). "
            f"A customer support specialist is assigned and working on your case."
        )
        ticket_obj = {
            "ticket_id": ticket_id,
            "session_id": session_id,
            "customer_id": customer_id,
            "order_id": order_id,
            "category": existing_tkt.get("category", intent),
            "priority": existing_tkt.get("priority", priority),
            "status": existing_tkt.get("status", "open"),
            "original_message": existing_tkt.get("original_message", message),
            "escalation_reason": reason,
            "target_team": existing_tkt.get("target_team", team),
            "created_at": existing_tkt.get("created_at"),
            "is_reused": True,
        }
    else:
        # Create new support ticket via tool
        title = f"[{team.replace('_', ' ').title()}] {intent.replace('_', ' ').title()} - {order_id or 'General'}"
        tkt_raw = create_support_ticket.invoke({
            "title": title,
            "category": intent,
            "priority": priority,
            "escalation_reason": reason,
            "customer_id": customer_id or "",
            "order_id": order_id or "",
            "target_team": team,
            "internal_notes": f"Escalated via AI Support Workflow. Customer Statement: '{message}'",
        })
        tkt_res = json.loads(tkt_raw)
        ticket_id = tkt_res.get("ticket_id")

        asst_msg = (
            f"Your issue has been referred for human support review (Ticket ID: {ticket_id}). "
            f"A specialist from {team.replace('_', ' ').title()} will review your details and follow up. "
            f"Target SLA Response Deadline: {tkt_res.get('sla_deadline', 'Within 4 hours')}."
        )
        ticket_obj = {
            "ticket_id": ticket_id,
            "session_id": session_id,
            "customer_id": customer_id,
            "order_id": order_id,
            "category": intent,
            "priority": priority,
            "status": "open",
            "original_message": message,
            "escalation_reason": reason,
            "target_team": team,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_reused": False,
        }

    return {
        "ticket": ticket_obj,
        "assistant_message": asst_msg,
        "decision": "escalated",
    }


# ---------------------------------------------------------------------------
# LangGraph Workflow Construction: Dual-Mode (Agentic ReAct + Deterministic Fallback)
# ---------------------------------------------------------------------------

def build_deterministic_support_graph():
    """Construct and compile the deterministic multi-agent state graph."""
    workflow = StateGraph(SupportAgentState)

    # Add Nodes
    workflow.add_node("supervisor_node", supervisor_node)
    workflow.add_node("triage_agent_node", triage_agent_node)
    workflow.add_node("action_agent_node", action_agent_node)
    workflow.add_node("escalation_agent_node", escalation_agent_node)

    # Add Edges
    workflow.add_edge(START, "supervisor_node")
    workflow.add_conditional_edges(
        "supervisor_node",
        supervisor_router,
        {
            "triage_agent_node": "triage_agent_node",
            "action_agent_node": "action_agent_node",
            "escalation_agent_node": "escalation_agent_node",
            END: END,
        },
    )
    workflow.add_conditional_edges(
        "triage_agent_node",
        triage_router,
        {
            "escalation_agent_node": "escalation_agent_node",
            END: END,
        },
    )
    workflow.add_edge("action_agent_node", END)
    workflow.add_edge("escalation_agent_node", END)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


def build_agentic_supervisor_graph(api_key: str):
    """Build the dynamic ReAct multi-agent supervisor graph using Gemini."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langgraph.prebuilt import create_react_agent
        from langgraph_supervisor import create_supervisor

        raw_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
        model_name = raw_model if raw_model.startswith(("gemini-", "models/")) else f"gemini-{raw_model}"

        model = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.1,
        )

        triage_agent = create_react_agent(
            model=model,
            tools=[
                lookup_order,
                lookup_payment,
                lookup_customer,
                search_knowledge_base,
                check_return_eligibility,
            ],
            name="triage_agent",
            prompt=TRIAGE_PROMPT,
        )

        action_agent = create_react_agent(
            model=model,
            tools=[
                cancel_order,
                request_return,
                initiate_refund,
                lookup_order,
            ],
            name="action_agent",
            prompt=ACTION_PROMPT,
        )

        escalation_agent = create_react_agent(
            model=model,
            tools=[
                create_support_ticket,
                update_ticket_status,
                search_tickets,
                record_csat_rating,
                get_resolution_metrics,
            ],
            name="escalation_agent",
            prompt=ESCALATION_PROMPT,
        )

        workflow = create_supervisor(
            agents=[triage_agent, action_agent, escalation_agent],
            model=model,
            prompt=SUPERVISOR_PROMPT,
            output_mode="full_history",
        )

        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    except Exception as e:
        logger.warning(f"Could not initialize agentic supervisor graph ({e}), falling back to deterministic mode.")
        return None


# Initialize graphs
support_graph = build_deterministic_support_graph()

_gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
agentic_graph = build_agentic_supervisor_graph(_gemini_key) if _gemini_key else None


def run_support_workflow(
    message: str,
    session_id: Optional[str] = None,
    customer_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute the multi-agent customer support workflow for a message in a session thread.

    Maintains thread memory via LangGraph MemorySaver checkpointer.
    Attempts ReAct agentic supervisor when GEMINI_API_KEY is configured,
    and falls back to deterministic supervisor graph seamlessly.
    """
    resolved_session_id = session_id.strip() if session_id and session_id.strip() else str(uuid.uuid4())
    config = {"configurable": {"thread_id": resolved_session_id}}

    resolved_customer_id = customer_id.strip() if customer_id and customer_id.strip() else None

    initial_state: SupportAgentState = {
        "messages": [HumanMessage(content=message)],
        "session_id": resolved_session_id,
        "user_message": message,
        "customer_id": resolved_customer_id,
    }

    # Try agentic supervisor if configured
    if agentic_graph is not None:
        try:
            # Build customer context header if customer_id is linked
            system_context_prefix = ""
            if resolved_customer_id:
                matching_cust = next((c for c in CUSTOMERS if c["id"].upper() == resolved_customer_id.upper()), None)
                cust_orders = [o for o in ORDERS if o.get("customer_id", "").upper() == resolved_customer_id.upper()]
                orders_summary = ", ".join([f"{o['id']} ({o['status']}, items: {len(o.get('items', []))})" for o in cust_orders])
                cust_name = matching_cust.get("name") if matching_cust else resolved_customer_id
                system_context_prefix = (
                    f"[Verified Customer Context: Customer Name: {cust_name}, Customer ID: {resolved_customer_id}. "
                    f"Known Orders: {orders_summary or 'None'}]. "
                )

            full_user_prompt = f"{system_context_prefix}{message}" if system_context_prefix else message

            res = agentic_graph.invoke(
                {"messages": [HumanMessage(content=full_user_prompt)]},
                config=config,
            )

            # Parse message history to extract agent stages and tool executions
            agent_stages = []
            extracted_knowledge = []
            extracted_investigation = None
            extracted_action_result = None
            extracted_ticket = None
            active_agent_name = "supervisor"
            asst_text = ""


            messages_list = res.get("messages", [])
            for m in messages_list:
                m_type = type(m).__name__
                name = getattr(m, "name", None) or ("user" if m_type == "HumanMessage" else "supervisor")
                tool_calls = getattr(m, "tool_calls", None) or []
                raw_content = getattr(m, "content", "")

                # Normalise content string
                text_content = ""
                if isinstance(raw_content, str):
                    text_content = raw_content
                elif isinstance(raw_content, list):
                    for part in raw_content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text_content += part.get("text", "")
                        elif isinstance(part, str):
                            text_content += part
                else:
                    text_content = str(raw_content)

                if m_type == "AIMessage":
                    if tool_calls:
                        for tc in tool_calls:
                            tc_name = tc.get("name", "")
                            tc_args = tc.get("args", {})
                            if tc_name.startswith("transfer_to_"):
                                target_agent = tc_name.replace("transfer_to_", "")
                                agent_stages.append({
                                    "stage": "Routing & Delegation",
                                    "agent": "Master Supervisor",
                                    "action": f"Delegating query to specialist: {target_agent}",
                                    "detail": f"Supervisor routed conversation to '{target_agent}' for specialized handling.",
                                    "status": "completed",
                                })
                            else:
                                agent_stages.append({
                                    "stage": "Specialist Tool Execution",
                                    "agent": name,
                                    "action": f"Executing tool: {tc_name}",
                                    "detail": f"Calling `{tc_name}` with parameters: {json.dumps(tc_args)}",
                                    "status": "completed",
                                })
                    elif text_content and name != "user":
                        asst_text = text_content
                        active_agent_name = name
                        agent_stages.append({
                            "stage": "Multi-Agent Synthesis",
                            "agent": name,
                            "action": "Generated final answer via Gemini",
                            "detail": f"{name} synthesized tool evidence and formulated customer response.",
                            "status": "completed",
                        })

                elif m_type == "ToolMessage":
                    tool_name = getattr(m, "name", "tool")
                    # Check if tool returned knowledge base articles, order info, action execution, or tickets
                    try:
                        parsed_content = json.loads(text_content) if isinstance(text_content, str) and text_content.startswith("{") else None
                        if isinstance(parsed_content, dict):
                            if "articles" in parsed_content:
                                for art in parsed_content.get("articles", []):
                                    if art not in extracted_knowledge:
                                        extracted_knowledge.append(art)
                            if "order_id" in parsed_content and parsed_content.get("found"):
                                extracted_investigation = {
                                    "attempted": True,
                                    "order_id": parsed_content.get("order_id"),
                                    "status": "found",
                                    "order": {
                                        "id": parsed_content.get("order_id"),
                                        "customer_id": parsed_content.get("customer_id", ""),
                                        "items": parsed_content.get("items", []),
                                        "total_amount": parsed_content.get("total_amount", 0.0),
                                        "status": parsed_content.get("status", ""),
                                        "created_at": parsed_content.get("created_at", ""),
                                    },
                                    "summary": f"Order {parsed_content.get('order_id')} is currently '{parsed_content.get('status')}'.",
                                }
                            # Extract action execution (cancellation, return request)
                            if "action" in parsed_content and "success" in parsed_content:
                                extracted_action_result = {
                                    "success": parsed_content.get("success", True),
                                    "action": parsed_content.get("action", ""),
                                    "order_id": parsed_content.get("order_id", ""),
                                    "message": parsed_content.get("message", ""),
                                    "return_request": parsed_content.get("return_request"),
                                }
                            # Extract support ticket
                            if "ticket_id" in parsed_content and "target_team" in parsed_content:
                                extracted_ticket = {
                                    "ticket_id": parsed_content.get("ticket_id"),
                                    "customer_id": parsed_content.get("customer_id"),
                                    "category": parsed_content.get("category", "general"),
                                    "priority": parsed_content.get("priority", "medium"),
                                    "status": parsed_content.get("status", "open"),
                                    "escalation_reason": parsed_content.get("escalation_reason") or parsed_content.get("reason", ""),
                                    "target_team": parsed_content.get("target_team"),
                                    "created_at": parsed_content.get("created_at"),
                                }
                    except Exception:
                        pass


                    if not tool_name.startswith("transfer_"):
                        agent_stages.append({
                            "stage": "Evidence Retrieval",
                            "agent": name or "Tool System",
                            "action": f"Received output from `{tool_name}`",
                            "detail": text_content[:180] + ("..." if len(text_content) > 180 else ""),
                            "status": "completed",
                        })

            if asst_text:
                order_id, cust_id = extract_entities(message)
                cust_id = cust_id or resolved_customer_id
                intent = detect_intent(message)

                # Determine if the assistant is asking for confirmation or has resolved
                decision = "agentic_resolved"
                lower_asst = asst_text.lower()
                if extracted_action_result:
                    if extracted_action_result.get("success"):
                        decision = "action_completed"
                    else:
                        decision = "action_rejected"
                elif extracted_ticket:
                    decision = "escalated"
                elif any(phrase in lower_asst for phrase in ["are you sure", "confirm to proceed", "please reply 'yes'", "please confirm", "proceed with cancelling", "would you like to proceed"]):
                    decision = "confirmation_required"
                elif intent == "order_tracking" and extracted_investigation and extracted_investigation.get("found"):
                    decision = "order_found"

                return {
                    "session_id": resolved_session_id,
                    "user_message": message,
                    "assistant_message": asst_text,
                    "intent": intent,
                    "status": "received",
                    "decision": decision,
                    "ticket": extracted_ticket,
                    "action_result": extracted_action_result,
                    "investigation": extracted_investigation,
                    "knowledge_results": extracted_knowledge,


                    "understanding": {
                        "intent": intent,
                        "sentiment": detect_sentiment(message),
                        "priority": "medium",
                        "active_agent": active_agent_name,
                        "mode": "agentic_react_supervisor",
                    },
                    "customer_context": {"customer_id": cust_id, "order_id": order_id},
                    "knowledge_retrieval": None,
                    "troubleshooting": None,
                    "action_execution": extracted_action_result,
                    "memory": {"session_id": resolved_session_id, "active_order_id": order_id},
                    "escalation": {"escalated": bool(extracted_ticket), "ticket_id": extracted_ticket.get("ticket_id") if extracted_ticket else None},
                    "ticket_generation": extracted_ticket,
                    "agent_stages": agent_stages,
                }


        except Exception as exc:
            logger.warning(f"Agentic supervisor execution failed ({exc}), falling back to deterministic graph.")

    # Fallback to deterministic supervisor state graph
    final_state = support_graph.invoke(initial_state, config=config)

    # Format return dictionary adhering to ChatResponse API schema
    intent = final_state.get("intent", "general_inquiry")
    decision = final_state.get("decision", "general_inquiry")
    ticket = final_state.get("ticket")
    action_result = final_state.get("action_result")
    investigation = final_state.get("investigation")
    knowledge_results = final_state.get("knowledge_results") or []

    return {
        "session_id": resolved_session_id,
        "user_message": message,
        "assistant_message": final_state.get("assistant_message", ""),
        "intent": intent,
        "status": "received",
        "decision": decision,
        "ticket": ticket,
        "action_result": action_result,
        "investigation": investigation,
        "knowledge_results": knowledge_results,
        "understanding": {
            "intent": intent,
            "sentiment": final_state.get("sentiment", "neutral"),
            "priority": final_state.get("priority", "medium"),
            "active_agent": final_state.get("active_agent", "supervisor"),
        },
        "customer_context": {
            "customer_id": final_state.get("customer_id"),
            "order_id": final_state.get("order_id"),
        },
        "knowledge_retrieval": {
            "query": message,
            "articles": knowledge_results,
        },
        "troubleshooting": {
            "summary": investigation.get("summary") if investigation else None,
        },
        "action_execution": action_result,
        "memory": {
            "session_id": resolved_session_id,
            "active_order_id": final_state.get("order_id"),
            "pending_confirmation": bool(final_state.get("pending_confirmation")),
        },
        "escalation": {
            "escalated": bool(ticket),
            "ticket_id": ticket.get("ticket_id") if ticket else None,
        },
        "ticket_generation": ticket,
        "agent_stages": [
            {
                "stage": "Intent & Entity Analysis",
                "agent": "Master Supervisor",
                "action": f"Classified intent as '{intent}'",
                "detail": f"Detected priority: {final_state.get('priority', 'medium')}, sentiment: {final_state.get('sentiment', 'neutral')}.",
                "status": "completed",
            },
            {
                "stage": "Specialist Delegation",
                "agent": final_state.get("active_agent", "supervisor"),
                "action": f"Handled by {final_state.get('active_agent', 'supervisor')}",
                "detail": f"Evaluated decision rule: '{decision}'.",
                "status": "completed",
            },
            {
                "stage": "Response Formulation",
                "agent": final_state.get("active_agent", "supervisor"),
                "action": "Compiled verified customer response",
                "detail": "Formulated response from ground truth records and knowledge base policies.",
                "status": "completed",
            },
        ],
    }

