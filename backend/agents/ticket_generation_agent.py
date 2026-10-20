"""Ticket Generation Agent.

The eighth specialized agent in the Agentic Customer Support System (PS-04).
Responsible for generating clear, actionable, structured support tickets for
unresolved, escalated, or human-review-required customer issues.

Reuses existing open tickets for the same issue, prevents duplicate tickets across
repeated turns in the same session, distinguishes customer claims from verified facts,
and generates customer-safe summaries and internal specialist notes.
"""

import copy
import logging
import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

try:
    from backend.ticket_service import create_ticket, list_tickets
except ImportError:
    from ticket_service import create_ticket, list_tickets

logger = logging.getLogger(__name__)


class TicketGenerationResult(BaseModel):
    """Validated output model produced by the Ticket Generation Agent."""

    ticket_id: Optional[str] = Field(
        default=None,
        description="Assigned unique support ticket ID (e.g. 'TKT-1A2B3C4D')",
    )
    session_id: str = Field(
        ...,
        description="Associated conversation session ID",
    )
    customer_id: Optional[str] = Field(
        default=None,
        description="Customer ID verified from official records, or None if unverified",
    )
    order_id: Optional[str] = Field(
        default=None,
        description="Associated verified order ID, or None if unverified/not found",
    )
    title: str = Field(
        ...,
        description="Concise, descriptive ticket title for support routing",
    )
    category: str = Field(
        ...,
        description="Support category / detected customer intent",
    )
    priority: str = Field(
        default="medium",
        description="Escalation priority: low, medium, high, urgent",
    )
    status: str = Field(
        default="open",
        description="Current ticket status: open, in_progress, resolved",
    )
    escalation_reason: str = Field(
        ...,
        description="Factual reason justifying escalation to human specialist",
    )
    target_team: str = Field(
        default="general_support",
        description="Target department (billing_support, logistics_support, technical_support, senior_support, general_support)",
    )
    customer_claims: List[str] = Field(
        default_factory=list,
        description="Customer-reported statements and unverified claims",
    )
    verified_facts: List[str] = Field(
        default_factory=list,
        description="Factual evidence verified directly against database records",
    )
    attempted_steps: List[str] = Field(
        default_factory=list,
        description="Automated troubleshooting or self-service actions already attempted",
    )
    knowledge_sources: List[str] = Field(
        default_factory=list,
        description="Knowledge base source article IDs consulted",
    )
    customer_safe_summary: str = Field(
        ...,
        description="Customer-safe explanation of ticket contents excluding internal reasoning",
    )
    internal_notes: str = Field(
        ...,
        description="Technical context and investigation notes for human support specialists",
    )
    is_reused: bool = Field(
        default=False,
        description="True if an existing open ticket was reused for the same unresolved issue",
    )
    generation_source: str = Field(
        default="deterministic_fallback",
        description="'gemini_assisted' or 'deterministic_fallback'",
    )
    ticket: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Complete stored ticket dictionary matching ticket_service schema",
    )


class LLMTicketSummaryOutput(BaseModel):
    """Structured output schema for optional LLM title and summary refinement."""

    title: str = Field(
        ...,
        description="Concise, professional headline for the ticket (e.g. '[Billing] Transaction Failed on Order ORD1004')",
    )
    customer_safe_summary: str = Field(
        ...,
        description="Clear, reassuring explanation for the customer without internal jargon",
    )
    internal_notes: str = Field(
        ...,
        description="Structured notes for support agent highlighting key problem, facts, and recommended human action",
    )


def extract_verified_order_id(investigation: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract order ID strictly when it is verified in system records."""
    if not investigation or not isinstance(investigation, dict):
        return None
    if investigation.get("status") == "found" and investigation.get("order_id"):
        return str(investigation["order_id"]).strip().upper()
    return None


def extract_verified_customer_id(
    investigation: Optional[Dict[str, Any]],
    customer_context: Optional[Dict[str, Any]],
) -> Optional[str]:
    """Extract customer ID strictly when verified from order records or authenticated context."""
    # First priority: verified order record
    if investigation and investigation.get("order"):
        cid = investigation["order"].get("customer_id")
        if cid:
            return str(cid).strip().upper()

    # Second priority: customer context if verified
    if customer_context and isinstance(customer_context, dict):
        if customer_context.get("verification_status") != "unverified_self_reported":
            cid = customer_context.get("customer_id")
            if cid:
                return str(cid).strip().upper()

    return None


def find_existing_ticket_for_same_issue(
    session_id: str,
    category: str,
    verified_order_id: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Check if an open or in-progress ticket already exists in this session for the same issue.

    Rules:
    - Same issue: matches category OR matches verified order ID.
    - Unrelated issue: different category AND different/missing order ID -> do NOT merge!
    """
    if not session_id:
        return None

    try:
        active_tickets = [
            t for t in list_tickets()
            if t.get("session_id") == session_id and t.get("status") in {"open", "in_progress"}
        ]
    except Exception as e:
        logger.warning("Failed to query existing tickets for reuse: %s", e)
        return None

    for t in active_tickets:
        # Check same category
        same_category = t.get("category") == category
        # Check same order ID
        same_order = verified_order_id and t.get("order_id") == verified_order_id
        if same_category or same_order:
            return copy.deepcopy(t)

    return None


def partition_claims_and_facts(
    message: str,
    investigation: Optional[Dict[str, Any]],
    customer_context: Optional[Dict[str, Any]],
    verified_order_id: Optional[str],
    verified_customer_id: Optional[str],
) -> tuple[List[str], List[str]]:
    """Partition customer claims from verified database facts."""
    customer_claims = [f"Customer stated: '{message}'"]
    verified_facts = []

    # Check claimed vs verified customer ID
    if customer_context:
        claimed_cid = customer_context.get("customer_id")
        if customer_context.get("verification_status") == "unverified_self_reported" and claimed_cid:
            customer_claims.append(f"Customer claimed customer ID '{claimed_cid}' (unverified).")
        elif verified_customer_id:
            verified_facts.append(f"Customer verified as '{verified_customer_id}' from database records.")

    # Check claimed vs verified order records
    inv = investigation or {}
    inv_status = inv.get("status")
    inv_order_id = inv.get("order_id")

    if inv_status == "found" and verified_order_id:
        order = inv.get("order") or {}
        order_status = order.get("status", "unknown")
        total_amount = order.get("total_amount", "N/A")
        verified_facts.append(f"Order '{verified_order_id}' verified in database: status='{order_status}', total=${total_amount}.")
        payments = inv.get("payments") or []
        verified_facts.append(f"Payment records: {len(payments)} transaction(s) recorded in database.")
    elif inv_status == "order_not_found" and inv_order_id:
        customer_claims.append(f"Customer reported issue for order ID '{inv_order_id}'.")
        verified_facts.append(f"Database lookup: Order ID '{inv_order_id}' was NOT found in orders database.")
    else:
        verified_facts.append("No active order was verified in system records for this inquiry.")

    return customer_claims, verified_facts


def gather_attempted_steps_and_sources(
    troubleshooting: Optional[Dict[str, Any]],
    knowledge_retrieval: Optional[Dict[str, Any]],
    knowledge_results: Optional[List[Dict[str, Any]]],
    action_execution: Optional[Dict[str, Any]],
) -> tuple[List[str], List[str]]:
    """Extract attempted self-service steps and consulted knowledge sources."""
    attempted_steps = []
    knowledge_sources = []

    # Knowledge sources consulted
    if knowledge_retrieval and knowledge_retrieval.get("sources"):
        knowledge_sources.extend(knowledge_retrieval["sources"])
    elif knowledge_results:
        for k in knowledge_results:
            if k.get("id"):
                knowledge_sources.append(k["id"])

    if knowledge_sources:
        attempted_steps.append(f"Automated knowledge retrieval consulted {len(knowledge_sources)} policy article(s): {', '.join(knowledge_sources)}.")

    # Troubleshooting steps attempted
    if troubleshooting:
        tb_steps = troubleshooting.get("recommended_steps") or []
        for s in tb_steps:
            attempted_steps.append(f"Diagnostic step: {s}")

    # Action execution attempts
    if action_execution:
        act_name = action_execution.get("action", "unknown")
        act_status = action_execution.get("status", "unknown")
        attempted_steps.append(f"Automated action execution attempted for '{act_name}': status was '{act_status}'.")

    if not attempted_steps:
        attempted_steps.append("Self-service automated evaluation completed prior to human escalation.")

    return attempted_steps, knowledge_sources


class TicketGenerationAgent:
    """Agent responsible for creating structured, deduplicated support escalation tickets."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        llm: Optional[Any] = None,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name or os.getenv("LLM_MODEL", "gemini-1.5-flash")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", str(temperature)))
        self._llm = llm
        self._structured_llm = None

    def _get_structured_llm(self) -> Optional[Any]:
        """Lazy-initialize structured output client if credentials are valid."""
        if self._llm is not None:
            try:
                from unittest.mock import Mock, MagicMock
                is_mock = isinstance(self._llm, (Mock, MagicMock))
            except ImportError:
                is_mock = False

            if not is_mock and hasattr(self._llm, "with_structured_output"):
                return self._llm.with_structured_output(LLMTicketSummaryOutput)
            return self._llm

        if not self.api_key or self.api_key.strip() in {"", "your_gemini_api_key_here"}:
            return None

        if self._structured_llm is None:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                chat_model = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=self.api_key,
                    temperature=self.temperature,
                )
                self._structured_llm = chat_model.with_structured_output(LLMTicketSummaryOutput)
            except Exception as e:
                logger.warning("Failed to initialize ChatGoogleGenerativeAI for ticket generation: %s", e)
                return None

        return self._structured_llm

    def generate_ticket(
        self,
        message: str,
        session_id: str,
        intent: Optional[str] = None,
        escalation: Optional[Dict[str, Any]] = None,
        escalation_reason: Optional[str] = None,
        priority: Optional[str] = None,
        target_team: Optional[str] = None,
        investigation: Optional[Dict[str, Any]] = None,
        customer_context: Optional[Dict[str, Any]] = None,
        troubleshooting: Optional[Dict[str, Any]] = None,
        knowledge_retrieval: Optional[Dict[str, Any]] = None,
        knowledge_results: Optional[List[Dict[str, Any]]] = None,
        action_execution: Optional[Dict[str, Any]] = None,
        memory: Optional[Dict[str, Any]] = None,
        force_create: bool = False,
    ) -> Optional[TicketGenerationResult]:
        """Generate or reuse a structured support ticket.

        Returns None if the issue is a normal inquiry not requiring escalation.
        """
        clean_msg = (message or "").strip()
        clean_sid = (session_id or "").strip() or "anonymous"
        clean_intent = (intent or "general_inquiry").strip()

        # STEP 1: Verify ticket creation necessity
        # Tickets are created ONLY when escalation or human review is required, or force_create=True
        esc = escalation or {}
        should_escalate = esc.get("should_escalate", False) or bool(escalation_reason)
        requires_human = esc.get("requires_human_review", False)

        if not (should_escalate or requires_human or force_create):
            # Ordinary question: do not create ticket
            return None

        # STEP 2: Extract factual metadata
        category = esc.get("category") or clean_intent
        priority = priority or esc.get("priority") or "medium"
        target_team = target_team or esc.get("target_team") or "general_support"
        escalation_reason = (
            escalation_reason
            or esc.get("escalation_reason")
            or "Customer issue referred for human support review."
        )

        verified_order_id = extract_verified_order_id(investigation)
        verified_customer_id = extract_verified_customer_id(investigation, customer_context)

        # STEP 3: Partition customer claims from verified database facts
        customer_claims, verified_facts = partition_claims_and_facts(
            message=clean_msg,
            investigation=investigation,
            customer_context=customer_context,
            verified_order_id=verified_order_id,
            verified_customer_id=verified_customer_id,
        )

        attempted_steps, knowledge_sources = gather_attempted_steps_and_sources(
            troubleshooting=troubleshooting,
            knowledge_retrieval=knowledge_retrieval,
            knowledge_results=knowledge_results,
            action_execution=action_execution,
        )

        # STEP 4: Check for ticket reuse in same session (Duplicate prevention)
        existing_ticket = find_existing_ticket_for_same_issue(
            session_id=clean_sid,
            category=category,
            verified_order_id=verified_order_id,
        )

        if existing_ticket:
            # Reusing existing open ticket for the same issue
            tid = existing_ticket.get("ticket_id")
            existing_ticket["is_reused"] = True

            customer_safe_summary = (
                f"Your ongoing support ticket ({tid}) regarding {category.replace('_', ' ')} "
                f"is active and being reviewed by our {target_team.replace('_', ' ')}."
            )

            return TicketGenerationResult(
                ticket_id=tid,
                session_id=clean_sid,
                customer_id=verified_customer_id,
                order_id=verified_order_id,
                title=existing_ticket.get("title") or f"[{category.replace('_', ' ').title()}] Support Request",
                category=category,
                priority=existing_ticket.get("priority") or priority,
                status=existing_ticket.get("status") or "open",
                escalation_reason=existing_ticket.get("escalation_reason") or escalation_reason,
                target_team=existing_ticket.get("target_team") or target_team,
                customer_claims=customer_claims,
                verified_facts=verified_facts,
                attempted_steps=attempted_steps,
                knowledge_sources=knowledge_sources,
                customer_safe_summary=customer_safe_summary,
                internal_notes=(
                    f"Reused active ticket {tid} for follow-up message in session {clean_sid}. "
                    f"Customer stated: '{clean_msg}'."
                ),
                is_reused=True,
                generation_source="deterministic_fallback",
                ticket=existing_ticket,
            )

        # STEP 5: Generate Title, Customer Safe Summary, and Internal Notes
        # Attempt Gemini LLM refinement if available
        title = None
        customer_safe_summary = None
        internal_notes = None
        generation_source = "deterministic_fallback"

        structured_llm = self._get_structured_llm()
        if structured_llm is not None and clean_msg:
            try:
                system_prompt = (
                    "You are the Support Ticket Specialist for an e-commerce platform.\n"
                    "Your role is to generate a concise, professional ticket title, customer-safe summary,\n"
                    "and internal specialist notes for an escalated case.\n\n"
                    "STRICT GROUNDING RULES:\n"
                    "1. NEVER invent non-existent order numbers, payment amounts, or customer names.\n"
                    "2. Ground your output strictly in the provided verified facts and category.\n"
                    "3. Customer-safe summary must be polite and clear, without internal system details.\n"
                    "4. Internal notes should highlight the core customer issue and verified records."
                )

                user_content = (
                    f"Category: {category}\n"
                    f"Priority: {priority}\n"
                    f"Target Team: {target_team}\n"
                    f"Customer Message: {clean_msg}\n"
                    f"Escalation Reason: {escalation_reason}\n"
                    f"Verified Order ID: {verified_order_id or 'None'}\n"
                    f"Verified Facts: {'; '.join(verified_facts)}\n"
                )

                llm_response = structured_llm.invoke(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ]
                )

                if isinstance(llm_response, LLMTicketSummaryOutput):
                    parsed_llm = llm_response
                elif isinstance(llm_response, dict):
                    parsed_llm = LLMTicketSummaryOutput(**llm_response)
                else:
                    parsed_llm = None

                if parsed_llm:
                    title = parsed_llm.title
                    customer_safe_summary = parsed_llm.customer_safe_summary
                    internal_notes = parsed_llm.internal_notes
                    generation_source = "gemini_assisted"

            except Exception as e:
                logger.warning("Gemini ticket title generation failed (%s), using deterministic fallback.", e)

        # Deterministic generation fallback
        if not title:
            if verified_order_id:
                title = f"[{category.replace('_', ' ').title()}] Issue regarding Order {verified_order_id}"
            elif escalation_reason:
                title = f"[{category.replace('_', ' ').title()}] {escalation_reason}"
            else:
                title = f"[{category.replace('_', ' ').title()}] Human Escalation Request"

        if not customer_safe_summary:
            order_clause = f" for order {verified_order_id}" if verified_order_id else ""
            customer_safe_summary = (
                f"Your request regarding {category.replace('_', ' ')}{order_clause} has been escalated to our "
                f"{target_team.replace('_', ' ')}. A customer support specialist will review your details and follow up."
            )

        if not internal_notes:
            inv_summary = (investigation or {}).get("summary", "No investigation records.")
            tb_diag = (troubleshooting or {}).get("diagnosis", "No troubleshooting diagnosis.")
            internal_notes = (
                f"Escalated issue: {clean_msg}\n"
                f"Reason: {escalation_reason}\n"
                f"Investigation: {inv_summary}\n"
                f"Diagnosis: {tb_diag}\n"
                f"Verified facts: {'; '.join(verified_facts)}"
            )

        # STEP 6: Create the new ticket in ticket_service
        inv_summary = (investigation or {}).get("summary")
        created_ticket = create_ticket(
            session_id=clean_sid,
            original_message=clean_msg,
            category=category,
            escalation_reason=escalation_reason,
            customer_id=verified_customer_id,
            priority=priority,
            status="open",
            investigation_summary=inv_summary,
            title=title,
            target_team=target_team,
            order_id=verified_order_id,
            customer_safe_summary=customer_safe_summary,
            is_reused=False,
        )

        return TicketGenerationResult(
            ticket_id=created_ticket["ticket_id"],
            session_id=clean_sid,
            customer_id=verified_customer_id,
            order_id=verified_order_id,
            title=title,
            category=category,
            priority=priority,
            status="open",
            escalation_reason=escalation_reason,
            target_team=target_team,
            customer_claims=customer_claims,
            verified_facts=verified_facts,
            attempted_steps=attempted_steps,
            knowledge_sources=knowledge_sources,
            customer_safe_summary=customer_safe_summary,
            internal_notes=internal_notes,
            is_reused=False,
            generation_source=generation_source,
            ticket=created_ticket,
        )


# Global singleton instance
_TICKET_GENERATION_AGENT = TicketGenerationAgent()


def generate_support_ticket(
    message: str,
    session_id: str,
    intent: Optional[str] = None,
    escalation: Optional[Dict[str, Any]] = None,
    escalation_reason: Optional[str] = None,
    priority: Optional[str] = None,
    target_team: Optional[str] = None,
    investigation: Optional[Dict[str, Any]] = None,
    customer_context: Optional[Dict[str, Any]] = None,
    troubleshooting: Optional[Dict[str, Any]] = None,
    knowledge_retrieval: Optional[Dict[str, Any]] = None,
    knowledge_results: Optional[List[Dict[str, Any]]] = None,
    action_execution: Optional[Dict[str, Any]] = None,
    memory: Optional[Dict[str, Any]] = None,
    force_create: bool = False,
) -> Optional[TicketGenerationResult]:
    """Convenience helper to generate or reuse a support ticket via the TicketGenerationAgent."""
    return _TICKET_GENERATION_AGENT.generate_ticket(
        message=message,
        session_id=session_id,
        intent=intent,
        escalation=escalation,
        escalation_reason=escalation_reason,
        priority=priority,
        target_team=target_team,
        investigation=investigation,
        customer_context=customer_context,
        troubleshooting=troubleshooting,
        knowledge_retrieval=knowledge_retrieval,
        knowledge_results=knowledge_results,
        action_execution=action_execution,
        memory=memory,
        force_create=force_create,
    )
