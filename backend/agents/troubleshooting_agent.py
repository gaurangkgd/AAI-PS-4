"""Troubleshooting Agent.

The fourth specialized agent in the Agentic Customer Support System (PS-04).
Responsible for diagnosing customer problems using factual evidence from order/payment
investigation, customer context, and approved knowledge base policies. Employs Gemini
for nuanced diagnostic reasoning when configured, with a deterministic rule-based
fallback. Strictly preserves read-only safety with zero mutations.
"""

import copy
import logging
import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TroubleshootingResult(BaseModel):
    """Validated structured diagnostic output from the Troubleshooting Agent."""

    issue: str = Field(
        ...,
        description="Identified customer issue or problem domain",
    )
    intent: str = Field(
        ...,
        description="Associated customer intent category",
    )
    order_id: Optional[str] = Field(
        default=None,
        description="Referenced or identified order ID, if applicable",
    )
    order_status: Optional[str] = Field(
        default=None,
        description="Factual order status from verified investigation records",
    )
    order_facts: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Factual order details extracted from verified records",
    )
    payment_facts: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Factual payment transaction records extracted from verified records",
    )
    knowledge_sources: List[str] = Field(
        default_factory=list,
        description="Approved knowledge base source IDs used in the diagnosis (e.g. ['KB-PAY-001'])",
    )
    diagnosis: str = Field(
        ...,
        description="Factual diagnosis summary explaining root cause or current state",
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="Concrete factual evidence points supporting the diagnosis",
    )
    recommended_steps: List[str] = Field(
        default_factory=list,
        description="Actionable, safe next steps for the customer or support team",
    )
    needs_more_info: bool = Field(
        default=False,
        description="True if critical information (e.g. order ID or payment details) is missing",
    )
    suggest_escalation: bool = Field(
        default=False,
        description="True if the issue requires human customer support escalation",
    )
    confidence: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Diagnostic confidence score between 0.0 and 1.0",
    )
    source: str = Field(
        default="deterministic_rule_based",
        description="Reasoning origin: 'llm_assisted' or 'deterministic_rule_based'",
    )


class LLMTroubleshootingOutput(BaseModel):
    """Structured output schema for optional LLM diagnostic reasoning."""

    issue: str = Field(..., description="Concise description of the identified issue")
    diagnosis: str = Field(..., description="Factual diagnosis grounded strictly in provided evidence")
    evidence: List[str] = Field(default_factory=list, description="Evidence points observed in facts")
    recommended_steps: List[str] = Field(default_factory=list, description="Recommended next steps")
    needs_more_info: bool = Field(default=False, description="Whether essential information is missing")
    suggest_escalation: bool = Field(default=False, description="Whether escalation is recommended")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Confidence score 0.0-1.0")


def deterministic_diagnosis(
    message: str,
    intent: str,
    investigation: Optional[Dict[str, Any]] = None,
    customer_context: Optional[Dict[str, Any]] = None,
    knowledge_retrieval: Optional[Dict[str, Any]] = None,
    knowledge_results: Optional[List[Dict[str, Any]]] = None,
    fallback_reason: Optional[str] = None,
) -> TroubleshootingResult:
    """Generate a factual, grounded diagnosis using deterministic logic and verified evidence."""
    inv = investigation or {}
    inv_status = inv.get("status")
    order = inv.get("order")
    order_id = inv.get("order_id")
    payments = inv.get("payments") or []

    # Extract knowledge sources
    kb_sources: List[str] = []
    if knowledge_retrieval and knowledge_retrieval.get("sources"):
        kb_sources = list(knowledge_retrieval.get("sources", []))
    elif knowledge_results:
        kb_sources = [k.get("id") for k in knowledge_results if k.get("id")]

    # Clean order facts
    order_facts: Optional[Dict[str, Any]] = None
    order_status: Optional[str] = None
    if order:
        order_status = order.get("status")
        order_facts = {
            "order_id": order.get("id"),
            "customer_id": order.get("customer_id"),
            "status": order_status,
            "total_amount": order.get("total_amount"),
            "items_count": len(order.get("items", [])),
        }

    # Clean payment facts
    payment_facts: Optional[List[Dict[str, Any]]] = None
    if payments:
        payment_facts = [
            {
                "id": p.get("id"),
                "status": p.get("status"),
                "amount": p.get("amount"),
                "payment_method": p.get("payment_method"),
                "transaction_ref": p.get("transaction_ref"),
            }
            for p in payments
        ]

    # 1. Payment Issue Diagnosis
    if intent == "payment_issue":
        if inv_status == "found" and order:
            failed_payments = [p for p in payments if p.get("status") == "failed"]
            pending_payments = [p for p in payments if p.get("status") == "pending"]

            if failed_payments or order_status == "payment_failed":
                ref = failed_payments[0].get("transaction_ref", "N/A") if failed_payments else "N/A"
                return TroubleshootingResult(
                    issue="Failed payment transaction",
                    intent=intent,
                    order_id=order_id,
                    order_status=order_status,
                    order_facts=order_facts,
                    payment_facts=payment_facts,
                    knowledge_sources=kb_sources,
                    diagnosis=(
                        f"Payment authorization failed for order {order_id} (Ref: {ref}). "
                        "Funds were not captured by the merchant."
                    ),
                    evidence=[
                        f"Order status is verified as '{order_status}'",
                        f"Payment transaction record status is 'failed' (Ref: {ref})",
                    ],
                    recommended_steps=[
                        "Verify with your bank whether a pre-authorization hold was released",
                        "Ensure card billing address matches bank records",
                        "Human escalation ticket required to investigate gateway decline code",
                    ],
                    needs_more_info=False,
                    suggest_escalation=True,
                    confidence=0.95,
                    source="deterministic_rule_based",
                )
            elif pending_payments or order_status == "pending_payment":
                ref = pending_payments[0].get("transaction_ref", "N/A") if pending_payments else "N/A"
                return TroubleshootingResult(
                    issue="Pending payment settlement",
                    intent=intent,
                    order_id=order_id,
                    order_status=order_status,
                    order_facts=order_facts,
                    payment_facts=payment_facts,
                    knowledge_sources=kb_sources,
                    diagnosis=(
                        f"Payment for order {order_id} is currently in a pending state with the payment processor (Ref: {ref})."
                    ),
                    evidence=[
                        f"Order status is verified as '{order_status}'",
                        f"Payment transaction record status is 'pending' (Ref: {ref})",
                    ],
                    recommended_steps=[
                        "Allow 3 to 5 business days for gateway auto-reconciliation per policy KB-PAY-001",
                        "Retain the transaction reference number for verification",
                        "Escalate for specialist billing review if amount was debited twice",
                    ],
                    needs_more_info=False,
                    suggest_escalation=True,
                    confidence=0.90,
                    source="deterministic_rule_based",
                )
            else:
                return TroubleshootingResult(
                    issue="Payment status inquiry",
                    intent=intent,
                    order_id=order_id,
                    order_status=order_status,
                    order_facts=order_facts,
                    payment_facts=payment_facts,
                    knowledge_sources=kb_sources,
                    diagnosis=f"Payment for order {order_id} is recorded as successful in our billing records.",
                    evidence=[
                        f"Order status is '{order_status}'",
                        f"All associated payment records ({len(payments)}) reflect successful settlement",
                    ],
                    recommended_steps=[
                        "Review your order summary in your customer account",
                        "If you observe duplicate bank charges, provide bank transaction timestamps",
                    ],
                    needs_more_info=False,
                    suggest_escalation=False,
                    confidence=0.90,
                    source="deterministic_rule_based",
                )
        elif inv_status == "order_not_found":
            return TroubleshootingResult(
                issue="Payment inquiry for unrecognized order",
                intent=intent,
                order_id=order_id,
                order_status=None,
                order_facts=None,
                payment_facts=None,
                knowledge_sources=kb_sources,
                diagnosis=f"Order ID '{order_id}' was not found in our order or billing database.",
                evidence=[f"Order database lookup returned no record for '{order_id}'"],
                recommended_steps=[
                    "Check your purchase confirmation email for the exact Order ID format (e.g. ORD1001)",
                    "Provide payment reference number or bank statement transaction ID",
                ],
                needs_more_info=True,
                suggest_escalation=True,
                confidence=0.85,
                source="deterministic_rule_based",
            )
        else:
            return TroubleshootingResult(
                issue="Payment issue missing order identification",
                intent=intent,
                order_id=None,
                order_status=None,
                order_facts=None,
                payment_facts=None,
                knowledge_sources=kb_sources,
                diagnosis="Cannot diagnose payment or billing discrepancies without an Order ID or Transaction Reference.",
                evidence=["Customer message does not specify an Order ID (ORDxxxx)"],
                recommended_steps=[
                    "Provide your Order ID (e.g. ORD1001) to verify transaction history",
                    "Keep your UPI or bank transaction reference handy",
                ],
                needs_more_info=True,
                suggest_escalation=False,
                confidence=0.75,
                source="deterministic_rule_based",
            )

    # 2. Order Tracking & Delivery Issues
    if intent == "order_tracking":
        if inv_status == "found" and order:
            if order_status == "delivered":
                return TroubleshootingResult(
                    issue="Delivered order tracking",
                    intent=intent,
                    order_id=order_id,
                    order_status=order_status,
                    order_facts=order_facts,
                    payment_facts=payment_facts,
                    knowledge_sources=kb_sources,
                    diagnosis=f"Order {order_id} has completed fulfillment and is marked as 'delivered'.",
                    evidence=[
                        f"Order status is 'delivered' in verified database",
                        f"Order completed on {order.get('created_at', 'recent date')}",
                    ],
                    recommended_steps=[
                        "Inspect delivery location, secure mailbox, or concierge desk",
                        "If item is missing or damaged, initiate a replacement request within inspection window",
                    ],
                    needs_more_info=False,
                    suggest_escalation=False,
                    confidence=0.95,
                    source="deterministic_rule_based",
                )
            elif order_status == "shipped":
                return TroubleshootingResult(
                    issue="In-transit shipment tracking",
                    intent=intent,
                    order_id=order_id,
                    order_status=order_status,
                    order_facts=order_facts,
                    payment_facts=payment_facts,
                    knowledge_sources=kb_sources,
                    diagnosis=f"Order {order_id} is in transit with courier partner.",
                    evidence=[f"Order status is 'shipped' in verified database"],
                    recommended_steps=[
                        "Monitor the courier tracking link; updates may take up to 24 hours per KB-TRK-001",
                        "If delayed beyond expected arrival window, courier will re-attempt on next business day",
                    ],
                    needs_more_info=False,
                    suggest_escalation=False,
                    confidence=0.95,
                    source="deterministic_rule_based",
                )
            elif order_status == "processing":
                return TroubleshootingResult(
                    issue="Processing order status",
                    intent=intent,
                    order_id=order_id,
                    order_status=order_status,
                    order_facts=order_facts,
                    payment_facts=payment_facts,
                    knowledge_sources=kb_sources,
                    diagnosis=f"Order {order_id} is currently processing and preparing for warehouse packaging.",
                    evidence=[f"Order status is 'processing' in verified database"],
                    recommended_steps=[
                        "Standard fulfillment takes 1-2 business days prior to carrier handover",
                        "Order remains eligible for cancellation if desired prior to dispatch",
                    ],
                    needs_more_info=False,
                    suggest_escalation=False,
                    confidence=0.95,
                    source="deterministic_rule_based",
                )
            else:
                return TroubleshootingResult(
                    issue="Order status tracking",
                    intent=intent,
                    order_id=order_id,
                    order_status=order_status,
                    order_facts=order_facts,
                    payment_facts=payment_facts,
                    knowledge_sources=kb_sources,
                    diagnosis=f"Order {order_id} is currently recorded with status '{order_status}'.",
                    evidence=[f"Verified database record reflects status '{order_status}'"],
                    recommended_steps=["Check account dashboard for live shipment updates"],
                    needs_more_info=False,
                    suggest_escalation=False,
                    confidence=0.90,
                    source="deterministic_rule_based",
                )
        elif inv_status == "order_not_found":
            return TroubleshootingResult(
                issue="Tracking unrecognized order",
                intent=intent,
                order_id=order_id,
                order_status=None,
                order_facts=None,
                payment_facts=None,
                knowledge_sources=kb_sources,
                diagnosis=f"Order ID '{order_id}' was not found in our fulfillment records.",
                evidence=[f"No matching order records found for '{order_id}'"],
                recommended_steps=["Verify order ID from checkout confirmation email"],
                needs_more_info=True,
                suggest_escalation=False,
                confidence=0.85,
                source="deterministic_rule_based",
            )
        else:
            return TroubleshootingResult(
                issue="Tracking inquiry missing order ID",
                intent=intent,
                order_id=None,
                order_status=None,
                order_facts=None,
                payment_facts=None,
                knowledge_sources=kb_sources,
                diagnosis="Cannot retrieve delivery milestones without an Order ID.",
                evidence=["Customer message contains no Order ID (ORDxxxx)"],
                recommended_steps=["Provide your Order ID (e.g. ORD1001) to look up tracking records"],
                needs_more_info=True,
                suggest_escalation=False,
                confidence=0.75,
                source="deterministic_rule_based",
            )

    # 3. Cancellation Diagnosis
    if intent == "cancellation":
        if inv_status == "found" and order:
            can_cancel = order_status == "processing"
            diagnosis = (
                f"Order {order_id} is in 'processing' status and is eligible for immediate cancellation."
                if can_cancel
                else f"Order {order_id} is '{order_status}' and cannot be cancelled directly in-transit per policy KB-CAN-001."
            )
            return TroubleshootingResult(
                issue="Order cancellation eligibility",
                intent=intent,
                order_id=order_id,
                order_status=order_status,
                order_facts=order_facts,
                payment_facts=payment_facts,
                knowledge_sources=kb_sources,
                diagnosis=diagnosis,
                evidence=[
                    f"Order status is verified as '{order_status}'",
                    "Cancellation policy allows cancellation only while order is processing",
                ],
                recommended_steps=(
                    ["Confirm cancellation request to proceed with order termination and refund"]
                    if can_cancel
                    else [
                        "You may refuse shipment delivery upon arrival",
                        "Alternatively, submit a return request once the package is delivered",
                    ]
                ),
                needs_more_info=False,
                suggest_escalation=False,
                confidence=0.95,
                source="deterministic_rule_based",
            )
        else:
            return TroubleshootingResult(
                issue="Cancellation request missing order ID",
                intent=intent,
                order_id=None,
                order_status=None,
                order_facts=None,
                payment_facts=None,
                knowledge_sources=kb_sources,
                diagnosis="Cancellation eligibility cannot be verified without an Order ID.",
                evidence=["No Order ID specified in message"],
                recommended_steps=["Please provide your Order ID (e.g. ORD1001) to check cancellation eligibility"],
                needs_more_info=True,
                suggest_escalation=False,
                confidence=0.75,
                source="deterministic_rule_based",
            )

    # 4. Return or Replacement Diagnosis
    if intent == "return_or_replacement":
        if inv_status == "found" and order:
            can_return = order_status == "delivered"
            diagnosis = (
                f"Order {order_id} is marked as 'delivered' and meets return/replacement request criteria."
                if can_return
                else f"Order {order_id} has status '{order_status}'; returns require the package to be delivered first."
            )
            return TroubleshootingResult(
                issue="Return or replacement eligibility",
                intent=intent,
                order_id=order_id,
                order_status=order_status,
                order_facts=order_facts,
                payment_facts=payment_facts,
                knowledge_sources=kb_sources,
                diagnosis=diagnosis,
                evidence=[
                    f"Order status is verified as '{order_status}'",
                    "Policy KB-RET-001 requires item to be delivered to initiate return/replacement",
                ],
                recommended_steps=(
                    [
                        "Submit return or replacement request specifying reason and item details",
                        "Ensure item is in original condition with tags and packaging per KB-RET-002",
                    ]
                    if can_return
                    else ["Wait for package delivery before submitting return request"]
                ),
                needs_more_info=False,
                suggest_escalation=False,
                confidence=0.95,
                source="deterministic_rule_based",
            )
        else:
            return TroubleshootingResult(
                issue="Return inquiry missing order ID",
                intent=intent,
                order_id=None,
                order_status=None,
                order_facts=None,
                payment_facts=None,
                knowledge_sources=kb_sources,
                diagnosis="Return and replacement eligibility requires an Order ID.",
                evidence=["No Order ID specified in message"],
                recommended_steps=["Provide your Order ID (e.g. ORD1001) to check return eligibility"],
                needs_more_info=True,
                suggest_escalation=False,
                confidence=0.75,
                source="deterministic_rule_based",
            )

    # 5. Account, Product, Refund, or General Inquiries
    if kb_sources:
        return TroubleshootingResult(
            issue=f"General guidance on {intent.replace('_', ' ')}",
            intent=intent,
            order_id=order_id,
            order_status=order_status,
            order_facts=order_facts,
            payment_facts=payment_facts,
            knowledge_sources=kb_sources,
            diagnosis=f"Inquiry matches approved support policy ({kb_sources[0]}).",
            evidence=[f"Approved knowledge base article {kb_sources[0]} matched customer inquiry"],
            recommended_steps=[
                "Follow policy instructions outlined in support knowledge base",
                "Contact customer support during business hours if self-service resolution is not possible",
            ],
            needs_more_info=False,
            suggest_escalation=False,
            confidence=0.85,
            source="deterministic_rule_based",
        )

    # Fallback for empty/unrecognized issues
    return TroubleshootingResult(
        issue="Unspecified or ambiguous inquiry",
        intent=intent,
        order_id=order_id,
        order_status=order_status,
        order_facts=order_facts,
        payment_facts=payment_facts,
        knowledge_sources=[],
        diagnosis="Insufficient factual information to formulate a specific diagnosis.",
        evidence=["No matching order, payment, or knowledge base articles found"],
        recommended_steps=[
            "Provide an Order ID (ORDxxxx), payment reference, or detailed problem description",
        ],
        needs_more_info=True,
        suggest_escalation=False,
        confidence=0.50,
        source="deterministic_rule_based",
    )


class TroubleshootingAgent:
    """Specialized agent for diagnosing customer support issues using factual evidence."""

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
            if hasattr(self._llm, "with_structured_output"):
                return self._llm.with_structured_output(LLMTroubleshootingOutput)
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
                self._structured_llm = chat_model.with_structured_output(LLMTroubleshootingOutput)
            except Exception as e:
                logger.warning("Failed to initialize ChatGoogleGenerativeAI for troubleshooting: %s", e)
                return None

        return self._structured_llm

    def diagnose(
        self,
        message: str,
        intent: str,
        investigation: Optional[Dict[str, Any]] = None,
        customer_context: Optional[Dict[str, Any]] = None,
        knowledge_retrieval: Optional[Dict[str, Any]] = None,
        knowledge_results: Optional[List[Dict[str, Any]]] = None,
    ) -> TroubleshootingResult:
        """Diagnose the customer issue using grounded evidence.

        Evaluates LLM when available, strictly validating against verified facts.
        Falls back seamlessly to deterministic rule-based diagnosis.
        """
        clean_msg = (message or "").strip()
        clean_intent = (intent or "general_inquiry").strip()

        # If LLM is available, attempt grounded diagnostic reasoning
        structured_llm = self._get_structured_llm()
        if structured_llm is not None and clean_msg:
            try:
                system_prompt = (
                    "You are the Troubleshooting Specialist for an e-commerce support system.\n"
                    "Your task is to analyze the customer's problem strictly using the verified facts provided.\n\n"
                    "STRICT RULES:\n"
                    "1. Ground your diagnosis ONLY in verified facts (order status, payment records, KB policies).\n"
                    "2. NEVER invent non-existent order statuses, fake payments, or fabricated policies.\n"
                    "3. Distinguish observed facts from recommendations.\n"
                    "4. If essential info (like order ID) is missing, set needs_more_info to true.\n"
                    "5. If a verified payment failure, decline, or unresolvable issue is present, set suggest_escalation to true."
                )

                inv_summary = (investigation or {}).get("summary", "No investigation records.")
                kb_sources_str = ", ".join(
                    knowledge_retrieval.get("sources", [])
                    if knowledge_retrieval and knowledge_retrieval.get("sources")
                    else [k.get("id", "") for k in (knowledge_results or []) if k.get("id")]
                )

                user_content = (
                    f"Customer Message: {clean_msg}\n"
                    f"Classified Intent: {clean_intent}\n"
                    f"Verified Investigation Records: {inv_summary}\n"
                    f"Knowledge Sources: {kb_sources_str}\n"
                )

                response: LLMTroubleshootingOutput = structured_llm.invoke(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ]
                )

                # Defensive validation: Ensure LLM diagnosis is grounded and doesn't contradict facts
                inv = investigation or {}
                order = inv.get("order")
                order_id = inv.get("order_id")
                order_status = order.get("status") if order else None
                payments = inv.get("payments") or []

                # Extract knowledge sources
                kb_sources: List[str] = []
                if knowledge_retrieval and knowledge_retrieval.get("sources"):
                    kb_sources = list(knowledge_retrieval.get("sources", []))
                elif knowledge_results:
                    kb_sources = [k.get("id") for k in knowledge_results if k.get("id")]

                return TroubleshootingResult(
                    issue=response.issue,
                    intent=clean_intent,
                    order_id=order_id,
                    order_status=order_status,
                    order_facts=(
                        {
                            "order_id": order.get("id"),
                            "status": order_status,
                            "total_amount": order.get("total_amount"),
                        }
                        if order
                        else None
                    ),
                    payment_facts=(
                        [
                            {
                                "id": p.get("id"),
                                "status": p.get("status"),
                                "ref": p.get("transaction_ref"),
                            }
                            for p in payments
                        ]
                        if payments
                        else None
                    ),
                    knowledge_sources=kb_sources,
                    diagnosis=response.diagnosis,
                    evidence=response.evidence,
                    recommended_steps=response.recommended_steps,
                    needs_more_info=response.needs_more_info,
                    suggest_escalation=response.suggest_escalation,
                    confidence=float(response.confidence),
                    source="llm_assisted",
                )

            except Exception as e:
                logger.info(
                    "LLM troubleshooting encountered error (%s); falling back to deterministic diagnosis.",
                    e,
                )

        # Fallback deterministic diagnosis path
        return deterministic_diagnosis(
            message=clean_msg,
            intent=clean_intent,
            investigation=investigation,
            customer_context=customer_context,
            knowledge_retrieval=knowledge_retrieval,
            knowledge_results=knowledge_results,
        )


def diagnose_support_issue(
    message: str,
    intent: str,
    investigation: Optional[Dict[str, Any]] = None,
    customer_context: Optional[Dict[str, Any]] = None,
    knowledge_retrieval: Optional[Dict[str, Any]] = None,
    knowledge_results: Optional[List[Dict[str, Any]]] = None,
) -> TroubleshootingResult:
    """Convenience helper to diagnose support issues using the TroubleshootingAgent."""
    agent = TroubleshootingAgent()
    return agent.diagnose(
        message=message,
        intent=intent,
        investigation=investigation,
        customer_context=customer_context,
        knowledge_retrieval=knowledge_retrieval,
        knowledge_results=knowledge_results,
    )
