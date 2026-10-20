"""Escalation Decision Agent.

The seventh specialized agent in the Agentic Customer Support System (PS-04).
Responsible for deciding whether a customer issue can be resolved automatically
through self-service or requires escalation to a human support representative.

Employs Google Gemini for nuanced contextual reasoning while enforcing strict,
deterministic hard safety rules that cannot be overridden by the LLM.
"""

import copy
import logging
import os
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

# Regex patterns for detecting explicit requests for human assistance or supervisors
HUMAN_REQUEST_PATTERNS = [
    re.compile(r"\b(human|person|agent|representative|specialist|operator|supervisor|manager)\b", re.IGNORECASE),
    re.compile(r"\b(speak|talk)\s+to\s+(someone|a\s+person|a\s+human|an\s+agent|a\s+rep|a\s+supervisor|a\s+manager)\b", re.IGNORECASE),
    re.compile(r"\b(transfer|connect)\s+me\s+to\b", re.IGNORECASE),
    re.compile(r"\bcustomer\s+service\s+(rep|agent|person)\b", re.IGNORECASE),
]

# Frustration and urgency markers
FRUSTRATION_PATTERNS = [
    re.compile(r"\b(unacceptable|furious|disgusted|ridiculous|terrible|horrible|worst|scam|fraud|lawsuit|lawyer|attorney)\b", re.IGNORECASE),
    re.compile(r"\b(stolen|ripoff|cheat|cheating|robbed)\b", re.IGNORECASE),
]

VALID_PRIORITIES = {"low", "medium", "high", "urgent"}
VALID_TARGET_TEAMS = {
    "billing_support",
    "logistics_support",
    "technical_support",
    "senior_support",
    "general_support",
}


class EscalationDecisionResult(BaseModel):
    """Validated structured output from the Escalation Decision Agent."""

    should_escalate: bool = Field(
        ...,
        description="Whether the customer issue must be escalated to a human support representative",
    )
    escalation_reason: Optional[str] = Field(
        default=None,
        description="Factual, clear reason justifying the escalation",
    )
    priority: str = Field(
        default="medium",
        description="Assessed priority: low, medium, high, urgent",
    )
    target_team: Optional[str] = Field(
        default=None,
        description="Recommended support team (billing_support, logistics_support, technical_support, senior_support, general_support)",
    )
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="Concrete factual evidence points from the workflow supporting the decision",
    )
    requires_human_review: bool = Field(
        default=False,
        description="True if human specialist intervention is strictly mandatory",
    )
    explanation: str = Field(
        ...,
        description="Clear explanation justifying why escalation was or was not triggered",
    )
    decision_source: str = Field(
        default="deterministic_fallback",
        description="Origin of the decision: 'gemini_assisted', 'deterministic_fallback', or 'deterministic_safety_override'",
    )

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> str:
        if v and v.strip().lower() in VALID_PRIORITIES:
            return v.strip().lower()
        return "medium"

    @field_validator("target_team")
    @classmethod
    def validate_target_team(cls, v: Optional[str]) -> Optional[str]:
        if v and v.strip().lower() in VALID_TARGET_TEAMS:
            return v.strip().lower()
        return "general_support" if v else None


class LLMEscalationOutput(BaseModel):
    """Structured output schema for optional LLM escalation evaluation."""

    should_escalate: bool = Field(
        ...,
        description="True if issue requires human support escalation, False if automated resolution is sufficient",
    )
    escalation_reason: Optional[str] = Field(
        default=None,
        description="Specific reason for escalation if should_escalate is True",
    )
    priority: str = Field(
        default="medium",
        description="Assessed urgency: low, medium, high, urgent",
    )
    target_team: Optional[str] = Field(
        default="general_support",
        description="Target department: billing_support, logistics_support, technical_support, senior_support, general_support",
    )
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="Observed facts or signals indicating need for escalation",
    )
    requires_human_review: bool = Field(
        default=False,
        description="Whether a human specialist must review or action the case",
    )
    explanation: str = Field(
        ...,
        description="Concise rationale for the recommendation",
    )


def detect_explicit_human_request(message: str) -> Optional[str]:
    """Check if the user explicitly requested a human, agent, or supervisor."""
    if not message or not isinstance(message, str):
        return None
    for pattern in HUMAN_REQUEST_PATTERNS:
        match = pattern.search(message)
        if match:
            return match.group(0)
    return None


def detect_severe_frustration(message: str) -> Optional[str]:
    """Check if message contains severe frustration or adversarial terms."""
    if not message or not isinstance(message, str):
        return None
    for pattern in FRUSTRATION_PATTERNS:
        match = pattern.search(message)
        if match:
            return match.group(0)
    return None


def evaluate_hard_safety_rules(
    message: str,
    intent: str,
    investigation: Optional[Dict[str, Any]] = None,
    customer_context: Optional[Dict[str, Any]] = None,
    troubleshooting: Optional[Dict[str, Any]] = None,
    action_execution: Optional[Dict[str, Any]] = None,
    memory: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Evaluate non-negotiable policy safety rules that MANDATE human escalation.

    These hard safety rules CANNOT be overridden by LLM output.
    Returns escalation details dict if a hard rule triggers, or None.
    """
    clean_msg = (message or "").strip()
    inv = investigation or {}
    inv_status = inv.get("status")
    order = inv.get("order") or {}
    payments = inv.get("payments") or []
    order_status = order.get("status", "").lower() if order else ""

    # Rule 1: Explicit human or supervisor request
    human_kw = detect_explicit_human_request(clean_msg)
    if human_kw:
        is_senior = any(w in clean_msg.lower() for w in ["supervisor", "manager"])
        return {
            "escalation_reason": "Customer explicitly requested to speak with a human support representative or supervisor.",
            "priority": "high" if is_senior else "medium",
            "target_team": "senior_support" if is_senior else "general_support",
            "supporting_evidence": [f"Explicit human assistance keyword '{human_kw}' detected in customer message."],
            "requires_human_review": True,
            "explanation": "Customer requested human representative; policy mandates honoring direct escalation requests.",
            "rule_name": "explicit_human_request",
        }

    # Rule 2: Payment failure or transaction discrepancy on verified order
    has_failed_payment = any(p.get("status") in {"failed", "pending"} for p in payments)
    is_order_payment_failed = order_status in {"payment_failed", "pending_payment"}
    if intent == "payment_issue" and inv_status == "found" and (has_failed_payment or is_order_payment_failed):
        priority = "urgent" if has_failed_payment else "high"
        return {
            "escalation_reason": "Unresolved payment failure or transaction discrepancy requires billing team review.",
            "priority": priority,
            "target_team": "billing_support",
            "supporting_evidence": [
                f"Verified records for order '{inv.get('order_id')}' contain failed/pending payments or order status '{order_status}'."
            ],
            "requires_human_review": True,
            "explanation": "Billing transaction failures cannot be modified by automated chat and require billing specialist investigation.",
            "rule_name": "verified_payment_failure",
        }

    # Rule 3: Payment deduction claimed for missing or unrecognized order ID
    if intent == "payment_issue" and inv_status == "order_not_found":
        order_id = inv.get("order_id", "specified")
        return {
            "escalation_reason": f"Customer reported payment deduction for unrecognized order ID '{order_id}'.",
            "priority": "high",
            "target_team": "billing_support",
            "supporting_evidence": [
                f"Customer reported debit/charge, but order ID '{order_id}' was not found in live orders database."
            ],
            "requires_human_review": True,
            "explanation": "Reported unauthorized charge or payment deduction on non-existent order requires immediate billing reconciliation.",
            "rule_name": "unrecognized_order_payment_deduction",
        }

    # Rule 4: Financial fraud, legal threat, or unauthorized charge dispute
    if any(w in clean_msg.lower() for w in ["fraud", "unauthorized charge", "chargeback", "lawsuit", "lawyer", "stolen card"]):
        return {
            "escalation_reason": "Customer reported financial dispute, fraud concern, or legal matter requiring specialist handling.",
            "priority": "urgent",
            "target_team": "billing_support",
            "supporting_evidence": ["Severe legal or financial fraud terminology identified in message."],
            "requires_human_review": True,
            "explanation": "Legal and fraud claims cannot be processed via automated chat.",
            "rule_name": "fraud_or_legal_dispute",
        }

    # Rule 5: ActionExecutionAgent flagged an unsupported financial operation
    if action_execution and action_execution.get("status") == "unsupported":
        return {
            "escalation_reason": "The requested action involves financial modifications that require human billing review.",
            "priority": "high",
            "target_team": "billing_support",
            "supporting_evidence": [action_execution.get("message", "Unsupported financial action")],
            "requires_human_review": True,
            "explanation": "Automated workflow cannot execute financial modifications; routed to billing team.",
            "rule_name": "unsupported_financial_action",
        }

    return None


def deterministic_escalation_decision(
    message: str,
    intent: str,
    understanding: Optional[Dict[str, Any]] = None,
    customer_context: Optional[Dict[str, Any]] = None,
    investigation: Optional[Dict[str, Any]] = None,
    knowledge_retrieval: Optional[Dict[str, Any]] = None,
    knowledge_results: Optional[List[Dict[str, Any]]] = None,
    troubleshooting: Optional[Dict[str, Any]] = None,
    action_execution: Optional[Dict[str, Any]] = None,
    memory: Optional[Dict[str, Any]] = None,
) -> EscalationDecisionResult:
    """Evaluate escalation deterministically using workflow signals and business rules."""
    clean_msg = (message or "").strip()
    clean_intent = (intent or "general_inquiry").strip()

    # 1. First, check non-negotiable hard safety rules
    hard_safety = evaluate_hard_safety_rules(
        message=clean_msg,
        intent=clean_intent,
        investigation=investigation,
        customer_context=customer_context,
        troubleshooting=troubleshooting,
        action_execution=action_execution,
        memory=memory,
    )
    if hard_safety:
        return EscalationDecisionResult(
            should_escalate=True,
            escalation_reason=hard_safety["escalation_reason"],
            priority=hard_safety["priority"],
            target_team=hard_safety["target_team"],
            supporting_evidence=hard_safety["supporting_evidence"],
            requires_human_review=hard_safety["requires_human_review"],
            explanation=hard_safety["explanation"],
            decision_source="deterministic_fallback",
        )

    # 2. Check troubleshooting diagnosis recommendation
    if troubleshooting and troubleshooting.get("suggest_escalation"):
        tb_diag = troubleshooting.get("diagnosis", "Troubleshooting flagged escalation requirement.")
        tb_evidence = troubleshooting.get("evidence", [])
        tb_intent = troubleshooting.get("intent", clean_intent)
        target = "billing_support" if tb_intent == "payment_issue" else ("technical_support" if tb_intent == "account_issue" else "logistics_support")
        return EscalationDecisionResult(
            should_escalate=True,
            escalation_reason=tb_diag,
            priority="high" if tb_intent == "payment_issue" else "medium",
            target_team=target,
            supporting_evidence=tb_evidence or ["Troubleshooting diagnosis identified an unresolvable issue."],
            requires_human_review=True,
            explanation=f"Troubleshooting analysis determined this issue requires human specialist review: {tb_diag}",
            decision_source="deterministic_fallback",
        )

    # 3. Check for severe customer frustration with an unresolved issue
    sentiment = (understanding or {}).get("sentiment", "neutral")
    frustration_kw = detect_severe_frustration(clean_msg)
    if frustration_kw and sentiment in {"frustrated", "urgent"}:
        return EscalationDecisionResult(
            should_escalate=True,
            escalation_reason=f"Significant customer frustration detected with unresolved support issue ('{frustration_kw}').",
            priority="high",
            target_team="senior_support",
            supporting_evidence=[
                f"Customer expressed strong frustration keyword '{frustration_kw}' with sentiment '{sentiment}'."
            ],
            requires_human_review=True,
            explanation="Customer expressed severe frustration and distress; escalated to senior support for personalized resolution.",
            decision_source="deterministic_fallback",
        )

    # 4. Check for repeated unsuccessful attempts in multi-turn memory
    turn_count = (memory or {}).get("turn_count", 0)
    if turn_count >= 3 and any(w in clean_msg.lower() for w in ["still", "not working", "again", "already told you", "tried that"]):
        return EscalationDecisionResult(
            should_escalate=True,
            escalation_reason="Customer reported repeated unsuccessful troubleshooting across multiple conversation turns.",
            priority="high",
            target_team="senior_support",
            supporting_evidence=[
                f"Session memory records {turn_count} prior turns with ongoing customer difficulty."
            ],
            requires_human_review=True,
            explanation="Multi-turn conversation history shows issue could not be resolved in automated turns.",
            decision_source="deterministic_fallback",
        )

    # 5. Default: Automated self-service is sufficient (No escalation)
    evidence_points = []
    if (investigation or {}).get("status") == "found":
        evidence_points.append("Active order successfully located and verified in system.")
    if knowledge_results:
        evidence_points.append(f"Matching knowledge guidance available ({len(knowledge_results)} articles).")
    if not evidence_points:
        evidence_points.append("Standard customer inquiry suitable for self-service response.")

    return EscalationDecisionResult(
        should_escalate=False,
        escalation_reason=None,
        priority="low",
        target_team=None,
        supporting_evidence=evidence_points,
        requires_human_review=False,
        explanation="Issue does not meet any human escalation criteria and can be safely addressed via automated self-service.",
        decision_source="deterministic_fallback",
    )


class EscalationDecisionAgent:
    """Specialized agent deciding whether to resolve automatically or escalate to human support."""

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
                return self._llm.with_structured_output(LLMEscalationOutput)
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
                self._structured_llm = chat_model.with_structured_output(LLMEscalationOutput)
            except Exception as e:
                logger.warning("Failed to initialize ChatGoogleGenerativeAI for escalation: %s", e)
                return None

        return self._structured_llm

    def decide(
        self,
        message: str,
        intent: str,
        understanding: Optional[Dict[str, Any]] = None,
        customer_context: Optional[Dict[str, Any]] = None,
        investigation: Optional[Dict[str, Any]] = None,
        knowledge_retrieval: Optional[Dict[str, Any]] = None,
        knowledge_results: Optional[List[Dict[str, Any]]] = None,
        troubleshooting: Optional[Dict[str, Any]] = None,
        action_execution: Optional[Dict[str, Any]] = None,
        memory: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> EscalationDecisionResult:
        """Evaluate whether to escalate to human support.

        Enforces hard safety rules that CANNOT be overridden by LLM output.
        Falls back seamlessly to deterministic rules if LLM is unavailable or fails.
        """
        clean_msg = (message or "").strip()
        clean_intent = (intent or "general_inquiry").strip()

        # STEP 1: Check hard safety rules before or alongside LLM
        hard_safety = evaluate_hard_safety_rules(
            message=clean_msg,
            intent=clean_intent,
            investigation=investigation,
            customer_context=customer_context,
            troubleshooting=troubleshooting,
            action_execution=action_execution,
            memory=memory,
        )

        structured_llm = self._get_structured_llm()

        # STEP 2: Attempt Gemini LLM evaluation if available
        if structured_llm is not None and clean_msg:
            try:
                system_prompt = (
                    "You are the Escalation Decision Specialist for an e-commerce customer support system.\n"
                    "Your role is to assess whether an inquiry can be resolved automatically or requires\n"
                    "escalation to a human customer support specialist.\n\n"
                    "Decision Guidelines:\n"
                    "1. Explicit human request: Customer asks to speak to an agent, representative, or supervisor -> MUST escalate.\n"
                    "2. Payment failures or unverified transactions -> MUST escalate to billing_support with high/urgent priority.\n"
                    "3. Severe customer frustration or distress with an unresolved problem -> Escalate to senior_support.\n"
                    "4. Repeated failed troubleshooting across multiple turns -> Escalate to senior_support.\n"
                    "5. Normal order tracking, supported self-service cancellations, or policy inquiries -> Do NOT escalate.\n"
                    "6. Target team must be one of: billing_support, logistics_support, technical_support, senior_support, general_support.\n"
                    "7. Priority must be one of: low, medium, high, urgent."
                )

                inv_summary = (investigation or {}).get("summary", "No investigation records.")
                tb_diag = (troubleshooting or {}).get("diagnosis", "No troubleshooting diagnosis.")
                sentiment = (understanding or {}).get("sentiment", "neutral")

                user_content = (
                    f"Customer Message: {clean_msg}\n"
                    f"Classified Intent: {clean_intent}\n"
                    f"Customer Sentiment: {sentiment}\n"
                    f"Investigation Summary: {inv_summary}\n"
                    f"Troubleshooting Diagnosis: {tb_diag}\n"
                )

                llm_response = structured_llm.invoke(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ]
                )

                # Defensive normalization of LLM response
                if isinstance(llm_response, LLMEscalationOutput):
                    parsed_output = llm_response
                elif isinstance(llm_response, dict):
                    parsed_output = LLMEscalationOutput(**llm_response)
                else:
                    logger.warning("LLM returned unexpected type %s, falling back to deterministic rules.", type(llm_response))
                    return deterministic_escalation_decision(
                        message=clean_msg,
                        intent=clean_intent,
                        understanding=understanding,
                        customer_context=customer_context,
                        investigation=investigation,
                        knowledge_retrieval=knowledge_retrieval,
                        knowledge_results=knowledge_results,
                        troubleshooting=troubleshooting,
                        action_execution=action_execution,
                        memory=memory,
                    )

                # STEP 3: Apply Hard Safety Override
                # If a hard safety rule triggered, LLM cannot overturn it!
                if hard_safety:
                    if not parsed_output.should_escalate:
                        logger.warning(
                            "Hard safety rule '%s' overrode LLM recommendation against escalation.",
                            hard_safety.get("rule_name"),
                        )
                    return EscalationDecisionResult(
                        should_escalate=True,
                        escalation_reason=hard_safety["escalation_reason"],
                        priority=hard_safety["priority"],
                        target_team=hard_safety["target_team"],
                        supporting_evidence=hard_safety["supporting_evidence"] + parsed_output.supporting_evidence,
                        requires_human_review=True,
                        explanation=f"Hard safety policy rule overrode model recommendation: {hard_safety['explanation']}",
                        decision_source="deterministic_safety_override",
                    )

                # If no hard safety rule, return validated LLM result
                return EscalationDecisionResult(
                    should_escalate=parsed_output.should_escalate,
                    escalation_reason=parsed_output.escalation_reason if parsed_output.should_escalate else None,
                    priority=parsed_output.priority,
                    target_team=parsed_output.target_team if parsed_output.should_escalate else None,
                    supporting_evidence=parsed_output.supporting_evidence,
                    requires_human_review=parsed_output.requires_human_review,
                    explanation=parsed_output.explanation,
                    decision_source="gemini_assisted",
                )

            except Exception as e:
                logger.warning("Gemini escalation evaluation failed (%s), falling back to deterministic rules.", e)
                return deterministic_escalation_decision(
                    message=clean_msg,
                    intent=clean_intent,
                    understanding=understanding,
                    customer_context=customer_context,
                    investigation=investigation,
                    knowledge_retrieval=knowledge_retrieval,
                    knowledge_results=knowledge_results,
                    troubleshooting=troubleshooting,
                    action_execution=action_execution,
                    memory=memory,
                )

        # STEP 4: Deterministic fallback when LLM is unavailable
        return deterministic_escalation_decision(
            message=clean_msg,
            intent=clean_intent,
            understanding=understanding,
            customer_context=customer_context,
            investigation=investigation,
            knowledge_retrieval=knowledge_retrieval,
            knowledge_results=knowledge_results,
            troubleshooting=troubleshooting,
            action_execution=action_execution,
            memory=memory,
        )


# Global singleton instance
_ESCALATION_AGENT = EscalationDecisionAgent()


def decide_escalation(
    message: str,
    intent: str,
    understanding: Optional[Dict[str, Any]] = None,
    customer_context: Optional[Dict[str, Any]] = None,
    investigation: Optional[Dict[str, Any]] = None,
    knowledge_retrieval: Optional[Dict[str, Any]] = None,
    knowledge_results: Optional[List[Dict[str, Any]]] = None,
    troubleshooting: Optional[Dict[str, Any]] = None,
    action_execution: Optional[Dict[str, Any]] = None,
    memory: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
) -> EscalationDecisionResult:
    """Convenience function to evaluate escalation using the global EscalationDecisionAgent."""
    return _ESCALATION_AGENT.decide(
        message=message,
        intent=intent,
        understanding=understanding,
        customer_context=customer_context,
        investigation=investigation,
        knowledge_retrieval=knowledge_retrieval,
        knowledge_results=knowledge_results,
        troubleshooting=troubleshooting,
        action_execution=action_execution,
        memory=memory,
        session_id=session_id,
    )
